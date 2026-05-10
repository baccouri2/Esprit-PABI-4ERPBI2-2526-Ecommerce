"""
Minimal Flask app to test if basic functionality works
"""
import os
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'

from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Minimal app is running'})

@app.route('/api/test', methods=['GET'])
def test():
    # Test basic imports
    import pandas as pd
    import numpy as np
    
    return jsonify({
        'status': 'ok',
        'pandas_version': pd.__version__,
        'numpy_version': np.__version__
    })

if __name__ == '__main__':
    print("=" * 60)
    print("  MINIMAL TEST APP")
    print("=" * 60)
    print("  Starting on http://0.0.0.0:5000")
    print("  Test endpoints:")
    print("    GET /api/health")
    print("    GET /api/test")
    print("=" * 60)
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
