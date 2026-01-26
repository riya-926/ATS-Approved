"""
Diagnostic script to check API setup and identify issues.
"""
import sys
from pathlib import Path

print("=" * 80)
print("API Diagnostic Check")
print("=" * 80)
print()

# Check 1: Python version
print("[1/7] Checking Python version...")
print(f"   Python: {sys.version}")
if sys.version_info < (3, 10):
    print("   [WARNING] Python 3.10+ recommended")
else:
    print("   [OK] Python version OK")
print()

# Check 2: Required modules
print("[2/7] Checking required modules...")
required_modules = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "anthropic",
    "docx",
    "dotenv",
    "requests"
]

missing_modules = []
for module in required_modules:
    try:
        if module == "docx":
            __import__("docx")
        elif module == "dotenv":
            __import__("dotenv")
        else:
            __import__(module)
        print(f"   [OK] {module}")
    except ImportError:
        print(f"   [MISSING] {module}")
        missing_modules.append(module)

if missing_modules:
    print(f"\n   ⚠️  Missing modules: {', '.join(missing_modules)}")
    print("   Install with: python -m pip install -r requirements.txt")
print()

# Check 3: Environment variables
print("[3/7] Checking environment variables...")
try:
    from dotenv import load_dotenv
    import os
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print(f"   [OK] ANTHROPIC_API_KEY found (length: {len(api_key)})")
    else:
        print("   [WARNING] ANTHROPIC_API_KEY not found in .env file")
        print("   This is needed for rewrite suggestions")
except Exception as e:
    print(f"   [WARNING] Error checking env: {e}")
print()

# Check 4: Import main app
print("[4/7] Checking app imports...")
try:
    from app.main import app
    print("   [OK] app.main imported successfully")
except Exception as e:
    print(f"   [ERROR] Error importing app.main: {e}")
    print("   This is the main issue!")
    import traceback
    traceback.print_exc()
    sys.exit(1)
print()

# Check 5: Check API routers
print("[5/7] Checking API routers...")
try:
    from app.api import parse, jd, evidence, rewrite, test_roundtrip
    print("   [OK] All routers imported successfully")
except Exception as e:
    print(f"   [ERROR] Error importing routers: {e}")
    import traceback
    traceback.print_exc()
print()

# Check 6: Check rewrite module specifically
print("[6/7] Checking rewrite module...")
try:
    from app.rewrite.suggester import suggest_rewrites
    print("   [OK] Rewrite suggester imported successfully")
except Exception as e:
    print(f"   [WARNING] Error importing rewrite suggester: {e}")
    print("   This might cause issues with /rewrite/suggest endpoint")
    import traceback
    traceback.print_exc()
print()

# Check 7: Test uvicorn availability
print("[7/7] Checking uvicorn...")
try:
    import uvicorn
    print(f"   [OK] uvicorn available (version: {uvicorn.__version__})")
except ImportError:
    print("   [MISSING] uvicorn not found")
    print("   Install with: python -m pip install uvicorn[standard]")
print()

print("=" * 80)
if missing_modules:
    print("[WARNING] Some modules are missing. Install them first.")
else:
    print("[SUCCESS] All checks passed! You should be able to run the API.")
print("=" * 80)
print()
print("To start the API, run:")
print("  uvicorn app.main:app --reload")
