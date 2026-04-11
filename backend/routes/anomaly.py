"""
Objectif 3 — Anomaly Detection
Models: IsolationForest, OneClassSVM, LocalOutlierFactor
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, request
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

from db import query_df

anomaly_bp = Blueprint('anomaly', __name__)

# ── helpers ──────────────────────────────────────────────────────────────────

def _load_transactions():
    sql = """
        SELECT s.pk_id_sale, s.quantity, s.unit_price, s.discount, s.total_price,
               d.full_date, d.day, d.month
        FROM fact_sale s
        INNER JOIN dim_date d ON s.fk_date = d.pk_id_date
        WHERE s.quantity IS NOT NULL AND s.unit_price IS NOT NULL
    """
    df = query_df(sql)
    df['full_date'] = pd.to_datetime(df['full_date'])
    for col in ['quantity', 'unit_price', 'discount', 'total_price']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['discount_rate'] = np.where(
        df['unit_price'] > 0, df['discount'] / df['unit_price'], 0
    )
    return df


def _detect(df, model_name='isolation_forest', contamination=0.05):
    features = df[['quantity', 'unit_price', 'discount_rate']].copy()
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    if model_name == 'isolation_forest':
        detector = IsolationForest(contamination=contamination, random_state=42)
        preds = detector.fit_predict(scaled)
        scores = detector.score_samples(scaled)
    elif model_name == 'one_class_svm':
        detector = OneClassSVM(nu=contamination)
        preds = detector.fit_predict(scaled)
        scores = detector.score_samples(scaled)
    elif model_name == 'lof':
        detector = LocalOutlierFactor(contamination=contamination)
        preds = detector.fit_predict(scaled)
        scores = detector.negative_outlier_factor_
    else:
        raise ValueError(f'Unknown model: {model_name}')

    df = df.copy()
    df['is_anomaly'] = (preds == -1).astype(int)
    df['anomaly_score'] = np.round(scores, 4)
    return df

# ── endpoints ─────────────────────────────────────────────────────────────────

@anomaly_bp.route('/detect', methods=['GET'])
def detect():
    """
    Query params:
      model  = isolation_forest | one_class_svm | lof  (default: isolation_forest)
      contamination = float 0-0.5  (default: 0.05)
    """
    try:
        model_name = request.args.get('model', 'isolation_forest')
        contamination = float(request.args.get('contamination', 0.05))

        df = _load_transactions()
        df = _detect(df, model_name, contamination)

        records = []
        for _, row in df.iterrows():
            records.append({
                'id': int(row['pk_id_sale']),
                'date': row['full_date'].strftime('%Y-%m-%d'),
                'quantity': float(row['quantity']),
                'unit_price': float(row['unit_price']),
                'discount_rate': round(float(row['discount_rate']), 4),
                'total_price': float(row['total_price']),
                'is_anomaly': int(row['is_anomaly']),
                'anomaly_score': float(row['anomaly_score']),
            })

        anomaly_count = sum(1 for r in records if r['is_anomaly'])
        return jsonify({
            'success': True,
            'model': model_name,
            'total': len(records),
            'anomalies': anomaly_count,
            'data': records,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
