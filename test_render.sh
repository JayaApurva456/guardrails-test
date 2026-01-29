#!/bin/bash

# Test Render Deployment
# Usage: ./test_render.sh https://your-app.onrender.com

if [ -z "$1" ]; then
    echo "Usage: ./test_render.sh <RENDER_URL>"
    echo "Example: ./test_render.sh https://guardrails-backend.onrender.com"
    exit 1
fi

RENDER_URL=$1

echo " Testing Render Deployment: $RENDER_URL"
echo "=================================================="

# Test 1: Health Check
echo ""
echo "1️ Testing Health Endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$RENDER_URL/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Health check passed!"
    echo "   Response: $BODY"
else
    echo "❌ Health check failed! (HTTP $HTTP_CODE)"
    exit 1
fi

# Test 2: API Documentation
echo ""
echo "2️ Testing API Documentation..."
DOCS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$RENDER_URL/docs")
if [ "$DOCS_CODE" = "200" ]; then
    echo " API docs accessible!"
    echo "   URL: $RENDER_URL/docs"
else
    echo "⚠️  API docs not accessible (HTTP $DOCS_CODE)"
fi

# Test 3: Analyze Endpoint
echo ""
echo "3️ Testing Analysis Endpoint..."
ANALYSIS_RESPONSE=$(curl -s -X POST "$RENDER_URL/api/analyze/file" \
    -H "Content-Type: application/json" \
    -d '{
        "code": "API_KEY = \"sk-test123\"\neval(input())\nimport pickle",
        "filename": "test.py",
        "language": "python"
    }')

if echo "$ANALYSIS_RESPONSE" | grep -q "violations"; then
    echo "✅ Analysis endpoint working!"
    TOTAL_COUNT=$(echo "$ANALYSIS_RESPONSE" | grep -o '"total_count":[0-9]*' | grep -o '[0-9]*')
    echo "   Found $TOTAL_COUNT violations"
    
    # Show sample violation
    echo ""
    echo "   Sample violations:"
    echo "$ANALYSIS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for v in data.get('violations', [])[:3]:
        print(f\"   - {v['type']}: {v['severity']} (line {v['line']})\")
except:
    pass
" 2>/dev/null || echo "   (Could not parse violations)"
else
    echo "❌ Analysis endpoint failed!"
    echo "   Response: $ANALYSIS_RESPONSE"
    exit 1
fi

# Test 4: Policy Endpoint
echo ""
echo "4️⃣ Testing Policy Endpoint..."
POLICY_RESPONSE=$(curl -s "$RENDER_URL/api/policy/test/repo")
if echo "$POLICY_RESPONSE" | grep -q "mode"; then
    echo "✅ Policy endpoint working!"
    MODE=$(echo "$POLICY_RESPONSE" | grep -o '"mode":"[^"]*"' | cut -d'"' -f4)
    echo "   Mode: $MODE"
else
    echo "⚠️  Policy endpoint not accessible"
fi

# Test 5: Scanners Status
echo ""
echo "5️⃣ Testing Scanners Status..."
SCANNERS_RESPONSE=$(curl -s "$RENDER_URL/api/scanners/status")
if echo "$SCANNERS_RESPONSE" | grep -q "static_analyzers"; then
    echo "✅ Scanners status endpoint working!"
    echo "$SCANNERS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('   Static analyzers:', 'bandit' if data['static_analyzers']['python'].get('bandit') else 'patterns only')
    print('   Secrets scanner:', 'detect-secrets' if data['secrets'].get('detect_secrets') else 'patterns only')
    print('   License scanner:', 'scancode' if data['licenses'].get('scancode') else 'patterns only')
    print('   AI analyzer:', 'enabled' if data['ai'].get('gemini') else 'disabled')
except:
    print('   (Could not parse status)')
" 2>/dev/null
else
    echo "⚠️  Scanners status not accessible"
fi

echo ""
echo "=================================================="
echo "✅ DEPLOYMENT TEST COMPLETE!"
echo ""
echo "Your API is live at: $RENDER_URL"
echo "API Docs: $RENDER_URL/docs"
echo ""
echo "🎉 Ready for production use!"
