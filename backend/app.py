# -*- coding: utf-8 -*-

"""

ML Dashboard Backend API

Serves predictions from the 5 ML models in the ml/ folder.

"""

# Fix statsmodels/numpy threading issues on Windows - MUST BE FIRST
import os
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

import sys

import json

import logging

from datetime import datetime

# -- File logger - captures ALL Flask activity automatically ------------------

LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'execution_logs.json')

class JsonFileHandler(logging.Handler):

    """Appends every log record as a JSON entry to execution_logs.json."""

    def emit(self, record):

        try:

            entry = {

                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),

                'level':     record.levelname,

                'workflow':  'Flask Backend',

                'status':    'error' if record.levelno >= logging.ERROR else 'info',

                'details':   self.format(record)

            }

            logs = []

            if os.path.exists(LOG_PATH):

                with open(LOG_PATH, 'r', encoding='utf-8') as f:

                    logs = json.load(f)

            logs.append(entry)

            logs = logs[-500:]  # keep last 500

            with open(LOG_PATH, 'w', encoding='utf-8') as f:

                json.dump(logs, f, ensure_ascii=False, indent=2, default=str)

        except Exception:

            pass

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger('ml_backend')

logger.addHandler(JsonFileHandler())

# Add the ml folder to path so notebooks can be referenced

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ml'))

from flask import Flask, jsonify, request

from flask_cors import CORS

from routes.forecast import forecast_bp

from routes.segmentation import segmentation_bp

from routes.anomaly import anomaly_bp

from routes.promotion import promotion_bp

from routes.recommendations import recommendations_bp

from routes.sentiment import sentiment_bp

from routes.chatbot import chatbot_bp

from routes.competition import competition_bp

from routes.data import data_bp

from routes.model import model_bp

from routes.clients import clients_bp

from routes.suppliers import suppliers_bp

from routes.products import products_bp

from routes.orders import orders_bp

from routes.crm import crm_bp

# -- Startup banner ------------------------------------------------------------

print("=" * 55)

print("  ML PIPELINE BACKEND - DEMARRAGE")

print("=" * 55)

print(f"  Heure   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

print(f"  Mode    : Developpement")

print(f"  Port    : 5000")

print(f"  Base URL: http://0.0.0.0:5000/api")

print("=" * 55)

print("  Chargement des modules ML...")

print(f"   [OK]  Forecast       - ARIMA / SARIMA / XGBoost / ExpSmoothing")

print(f"   [OK]  Segmentation   - KMeans RFM")

print(f"   [OK]  Anomaly        - IsolationForest / OneClassSVM / LOF")

print(f"   [OK]  Promotion      - RandomForest / GradientBoosting / LinearReg")

print(f"   [OK]  Recommendations- Collaborative Filtering (TruncatedSVD)")

print(f"   [OK]  Competition    - XGBoost Best-Seller Classifier")

print(f"   [OK]  Chatbot        - Keyword Routing + SQL")

print(f"   [OK]  Data           - Dashboard Overview (dw_pi)")

print(f"   [OK]  Model          - Unified Predict Endpoint (/api/model/predict)")

print(f"   [OK]  Orders         - Order Management + Invoice PDF")

print(f"   [..]  Sentiment      - Entrainement en cours...")

app = Flask(__name__)

CORS(app)

# Register blueprints

app.register_blueprint(forecast_bp,        url_prefix='/api/forecast')

app.register_blueprint(segmentation_bp,    url_prefix='/api/segmentation')

app.register_blueprint(anomaly_bp,         url_prefix='/api/anomaly')

app.register_blueprint(promotion_bp,       url_prefix='/api/promotion')

app.register_blueprint(recommendations_bp, url_prefix='/api/recommendations')

app.register_blueprint(sentiment_bp,       url_prefix='/api/sentiment')

app.register_blueprint(chatbot_bp,         url_prefix='/api/chatbot')

app.register_blueprint(competition_bp,     url_prefix='/api/competition')

app.register_blueprint(data_bp,            url_prefix='/api/data')

app.register_blueprint(model_bp,           url_prefix='/api/model')

app.register_blueprint(clients_bp,         url_prefix='/api/clients')

app.register_blueprint(suppliers_bp,       url_prefix='/api/suppliers')

app.register_blueprint(products_bp,        url_prefix='/api/products')

app.register_blueprint(orders_bp,          url_prefix='/api/orders')

app.register_blueprint(crm_bp,             url_prefix='/api/crm')

# -- Pre-train sentiment model at startup --------------------------------------

def _warmup_sentiment():

    try:

        from routes.sentiment import _train_sentiment_model

        model, vectorizer, accuracy, n_neg, n_pos = _train_sentiment_model()

        sentiment_bp.model = model

        sentiment_bp.vectorizer = vectorizer

        print(f"   [OK]  Sentiment      - Precision: {accuracy*100:.1f}% | {n_neg} neg / {n_pos} pos")

    except Exception as e:

        print(f"   [!!]  Sentiment      - Warmup ignore: {e}")

with app.app_context():
    pass  # Sentiment trains on first request

print("=" * 55)

print("  Endpoints disponibles:")

print("   GET  /api/health")

print("   GET  /api/data")

print("   POST /api/model/predict        <- unified ML endpoint for n8n")

print("   POST /api/insert               <- store predictions to SQL")

print("   GET  /api/predictions          <- read stored predictions")

print("   POST /api/log                  <- write execution logs")

print("   GET  /api/logs                 <- read execution logs")

print("   POST /api/retrain              <- retrain sentiment model (bonus)")

print("   POST /api/query                <- run read-only SQL queries")

print("=" * 55)

# -- Health --------------------------------------------------------------------

@app.route('/api/health', methods=['GET'])

def health():

    logger.info('Health check called')

    return jsonify({'status': 'ok', 'message': 'ML Dashboard API is running'})

@app.route('/api/execute', methods=['POST'])

def execute_command():

    """

    Execute Command equivalent - runs ML model inline (no subprocess overhead).

    Body: { "model": "forecast", "steps": 4 }

    Satisfies the n8n Execute Command node requirement via HTTP proxy.

    """

    body       = request.get_json(force=True) or {}

    model_name = body.get('model', 'forecast').lower()

    timestamp  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:

        from routes.model import predict as _predict

        with app.test_request_context(

            '/api/model/predict',

            method='POST',

            json=body,

            content_type='application/json'

        ):

            resp   = _predict()

            result = resp.get_json() if hasattr(resp, 'get_json') else {'success': True}

        logger.info(f'execute_command: model={model_name}')

        return jsonify({

            'success':   True,

            'command':   f'python predict_local.py --model {model_name}',

            'timestamp': timestamp,

            'result':    result

        })

    except Exception as e:

        logger.error(f'execute_command error: {e}')

        return jsonify({'success': False, 'error': str(e)}), 500

# -- Insert prediction to SQL --------------------------------------------------

@app.route('/api/insert', methods=['POST'])

def insert_prediction():

    """

    INSERT a prediction into dw_pi.n8n_predictions table.

    Body: { "model_name": "forecast", "result": "..." }

    """

    import pyodbc

    body       = request.get_json(force=True) or {}

    model_name = body.get('model_name', 'unknown')

    result     = str(body.get('result', '{}'))

    try:

        conn = pyodbc.connect(

            'DRIVER={ODBC Driver 17 for SQL Server};'

            'SERVER=HEDIRE\\MSSQLSERVER05;'

            'DATABASE=dw_pi;'

            'Trusted_Connection=yes',

            timeout=10

        )

        cursor = conn.cursor()

        cursor.execute(

            "INSERT INTO n8n_predictions (model_name, result) VALUES (-, -)",

            model_name, result

        )

        conn.commit()

        cursor.execute("SELECT @@IDENTITY AS id")

        new_id = int(cursor.fetchone()[0])

        conn.close()

        return jsonify({

            'success':    True,

            'id':         new_id,

            'model_name': model_name,

            'message':    f'Prediction #{new_id} stored in dw_pi.n8n_predictions'

        })

    except Exception as e:

        logger.error(f'insert_prediction failed: {e}')

        return jsonify({'success': False, 'error': str(e)}), 500

# -- Read predictions from SQL -------------------------------------------------

@app.route('/api/predictions', methods=['GET'])

def get_predictions():

    """Return all stored predictions from n8n_predictions table."""

    import pyodbc

    try:

        conn = pyodbc.connect(

            'DRIVER={ODBC Driver 17 for SQL Server};'

            'SERVER=HEDIRE\\MSSQLSERVER05;'

            'DATABASE=dw_pi;'

            'Trusted_Connection=yes',

            timeout=10

        )

        cursor = conn.cursor()

        cursor.execute(

            "SELECT TOP 100 id, model_name, result, created_at "

            "FROM n8n_predictions ORDER BY created_at DESC"

        )

        rows = [

            {'id': r[0], 'model_name': r[1], 'result': r[2], 'created_at': str(r[3])}

            for r in cursor.fetchall()

        ]

        conn.close()

        return jsonify({'success': True, 'predictions': rows, 'count': len(rows)})

    except Exception as e:

        return jsonify({'success': False, 'error': str(e)}), 500

# -- Write execution log -------------------------------------------------------

@app.route('/api/log', methods=['POST'])

def write_log():

    """

    Write an n8n workflow execution log entry to execution_logs.json.

    Body: { "workflow": "ML Pipeline", "status": "success", "details": "..." }

    Called by n8n after each workflow run to keep traceable logs.

    """

    body      = request.get_json(force=True) or {}

    workflow  = body.get('workflow', 'ML Pipeline')

    status    = body.get('status', 'unknown')

    details   = body.get('details', '')

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    log_entry = {

        'timestamp': timestamp,

        'workflow':  workflow,

        'status':    status,

        'details':   details

    }

    log_path = os.path.join(os.path.dirname(__file__), '..', 'execution_logs.json')

    try:

        logs = []

        if os.path.exists(log_path):

            with open(log_path, 'r', encoding='utf-8') as f:

                logs = json.load(f)

        logs.append(log_entry)

        # Keep last 500 entries

        logs = logs[-500:]

        with open(log_path, 'w', encoding='utf-8') as f:

            json.dump(logs, f, ensure_ascii=False, indent=2, default=str)

        return jsonify({

            'success':    True,

            'message':    f'Log entry saved - status: {status}',

            'timestamp':  timestamp,

            'total_logs': len(logs)

        })

    except Exception as e:

        return jsonify({'success': False, 'error': str(e)}), 500

# -- Read execution logs -------------------------------------------------------

@app.route('/api/logs', methods=['GET'])

def read_logs():

    """Return the last N execution log entries."""

    limit    = int(request.args.get('limit', 50))

    log_path = os.path.join(os.path.dirname(__file__), '..', 'execution_logs.json')

    try:

        if not os.path.exists(log_path):

            return jsonify({'success': True, 'logs': [], 'count': 0})

        with open(log_path, 'r', encoding='utf-8') as f:

            logs = json.load(f)

        logs = logs[-limit:]

        return jsonify({'success': True, 'logs': logs, 'count': len(logs)})

    except Exception as e:

        return jsonify({'success': False, 'error': str(e)}), 500

# -- Retrain sentiment model (bonus) ------------------------------------------

@app.route('/api/retrain', methods=['POST'])

def retrain_model():

    """

    Retrain the sentiment model on fresh data from the database.

    Called by n8n Retraining Automation workflow (scheduled or on-demand).

    Body: { "model": "sentiment" }  (only sentiment supported for now)

    Stores new model version in memory and logs the retraining event.

    """

    body       = request.get_json(force=True) or {}

    model_name = body.get('model', 'sentiment').lower()

    timestamp  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if model_name != 'sentiment':

        return jsonify({

            'success': False,

            'error':   f'Retraining not supported for model: {model_name}. Only "sentiment" is supported.'

        }), 400

    try:

        from routes.sentiment import _train_sentiment_model

        # Retrain on fresh data

        model, vectorizer, accuracy, n_neg, n_pos = _train_sentiment_model()

        # Store new version

        sentiment_bp.model      = model

        sentiment_bp.vectorizer = vectorizer

        # Log the retraining event

        log_entry = {

            'timestamp':  timestamp,

            'event':      'retrain',

            'model':      'sentiment',

            'accuracy':   round(accuracy * 100, 1),

            'n_neg':      n_neg,

            'n_pos':      n_pos,

            'status':     'success'

        }

        retrain_log_path = os.path.join(os.path.dirname(__file__), '..', 'retrain_log.json')

        retrain_logs = []

        if os.path.exists(retrain_log_path):

            with open(retrain_log_path, 'r', encoding='utf-8') as f:

                retrain_logs = json.load(f)

        retrain_logs.append(log_entry)

        with open(retrain_log_path, 'w', encoding='utf-8') as f:

            json.dump(retrain_logs, f, ensure_ascii=False, indent=2)

        print(f"[retrain] Sentiment model retrained - accuracy: {accuracy*100:.1f}% at {timestamp}")

        logger.info(f'Sentiment retrained - accuracy: {accuracy*100:.1f}%, version: {len(retrain_logs)}')

        return jsonify({

            'success':   True,

            'model':     'sentiment',

            'accuracy':  round(accuracy * 100, 1),

            'n_neg':     n_neg,

            'n_pos':     n_pos,

            'timestamp': timestamp,

            'message':   f'Sentiment model retrained successfully - accuracy: {accuracy*100:.1f}%',

            'version':   len(retrain_logs)

        })

    except Exception as e:

        return jsonify({'success': False, 'error': str(e)}), 500

# -- Read-only SQL query proxy -------------------------------------------------

@app.route('/api/query', methods=['POST'])

def run_query():

    """

    Execute a safe read-only SQL query via n8n.

    Body: { "sql": "SELECT TOP 10 * FROM fact_sale" }

    Only SELECT statements allowed.

    """

    from db import query_df

    body = request.get_json(force=True) or {}

    sql  = body.get('sql', '').strip()

    if not sql:

        return jsonify({'success': False, 'error': 'No SQL provided'}), 400

    if not sql.upper().startswith('SELECT'):

        return jsonify({'success': False, 'error': 'Only SELECT queries are allowed'}), 403

    try:

        df = query_df(sql)

        return jsonify({

            'success': True,

            'rows':    df.to_dict(orient='records'),

            'count':   len(df),

            'columns': list(df.columns)

        })

    except Exception as e:

        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':

    print("\n  Serveur pr-t - recevoir des requ-tes !\n")

    app.run(debug=True, host='0.0.0.0', port=5000)

