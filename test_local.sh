#!/bin/bash
set -e

echo "🧪 Testing GitHub Guardrails..."
echo ""

# Check files exist
echo "✓ Checking files..."
test -f backend/app/main.py || { echo "❌ main.py missing"; exit 1; }
test -f backend/app/services/gemini_analyzer.py || { echo "❌ gemini_analyzer.py missing"; exit 1; }
test -f github-app/src/index.ts || { echo "❌ index.ts missing"; exit 1; }

# Check line counts
echo "✓ Checking code completeness..."
BACKEND_LINES=$(find backend/app -name "*.py" | xargs wc -l | tail -1 | awk '{print $1}')
if [ "$BACKEND_LINES" -lt 700 ]; then
    echo "❌ Backend too short: $BACKEND_LINES lines (need 700+)"
    exit 1
fi
echo "  Backend: $BACKEND_LINES lines ✓"

APP_LINES=$(find github-app/src -name "*.ts" | xargs wc -l | tail -1 | awk '{print $1}')
if [ "$APP_LINES" -lt 200 ]; then
    echo "❌ GitHub app too short: $APP_LINES lines (need 200+)"
    exit 1
fi
echo "  GitHub app: $APP_LINES lines ✓"

echo ""
echo "✅ All checks passed!"
echo ""
echo "Next steps:"
echo "1. docker-compose up"
echo "2. curl http://localhost:8000/health"
echo "3. Deploy to Render"
