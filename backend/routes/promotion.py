"""
Objectif 4 — Promotion Impact Prediction
Models: RandomForest, GradientBoosting, LinearRegression
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, request
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from db import query_df

promotion_bp = Blueprint('promotion', __name__)

# ── helpers ──────────────────────────────────────────────────────────────────

def _load_data():
    sql = """
        SELECT s.quantity, s.unit_price, s.discount,
               d.day, d.month, d.full_date
        FROM fact_sale s
        INNER JOIN dim_date d ON s.fk_date = d.pk_id_date
        WHERE s.quantity IS NOT NULL AND s.unit_price IS NOT NULL
    """
    df = query_df(sql)
    for col in ['quantity', 'unit_price', 'discount']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['discount_rate'] = np.where(df['unit_price'] > 0, df['discount'] / df['unit_price'], 0)
    
    # Calculate is_weekend from full_date
    df['full_date'] = pd.to_datetime(df['full_date'])
    df['is_weekend'] = df['full_date'].dt.dayofweek.isin([5, 6]).astype(int)
    
    # Clip outliers
    q99 = df['quantity'].quantile(0.99)
    df['quantity'] = df['quantity'].clip(upper=q99)
    return df


def _train_and_predict(df, model_name, input_row):
    feature_cols = ['unit_price', 'discount_rate', 'day', 'month', 'is_weekend']
    X = df[feature_cols]
    y = df['quantity']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )

    models = {
        'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
        'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
        'linear_regression': LinearRegression(),
    }
    if model_name not in models:
        raise ValueError(f'Unknown model: {model_name}')

    m = models[model_name]
    m.fit(X_train, y_train)
    y_pred = m.predict(X_test)

    metrics = {
        'mae': round(mean_absolute_error(y_test, y_pred), 2),
        'rmse': round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
        'r2': round(r2_score(y_test, y_pred), 4),
    }

    # Predict for the user-supplied input
    row_df = pd.DataFrame([input_row])[feature_cols]
    row_scaled = scaler.transform(row_df)
    prediction = max(0, float(m.predict(row_scaled)[0]))

    return prediction, metrics

# ── endpoints ─────────────────────────────────────────────────────────────────

@promotion_bp.route('/predict', methods=['POST'])
def predict():
    """
    Body:
    {
      "model": "random_forest" | "gradient_boosting" | "linear_regression",
      "unit_price": 50.0,
      "discount_rate": 0.1,
      "day": 3,
      "month": 6,
      "is_weekend": 0
    }
    """
    try:
        body = request.get_json(force=True) or {}
        model_name = body.get('model', 'random_forest')

        input_row = {
            'unit_price': float(body.get('unit_price', 50)),
            'discount_rate': float(body.get('discount_rate', 0.1)),
            'day': int(body.get('day', 3)),
            'month': int(body.get('month', 6)),
            'is_weekend': int(body.get('is_weekend', 0)),
        }

        df = _load_data()
        prediction, metrics = _train_and_predict(df, model_name, input_row)

        return jsonify({
            'success': True,
            'model': model_name,
            'predicted_quantity': round(prediction, 2),
            'metrics': metrics,
            'input': input_row,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
