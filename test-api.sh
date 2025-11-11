#!/usr/bin/env bash
set -euo pipefail

source venv-isolated/bin/activate

# Start API in background
python -m api.main > /tmp/scrapouille-api-test.log 2>&1 &
API_PID=$!

# Wait for startup
echo "Starting API server (PID: $API_PID)..."
sleep 4

# Test health endpoint
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
  echo "✅ API server started successfully"
  echo ""
  echo "Health check response:"
  curl -s http://localhost:8000/health | python -m json.tool
  echo ""
  echo "✅ Phase 1 backend test PASSED"
else
  echo "❌ API server failed to start"
  echo "Logs:"
  cat /tmp/scrapouille-api-test.log
  kill $API_PID 2>/dev/null || true
  exit 1
fi

# Cleanup
kill $API_PID 2>/dev/null || true
