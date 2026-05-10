"""
Diagnostic script to identify and fix Python backend startup issues
"""
import sys
import os
import subprocess
import time

print("=" * 60)
print("  BACKEND DIAGNOSTIC AND FIX TOOL")
print("=" * 60)
print()

# Set environment variables to fix threading issues
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    if package_name is None:
        package_name = module_name
    
    print(f"Testing {module_name}...", end=" ")
    sys.stdout.flush()
    
    try:
        start = time.time()
        __import__(module_name)
        elapsed = time.time() - start
        
        if elapsed > 5:
            print(f"⚠️  SLOW ({elapsed:.1f}s)")
            return 'slow'
        else:
            print(f"✓ OK ({elapsed:.2f}s)")
            return 'ok'
    except ImportError as e:
        print(f"✗ MISSING")
        return 'missing'
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return 'error'

print("Step 1: Testing basic imports")
print("-" * 60)

results = {}
packages = [
    ('flask', 'flask'),
    ('flask_cors', 'flask-cors'),
    ('pandas', 'pandas'),
    ('numpy', 'numpy'),
    ('sklearn', 'scikit-learn'),
    ('xgboost', 'xgboost'),
    ('scipy', 'scipy'),
    ('joblib', 'joblib'),
    ('pdfplumber', 'pdfplumber'),
    ('openpyxl', 'openpyxl'),
    ('pyodbc', 'pyodbc'),
]

for module, package in packages:
    results[module] = test_import(module, package)

print()
print("Step 2: Testing statsmodels (this may take a while)...")
print("-" * 60)

# Test statsmodels with timeout
print("Testing statsmodels import (30s timeout)...", end=" ")
sys.stdout.flush()

try:
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Import timed out")
    
    # This won't work on Windows, so we'll use a different approach
    start = time.time()
    
    # Try to import in a subprocess with timeout
    result = subprocess.run(
        [sys.executable, '-c', 'import statsmodels; print("OK")'],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    elapsed = time.time() - start
    
    if result.returncode == 0:
        if elapsed > 10:
            print(f"⚠️  SLOW ({elapsed:.1f}s) - This is the problem!")
            results['statsmodels'] = 'slow'
        else:
            print(f"✓ OK ({elapsed:.2f}s)")
            results['statsmodels'] = 'ok'
    else:
        print(f"✗ ERROR: {result.stderr}")
        results['statsmodels'] = 'error'
        
except subprocess.TimeoutExpired:
    print("✗ TIMEOUT (>30s) - This is the problem!")
    results['statsmodels'] = 'timeout'
except Exception as e:
    print(f"✗ ERROR: {e}")
    results['statsmodels'] = 'error'

print()
print("=" * 60)
print("  DIAGNOSIS RESULTS")
print("=" * 60)

missing = [k for k, v in results.items() if v == 'missing']
errors = [k for k, v in results.items() if v in ('error', 'timeout', 'slow')]

if missing:
    print(f"\n❌ Missing packages: {', '.join(missing)}")
    print(f"   Run: pip install {' '.join(missing)}")

if errors:
    print(f"\n❌ Problem packages: {', '.join(errors)}")
    
    if 'statsmodels' in errors:
        print("\n🔧 SOLUTION FOR STATSMODELS:")
        print("   The statsmodels package is hanging during import.")
        print("   This is a known issue on Windows.")
        print()
        print("   Option 1: Reinstall statsmodels")
        print("   ---------------------------------")
        print("   pip uninstall -y statsmodels")
        print("   pip install statsmodels==0.14.4 --no-cache-dir")
        print()
        print("   Option 2: Use XGBoost only (skip ARIMA/SARIMA)")
        print("   -----------------------------------------------")
        print("   Modify forecast.py to only use XGBoost model")
        print()
        
        response = input("   Would you like to try Option 1 now? (y/n): ")
        if response.lower() == 'y':
            print("\n   Uninstalling statsmodels...")
            subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', 'statsmodels'])
            
            print("   Installing statsmodels 0.14.4...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'statsmodels==0.14.4', '--no-cache-dir'])
            
            print("\n   Testing again...")
            test_import('statsmodels')

if not missing and not errors:
    print("\n✅ All packages are working correctly!")
    print("   The issue might be elsewhere. Check:")
    print("   - Database connection (SQL Server)")
    print("   - Port 5000 availability")
    print("   - Firewall settings")

print()
print("=" * 60)
print("  NEXT STEPS")
print("=" * 60)
print()
print("1. If statsmodels is fixed, try running: python app.py")
print("2. If still having issues, try: python run_app.py")
print("3. Check the execution_logs.json file for errors")
print()
