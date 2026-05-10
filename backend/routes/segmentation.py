"""
Objectif 2 — Advanced Customer Segmentation
RFM analysis + KMeans clustering
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, request
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from db import query_df

segmentation_bp = Blueprint('segmentation', __name__)

# ── helpers ──────────────────────────────────────────────────────────────────

def _load_rfm():
    sql_clients = """
        SELECT s.fk_clientB2B as client_id, 'B2B' as client_type,
               s.fk_date, s.quantity, s.total_price, s.discount
        FROM fact_sale s WHERE s.fk_clientB2B IS NOT NULL
        UNION ALL
        SELECT s.fk_clientB2C as client_id, 'B2C' as client_type,
               s.fk_date, s.quantity, s.total_price, s.discount
        FROM fact_sale s WHERE s.fk_clientB2C IS NOT NULL
    """
    sql_dates = "SELECT pk_id_date, full_date FROM dim_date"

    df = query_df(sql_clients)
    dates = query_df(sql_dates)

    df = df.merge(dates, left_on='fk_date', right_on='pk_id_date', how='left')
    df['fk_date'] = pd.to_datetime(df['full_date'])
    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0).astype(int)
    df['total_price'] = pd.to_numeric(df['total_price'], errors='coerce').fillna(0)
    df['discount'] = pd.to_numeric(df['discount'], errors='coerce').fillna(0)
    df = df[df['fk_date'] > '2000-01-01']

    ref = df['fk_date'].max()
    rfm = df.groupby(['client_id', 'client_type']).agg(
        recency=('fk_date', lambda x: (ref - x.max()).days),
        frequency=('quantity', 'count'),
        monetary=('total_price', 'sum'),
        avg_discount=('discount', 'mean'),
    ).reset_index()
    rfm = rfm[rfm['frequency'] > 0]
    rfm['recency'] = rfm['recency'].astype(int)
    rfm['monetary'] = rfm['monetary'].round(2)
    return rfm


def _cluster(rfm, n_clusters=3):
    features = rfm[['recency', 'frequency', 'monetary']].copy()
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    rfm = rfm.copy()
    rfm['cluster'] = km.fit_predict(scaled)

    # Label clusters by average monetary value
    cluster_means = rfm.groupby('cluster')['monetary'].mean().sort_values(ascending=False)
    label_map = {c: lbl for lbl, c in enumerate(cluster_means.index)}
    labels = ['High Value', 'Mid Value', 'Low Value']
    rfm['segment'] = rfm['cluster'].map(lambda c: labels[label_map[c]])
    return rfm

# ── endpoints ─────────────────────────────────────────────────────────────────

@segmentation_bp.route('/rfm', methods=['GET'])
def get_rfm():
    """Return RFM data with cluster labels."""
    try:
        n_clusters = int(request.args.get('clusters', 3))
        rfm = _load_rfm()
        rfm = _cluster(rfm, n_clusters)
        records = rfm.to_dict(orient='records')
        return jsonify({'success': True, 'data': records, 'total': len(records)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@segmentation_bp.route('/stats', methods=['GET'])
def get_stats():
    """Return per-segment summary statistics."""
    try:
        rfm = _load_rfm()
        rfm = _cluster(rfm)
        stats = (
            rfm.groupby('segment')
            .agg(
                count=('client_id', 'count'),
                avg_recency=('recency', 'mean'),
                avg_frequency=('frequency', 'mean'),
                avg_monetary=('monetary', 'mean'),
            )
            .round(2)
            .reset_index()
            .to_dict(orient='records')
        )
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
