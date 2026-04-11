"""
ML Dashboard Backend API
Serves predictions from the 5 ML models in the ml/ folder.
"""

import sys
import os

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

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(forecast_bp, url_prefix='/api/forecast')
app.register_blueprint(segmentation_bp, url_prefix='/api/segmentation')
app.register_blueprint(anomaly_bp, url_prefix='/api/anomaly')
app.register_blueprint(promotion_bp, url_prefix='/api/promotion')
app.register_blueprint(recommendations_bp, url_prefix='/api/recommendations')
app.register_blueprint(sentiment_bp, url_prefix='/api/sentiment')
app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'ML Dashboard API is running'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
