"""
POST /api/model/predict — Unified ML prediction endpoint for n8n
Single entry point that routes to any ML model based on the "model" field.

Body examples:
  { "model": "forecast",      "steps": 4 }
  { "model": "segmentation",  "clusters": 3 }
  { "model": "anomaly",       "contamination": 0.05 }
  { "model": "promotion",     "unit_price": 50, "discount_rate": 0.1, "day": 15, "month": 6, "is_weekend": 0 }
  { "model": "sentiment",     "text": "Great product!" }
  { "model": "recommendations","client_id": 1, "top_n": 5 }
  { "model": "competition",   "top_n": 10 }
  { "model": "data" }
"""

import warnings
warnings.filterwarnings('ignore')

from flask import Blueprint, jsonify, request

model_bp = Blueprint('model', __name__)


@model_bp.route('/predict', methods=['POST'])
def predict():
    """
    Unified prediction endpoint.
    Routes to the correct ML model based on the 'model' field in the request body.
    """
    try:
        body = request.get_json(force=True) or {}
        model_name = body.get('model', '').lower().strip()

        if not model_name:
            return jsonify({
                'success': False,
                'error': 'Missing "model" field',
                'available_models': [
                    'forecast', 'segmentation', 'anomaly',
                    'promotion', 'sentiment', 'recommendations',
                    'competition', 'data'
                ]
            }), 400

        # ── Route to the correct model ────────────────────────────────────────

        if model_name == 'forecast':
            from routes.forecast import _load_weekly_data, _run_xgboost, _run_arima, _run_sarima, _run_exp_smoothing
            import pandas as pd

            algo  = body.get('algorithm', 'xgboost').lower()
            steps = int(body.get('steps', 4))

            df     = _load_weekly_data()
            series = df['quantity'].values.astype(float)

            dispatch = {
                'xgboost':      _run_xgboost,
                'arima':        _run_arima,
                'sarima':       _run_sarima,
                'exp_smoothing':_run_exp_smoothing,
            }
            runner = dispatch.get(algo, _run_xgboost)
            forecast_vals = [max(0, round(v, 2)) for v in runner(series, steps)]

            last_date    = df['date'].iloc[-1]
            future_dates = pd.date_range(start=last_date, periods=steps + 1, freq='W')[1:]
            forecast     = [
                {'date': d.strftime('%Y-%m-%d'), 'quantity': v}
                for d, v in zip(future_dates, forecast_vals)
            ]
            avg = round(sum(f['quantity'] for f in forecast) / len(forecast), 2)

            return jsonify({
                'success': True, 'model': 'forecast', 'algorithm': algo,
                'steps': steps, 'forecast': forecast, 'avg_forecast': avg
            })

        elif model_name == 'segmentation':
            from routes.segmentation import _load_rfm, _cluster

            clusters = int(body.get('clusters', 3))
            rfm      = _load_rfm()
            rfm      = _cluster(rfm, clusters)
            total    = len(rfm)
            counts   = rfm['segment'].value_counts().to_dict()

            return jsonify({
                'success': True, 'model': 'segmentation',
                'total_customers': total,
                'clusters': clusters,
                'segments': {
                    k: {'count': v, 'pct': round(v / total * 100, 1)}
                    for k, v in counts.items()
                },
                'sample': rfm.head(10).to_dict(orient='records')
            })

        elif model_name == 'anomaly':
            from routes.anomaly import _load_transactions, _detect

            algo          = body.get('algorithm', 'isolation_forest')
            contamination = float(body.get('contamination', 0.05))

            df    = _load_transactions()
            df    = _detect(df, algo, contamination)
            total = len(df)
            anom  = int(df['is_anomaly'].sum())

            return jsonify({
                'success': True, 'model': 'anomaly', 'algorithm': algo,
                'total_transactions': total,
                'anomaly_count': anom,
                'anomaly_rate_pct': round(anom / total * 100, 2) if total else 0,
                'status': 'critical' if anom / total > 0.05 else ('warning' if anom > 0 else 'clean')
            })

        elif model_name == 'promotion':
            from routes.promotion import _load_sales_data, _train_model

            algo          = body.get('algorithm', 'random_forest')
            unit_price    = float(body.get('unit_price', 50))
            discount_rate = float(body.get('discount_rate', 0.1))
            day           = int(body.get('day', 15))
            month         = int(body.get('month', 6))
            is_weekend    = int(body.get('is_weekend', 0))

            df             = _load_sales_data()
            model_obj, metrics = _train_model(df, algo)
            import numpy as np
            prediction = float(model_obj.predict(
                np.array([[unit_price, discount_rate, day, month, is_weekend]])
            )[0])
            prediction = max(0, round(prediction, 2))
            revenue    = round(prediction * unit_price * (1 - discount_rate), 2)

            return jsonify({
                'success': True, 'model': 'promotion', 'algorithm': algo,
                'predicted_quantity': prediction,
                'estimated_revenue': revenue,
                'metrics': metrics,
                'inputs': {
                    'unit_price': unit_price, 'discount_rate': discount_rate,
                    'day': day, 'month': month, 'is_weekend': is_weekend
                }
            })

        elif model_name == 'sentiment':
            from routes.sentiment import _analyze_text, _train_sentiment_model
            from routes.sentiment import sentiment_bp

            text = body.get('text', '').strip()
            if not text:
                return jsonify({'success': False, 'error': 'Missing "text" field'}), 400

            if not hasattr(sentiment_bp, 'model'):
                m, v, _, _, _ = _train_sentiment_model()
                sentiment_bp.model      = m
                sentiment_bp.vectorizer = v

            result = _analyze_text(text, sentiment_bp.model, sentiment_bp.vectorizer)
            return jsonify({'success': True, 'model': 'sentiment', **result})

        elif model_name == 'recommendations':
            from routes.recommendations import _load_data, _build_matrix, _recommend, _get_client_history

            client_id = int(body.get('client_id', 1))
            top_n     = int(body.get('top_n', 5))

            df     = _load_data()
            matrix = _build_matrix(df)
            recs   = _recommend(df, matrix, client_id, top_n)
            hist   = _get_client_history(df, client_id)

            client_row  = df[df['client_id'] == client_id]
            client_name = client_row.iloc[0]['client_name'] if not client_row.empty else 'Unknown'
            client_type = client_row.iloc[0]['client_type'] if not client_row.empty else 'Unknown'

            return jsonify({
                'success': True, 'model': 'recommendations',
                'client_id': client_id, 'client_name': client_name, 'client_type': client_type,
                'recommendations': recs, 'purchase_history': hist
            })

        elif model_name == 'competition':
            from routes.competition import _load_competitor_data, _train_best_seller_model

            top_n        = int(body.get('top_n', 10))
            df           = _load_competitor_data()
            df_pred, _, _ = _train_best_seller_model(df)

            if df_pred is None:
                return jsonify({'success': False, 'error': 'Insufficient competitor data'}), 400

            top = df_pred.nlargest(top_n, 'probabilite_best_seller')
            recommendations = [
                {
                    'name':        row['nom'],
                    'price':       round(float(row['prix']), 2),
                    'category':    row['categorie'],
                    'probability': round(float(row['probabilite_best_seller']) * 100, 1)
                }
                for _, row in top.iterrows()
            ]
            return jsonify({
                'success': True, 'model': 'competition',
                'total_products': len(df_pred),
                'recommendations': recommendations
            })

        elif model_name == 'data':
            # Delegate to the data blueprint logic inline
            from db import query_df
            import pandas as pd

            kpi = query_df("""
                SELECT COUNT(*) AS txn, SUM(total_price) AS rev,
                       AVG(total_price) AS avg_sale, SUM(quantity) AS units
                FROM fact_sale
            """).iloc[0]

            prod_count = int(query_df("SELECT COUNT(*) AS cnt FROM dim_product").iloc[0]['cnt'])
            b2b_count  = int(query_df("SELECT COUNT(*) AS cnt FROM dim_clientb2b").iloc[0]['cnt'])
            b2c_count  = int(query_df("SELECT COUNT(*) AS cnt FROM dim_clientb2c").iloc[0]['cnt'])

            top_product = query_df("""
                SELECT TOP 1 p.name_product, SUM(s.total_price) AS rev
                FROM fact_sale s
                INNER JOIN dim_product p ON s.fk_product = p.pk_id_product
                GROUP BY p.name_product ORDER BY rev DESC
            """).iloc[0]

            return jsonify({
                'success': True, 'model': 'data',
                'kpis': {
                    'total_transactions': int(kpi['txn']),
                    'total_revenue':      round(float(kpi['rev'] or 0), 2),
                    'avg_sale_value':     round(float(kpi['avg_sale'] or 0), 2),
                    'total_units_sold':   int(kpi['units'] or 0),
                },
                'catalogue': {
                    'products':      prod_count,
                    'b2b_customers': b2b_count,
                    'b2c_customers': b2c_count,
                },
                'top_product': {
                    'name':    str(top_product['name_product']),
                    'revenue': round(float(top_product['rev']), 2)
                }
            })

        else:
            return jsonify({
                'success': False,
                'error': f'Unknown model: "{model_name}"',
                'available_models': [
                    'forecast', 'segmentation', 'anomaly',
                    'promotion', 'sentiment', 'recommendations',
                    'competition', 'data'
                ]
            }), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
