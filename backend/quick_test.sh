#!/bin/bash

echo "=========================================="
echo "🧪 QUICK VERIFICATION TEST"
echo "=========================================="
echo ""

# Check if in backend directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Please run this from the backend/ directory"
    echo "   cd backend && bash quick_test.sh"
    exit 1
fi

echo "1️⃣ Testing Python imports..."
python3 << 'EOF'
try:
    from app.engines.complete_hybrid_engine import CompleteHybridEngine
    print("   ✅ Complete hybrid engine")
except Exception as e:
    print(f"   ❌ Complete hybrid engine: {e}")
    exit(1)

try:
    from app.scanners.secrets_scanner import get_secrets_scanner
    print("   ✅ Secrets scanner")
except Exception as e:
    print(f"   ❌ Secrets scanner: {e}")
    exit(1)

try:
    from app.scanners.license_scanner import get_license_scanner
    print("   ✅ License scanner")
except Exception as e:
    print(f"   ❌ License scanner: {e}")
    exit(1)

try:
    from app.core.policy_engine import PolicyEngine
    print("   ✅ Policy engine")
except Exception as e:
    print(f"   ❌ Policy engine: {e}")
    exit(1)

try:
    from app.services.gemini_analyzer import GeminiAnalyzer
    print("   ✅ Gemini analyzer")
except Exception as e:
    print(f"   ❌ Gemini analyzer: {e}")
    exit(1)

try:
    from app.api.routes import router
    print("   ✅ API routes")
except Exception as e:
    print(f"   ❌ API routes: {e}")
    exit(1)

print("\n✅ All imports successful!")
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Import test failed"
    exit 1
fi

echo ""
echo "2️⃣ Testing syntax..."
python3 -m py_compile app/engines/complete_hybrid_engine.py 2>&1 | grep -q "SyntaxError" && echo "   ❌ Syntax error in engine" && exit 1
python3 -m py_compile app/scanners/secrets_scanner.py 2>&1 | grep -q "SyntaxError" && echo "   ❌ Syntax error in secrets" && exit 1
python3 -m py_compile app/scanners/license_scanner.py 2>&1 | grep -q "SyntaxError" && echo "   ❌ Syntax error in licenses" && exit 1
echo "   ✅ All syntax valid"

echo ""
echo "3️⃣ Testing FastAPI app..."
python3 << 'EOF'
try:
    from app.main import app
    print("   ✅ FastAPI app loads correctly")
except Exception as e:
    print(f"   ❌ FastAPI app error: {e}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ VERIFICATION COMPLETE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start server: uvicorn app.main:app --reload"
echo "2. Test endpoint: curl http://localhost:8000/health"
echo "3. Run full test: python test_analysis.py"
echo ""
echo "🎉 Your solution is ready to run!"
