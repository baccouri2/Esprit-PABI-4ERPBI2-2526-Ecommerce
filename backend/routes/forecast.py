"""
Objectif 1 — Demand Forecasting (Time Series)
Models: ARIMA, SARIMA, Exponential Smoothing, XGBoost
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, request

from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from db import query_df

forecast_bp = Blueprint('forecast', __name__)

# ── helpers ──────────────────────────────────────────────────────────────────

def _load_weekly_data():
    sql = """
        SELECT d.full_date, CAST(SUM(s.quantity) AS INT) as quantity
        FROM fact_sale s
        INNER JOIN dim_date d ON s.fk_date = d.pk_id_date
        WHERE s.quantity IS NOT NULL
        GROUP BY d.full_date
        ORDER BY d.full_date
    """
    df = query_df(sql)
    df['full_date'] = pd.to_datetime(df['full_date'])
    df['quantity'] = df['quantity'].astype(int)
    df = df.sort_values('full_date').reset_index(drop=True)

    df['week'] = df['full_date'].dt.isocalendar().week
    df['year'] = df['full_date'].dt.year
    weekly = df.groupby(['year', 'week'])['quantity'].sum().reset_index()
    weekly['date'] = pd.to_datetime(
        weekly['year'].astype(str) + '-W' + weekly['week'].astype(str) + '-1',
        format='%G-W%V-%u'
    )
    weekly = weekly.sort_values('date').reset_index(drop=True)
    return weekly[['date', 'quantity']]


def _metrics(actual, predicted):
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    r2 = r2_score(actual, predicted)
    return {'mae': round(mae, 2), 'rmse': round(rmse, 2), 'r2': round(r2, 4)}


def _run_arima(series, steps):
    model = ARIMA(series, order=(1, 1, 1))
    fit = model.fit()
    forecast = fit.forecast(steps=steps)
    return forecast.tolist()


def _run_sarima(series, steps):
    model = SARIMAX(series, order=(1, 1, 1), seasonal_order=(1, 1, 0, 4))
    fit = model.fit(disp=False)
    forecast = fit.forecast(steps=steps)
    return forecast.tolist()


def _run_exp_smoothing(series, steps):
    model = ExponentialSmoothing(series, trend='add', seasonal=None)
    fit = model.fit()
    forecast = fit.forecast(steps=steps)
    return forecast.tolist()


def _run_xgboost(series, steps):
    n_lags = min(4, len(series) - 1)
    X, y = [], []
    for i in range(n_lags, len(series)):
        X.append(series[i - n_lags:i])
        y.append(series[i])
    X, y = np.array(X), np.array(y)
    model = xgb.XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.1)
    model.fit(X, y)

    preds = []
    last = list(series[-n_lags:])
    for _ in range(steps):
        x = np.array(last[-n_lags:]).reshape(1, -1)
        p = float(model.predict(x)[0])
        preds.append(p)
        last.append(p)
    return preds

# ── endpoints ─────────────────────────────────────────────────────────────────

@forecast_bp.route('/data', methods=['GET'])
def get_historical():
    """Return historical weekly demand data."""
    try:
        df = _load_weekly_data()
        records = [
            {'date': row['date'].strftime('%Y-%m-%d'), 'quantity': int(row['quantity'])}
            for _, row in df.iterrows()
        ]
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@forecast_bp.route('/predict', methods=['POST'])
def predict():
    """
    Body: { "model": "arima"|"sarima"|"exp_smoothing"|"xgboost", "steps": 4 }
    """
    try:
        body = request.get_json(force=True) or {}
        model_name = body.get('model', 'xgboost').lower()
        steps = int(body.get('steps', 4))

        df = _load_weekly_data()
        series = df['quantity'].values.astype(float)

        dispatch = {
            'arima': _run_arima,
            'sarima': _run_sarima,
            'exp_smoothing': _run_exp_smoothing,
            'xgboost': _run_xgboost,
        }
        if model_name not in dispatch:
            return jsonify({'success': False, 'error': f'Unknown model: {model_name}'}), 400

        forecast = dispatch[model_name](series, steps)
        forecast = [max(0, round(v, 2)) for v in forecast]

        # Build future dates
        last_date = df['date'].iloc[-1]
        future_dates = pd.date_range(start=last_date, periods=steps + 1, freq='W')[1:]
        future = [
            {'date': d.strftime('%Y-%m-%d'), 'quantity': v}
            for d, v in zip(future_dates, forecast)
        ]

        return jsonify({'success': True, 'model': model_name, 'forecast': future})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
