"""
GET /api/data — Dashboard overview
Returns a single JSON snapshot of all key metrics from dw_pi.

Verified schema (from INFORMATION_SCHEMA):
  fact_sale       : pk_id_sale, fk_date, fk_product, fk_clientB2B, fk_clientB2C,
                    quantity, unit_price, discount, total_price
  dim_product     : pk_id_product, fk_category, ref_product, name_product
  dim_category    : pk_id_category, name_category, number_product
  dim_clientb2b   : pk_id_client, MF, company
  dim_clientb2c   : pk_id_client, first_name, last_name
  dim_date        : pk_id_date, full_date, day, month, trimester, semester, year
  dim_claim       : pk_id_claim, description, status
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
from flask import Blueprint, jsonify
from db import query_df

data_bp = Blueprint('data', __name__)


@data_bp.route('', methods=['GET'])
def get_data():
    try:
        result = {}

        # ── 1. Sales KPIs ────────────────────────────────────────────────────
        kpi = query_df("""
            SELECT
                COUNT(*)           AS total_transactions,
                SUM(total_price)   AS total_revenue,
                AVG(total_price)   AS avg_sale_value,
                AVG(discount)      AS avg_discount,
                SUM(quantity)      AS total_units_sold,
                MIN(total_price)   AS min_sale,
                MAX(total_price)   AS max_sale
            FROM fact_sale
        """).iloc[0]

        result['kpis'] = {
            'total_transactions': int(kpi['total_transactions']),
            'total_revenue':      round(float(kpi['total_revenue'] or 0), 2),
            'avg_sale_value':     round(float(kpi['avg_sale_value'] or 0), 2),
            'avg_discount':       round(float(kpi['avg_discount'] or 0), 4),
            'total_units_sold':   int(kpi['total_units_sold'] or 0),
            'min_sale':           round(float(kpi['min_sale'] or 0), 2),
            'max_sale':           round(float(kpi['max_sale'] or 0), 2),
        }

        # ── 2. Products ──────────────────────────────────────────────────────
        prod_count = int(query_df(
            "SELECT COUNT(*) AS cnt FROM dim_product"
        ).iloc[0]['cnt'])

        top_products = query_df("""
            SELECT TOP 5
                p.name_product,
                c.name_category,
                SUM(s.quantity)    AS total_qty,
                SUM(s.total_price) AS total_revenue,
                AVG(s.unit_price)  AS avg_price
            FROM fact_sale s
            INNER JOIN dim_product  p ON s.fk_product  = p.pk_id_product
            LEFT  JOIN dim_category c ON p.fk_category = c.pk_id_category
            GROUP BY p.name_product, c.name_category
            ORDER BY total_revenue DESC
        """)

        result['products'] = {
            'total_count': prod_count,
            'top_5': [
                {
                    'name':          str(r['name_product']),
                    'category':      str(r['name_category']) if r['name_category'] else 'Uncategorized',
                    'total_qty':     int(r['total_qty']),
                    'total_revenue': round(float(r['total_revenue']), 2),
                    'avg_price':     round(float(r['avg_price']), 2),
                }
                for _, r in top_products.iterrows()
            ]
        }

        # ── 3. Customers ─────────────────────────────────────────────────────
        b2b_count = int(query_df(
            "SELECT COUNT(*) AS cnt FROM dim_clientb2b"
        ).iloc[0]['cnt'])

        b2c_count = int(query_df(
            "SELECT COUNT(*) AS cnt FROM dim_clientb2c"
        ).iloc[0]['cnt'])

        try:
            top_b2b = query_df("""
                SELECT TOP 5
                    b.company          AS name,
                    'B2B'              AS type,
                    COUNT(*)           AS orders,
                    SUM(s.total_price) AS revenue
                FROM fact_sale s
                INNER JOIN dim_clientb2b b ON s.fk_clientB2B = b.pk_id_client
                GROUP BY b.company
                ORDER BY revenue DESC
            """)
        except Exception:
            top_b2b = pd.DataFrame()

        try:
            top_b2c = query_df("""
                SELECT TOP 5
                    CONCAT(b.first_name, ' ', b.last_name) AS name,
                    'B2C'                                   AS type,
                    COUNT(*)                                AS orders,
                    SUM(s.total_price)                      AS revenue
                FROM fact_sale s
                INNER JOIN dim_clientb2c b ON s.fk_clientB2C = b.pk_id_client
                GROUP BY b.first_name, b.last_name
                ORDER BY revenue DESC
            """)
        except Exception:
            top_b2c = pd.DataFrame()

        if not top_b2b.empty or not top_b2c.empty:
            top_customers = (
                pd.concat([df for df in [top_b2b, top_b2c] if not df.empty])
                .sort_values('revenue', ascending=False)
                .head(5)
            )
        else:
            top_customers = pd.DataFrame()

        result['customers'] = {
            'b2b_count':   b2b_count,
            'b2c_count':   b2c_count,
            'total_count': b2b_count + b2c_count,
            'top_5': [
                {
                    'name':    str(r['name']),
                    'type':    str(r['type']),
                    'orders':  int(r['orders']),
                    'revenue': round(float(r['revenue']), 2),
                }
                for _, r in top_customers.iterrows()
            ] if not top_customers.empty else []
        }

        # ── 4. Categories ────────────────────────────────────────────────────
        categories = query_df("""
            SELECT
                c.name_category,
                COUNT(DISTINCT p.pk_id_product) AS product_count,
                SUM(s.quantity)                 AS total_qty,
                SUM(s.total_price)              AS total_revenue,
                AVG(s.unit_price)               AS avg_price
            FROM fact_sale s
            INNER JOIN dim_product  p ON s.fk_product  = p.pk_id_product
            LEFT  JOIN dim_category c ON p.fk_category = c.pk_id_category
            GROUP BY c.name_category
            ORDER BY total_revenue DESC
        """)

        result['categories'] = [
            {
                'category':      str(r['name_category']) if r['name_category'] else 'Uncategorized',
                'product_count': int(r['product_count']),
                'total_qty':     int(r['total_qty']),
                'total_revenue': round(float(r['total_revenue']), 2),
                'avg_price':     round(float(r['avg_price']), 2),
            }
            for _, r in categories.iterrows()
        ]

        # ── 5. Monthly trend (last 12 months) ────────────────────────────────
        monthly = query_df("""
            SELECT TOP 12
                d.year,
                d.month,
                SUM(s.total_price) AS revenue,
                SUM(s.quantity)    AS units,
                COUNT(*)           AS transactions
            FROM fact_sale s
            INNER JOIN dim_date d ON s.fk_date = d.pk_id_date
            GROUP BY d.year, d.month
            ORDER BY d.year DESC, d.month DESC
        """)

        result['monthly_trend'] = [
            {
                'year':         int(r['year']),
                'month':        int(r['month']),
                'revenue':      round(float(r['revenue']), 2),
                'units':        int(r['units']),
                'transactions': int(r['transactions']),
            }
            for _, r in monthly.sort_values(['year', 'month']).iterrows()
        ]

        # ── 6. Claims ────────────────────────────────────────────────────────
        try:
            claims_count = int(query_df(
                "SELECT COUNT(*) AS cnt FROM dim_claim"
            ).iloc[0]['cnt'])
        except Exception:
            claims_count = 0

        result['claims'] = {'total_count': claims_count}

        # ── 7. Best year ─────────────────────────────────────────────────────
        best_year = query_df("""
            SELECT TOP 1
                d.year,
                SUM(s.total_price) AS revenue,
                COUNT(*)           AS transactions
            FROM fact_sale s
            INNER JOIN dim_date d ON s.fk_date = d.pk_id_date
            GROUP BY d.year
            ORDER BY revenue DESC
        """).iloc[0]

        result['best_year'] = {
            'year':         int(best_year['year']),
            'revenue':      round(float(best_year['revenue']), 2),
            'transactions': int(best_year['transactions']),
        }

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
