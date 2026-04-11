"""
Recommandations — Collaborative Filtering with real product names
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, request
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD

from db import query_df

recommendations_bp = Blueprint('recommendations', __name__)

# ── helpers ──────────────────────────────────────────────────────────────────

def _load_data():
    sql = """
        SELECT
            COALESCE(s.fk_clientB2B, s.fk_clientB2C) as client_id,
            CASE WHEN s.fk_clientB2B IS NOT NULL THEN 'B2B' ELSE 'B2C' END as client_type,
            COALESCE(b2b.company, b2c.first_name + ' ' + b2c.last_name) as client_name,
            s.fk_product as product_id,
            p.name_product,
            cat.name_category,
            SUM(s.quantity) as total_qty
        FROM fact_sale s
        LEFT JOIN dim_clientB2B b2b ON s.fk_clientB2B = b2b.pk_id_client
        LEFT JOIN dim_clientB2C b2c ON s.fk_clientB2C = b2c.pk_id_client
        INNER JOIN dim_product p ON s.fk_product = p.pk_id_product
        LEFT JOIN dim_category cat ON p.fk_category = cat.pk_id_category
        WHERE (s.fk_clientB2B IS NOT NULL OR s.fk_clientB2C IS NOT NULL)
          AND s.fk_product IS NOT NULL
        GROUP BY
            COALESCE(s.fk_clientB2B, s.fk_clientB2C),
            CASE WHEN s.fk_clientB2B IS NOT NULL THEN 'B2B' ELSE 'B2C' END,
            COALESCE(b2b.company, b2c.first_name + ' ' + b2c.last_name),
            s.fk_product, p.name_product, cat.name_category
    """
    df = query_df(sql)
    df['total_qty'] = pd.to_numeric(df['total_qty'], errors='coerce').fillna(0)
    return df


def _build_matrix(df):
    matrix = df.pivot_table(
        index='client_id', columns='product_id', values='total_qty', fill_value=0
    )
    return matrix


def _recommend(df, matrix, client_id, top_n=5):
    if client_id not in matrix.index:
        return []

    if matrix.shape[1] > 5:
        n_components = min(10, matrix.shape[1] - 1)
        svd = TruncatedSVD(n_components=n_components, random_state=42)
        reduced = svd.fit_transform(matrix)
        sim = cosine_similarity(reduced)
    else:
        sim = cosine_similarity(matrix.values)

    idx = list(matrix.index).index(client_id)
    sim_scores = list(enumerate(sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    client_vec = matrix.loc[client_id].values
    already_bought = set(matrix.columns[client_vec > 0])

    scores = np.zeros(matrix.shape[1])
    for other_idx, score in sim_scores[1:11]:
        scores += score * matrix.iloc[other_idx].values

    for i, prod in enumerate(matrix.columns):
        if prod in already_bought:
            scores[i] = 0

    top_indices = np.argsort(scores)[::-1][:top_n]

    # Build product lookup
    product_info = df[['product_id', 'name_product', 'name_category']].drop_duplicates()
    product_map = {row['product_id']: row for _, row in product_info.iterrows()}

    recommendations = []
    for i in top_indices:
        prod_id = int(matrix.columns[i])
        if scores[i] > 0:
            info = product_map.get(prod_id, {})
            recommendations.append({
                'product_id': prod_id,
                'name': info.get('name_product', f'Product #{prod_id}'),
                'category': info.get('name_category', 'Unknown'),
                'score': round(float(scores[i]), 4)
            })
    return recommendations


def _get_client_history(df, client_id):
    bought = df[df['client_id'] == client_id][
        ['product_id', 'name_product', 'name_category', 'total_qty']
    ].sort_values('total_qty', ascending=False)
    return bought.to_dict(orient='records')

# ── endpoints ─────────────────────────────────────────────────────────────────

@recommendations_bp.route('/clients', methods=['GET'])
def list_clients():
    try:
        df = _load_data()
        clients = (
            df[['client_id', 'client_name', 'client_type']]
            .drop_duplicates()
            .sort_values('client_id')
            .to_dict(orient='records')
        )
        return jsonify({'success': True, 'clients': clients, 'total': len(clients)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@recommendations_bp.route('/products', methods=['POST'])
def recommend_products():
    """Body: { "client_id": 1, "top_n": 5 }"""
    try:
        body = request.get_json(force=True) or {}
        client_id = int(body.get('client_id', 1))
        top_n = int(body.get('top_n', 5))

        df = _load_data()
        matrix = _build_matrix(df)
        recs = _recommend(df, matrix, client_id, top_n)
        history = _get_client_history(df, client_id)

        # Client info
        client_row = df[df['client_id'] == client_id].iloc[0]
        client_name = client_row['client_name']
        client_type = client_row['client_type']

        return jsonify({
            'success': True,
            'client_id': client_id,
            'client_name': client_name,
            'client_type': client_type,
            'recommendations': recs,
            'purchase_history': history,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
