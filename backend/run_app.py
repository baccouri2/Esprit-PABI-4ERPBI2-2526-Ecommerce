"""
Startup script with environment fixes for Windows statsmodels issues
"""
import os
import sys

# Fix statsmodels threading issues on Windows
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

# Disable numpy threading
os.environ['NUMPY_EXPERIMENTAL_ARRAY_FUNCTION'] = '0'

# Now import and run the app
if __name__ == '__main__':
    from app import app
    print("\n  Server ready to receive requests!\n")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
