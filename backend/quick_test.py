"""Quick test to identify hanging imports"""
import sys
import time

def test_import(name):
    print(f"Importing {name}...", end=" ", flush=True)
    start = time.time()
    try:
        __import__(name)
        elapsed = time.time() - start
        print(f"OK ({elapsed:.2f}s)")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

print("Testing imports one by one:\n")

# Test in order
modules = [
    'flask',
    'pandas',
    'numpy',
]

for mod in modules:
    if not test_import(mod):
        break
    time.sleep(0.5)

print("\nNow testing sklearn...")
test_import('sklearn')
