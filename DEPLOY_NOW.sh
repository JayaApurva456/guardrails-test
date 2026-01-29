#!/bin/bash
# 🚀 Quick Deployment Script

echo "🚀 DEPLOYING COMPLETE 1ST PRIZE SOLUTION"
echo "========================================="
echo ""

# Check if in correct directory
if [ ! -f "backend/app/main.py" ]; then
    echo "❌ Error: Please run from INTEGRATED_COMPLETE_SOLUTION directory"
    exit 1
fi

echo "1️⃣  Installing backend dependencies..."
cd backend
pip install -r requirements.txt || { echo "❌ Failed to install dependencies"; exit 1; }

echo ""
echo "2️⃣  Running comprehensive tests..."
python test_complete.py || { echo "⚠️  Some tests failed, but continuing..."; }

echo ""
echo "3️⃣  Starting backend server..."
echo "   Dashboard: http://localhost:8000/dashboard"
echo "   API Docs: http://localhost:8000/docs"
echo "   Health: http://localhost:8000/health"
echo ""
echo "✅ Ready! Starting server..."
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
