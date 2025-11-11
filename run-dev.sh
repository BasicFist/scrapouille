#!/usr/bin/env bash
#
# Launch Development Environment
# Starts FastAPI backend + TUIjoli frontend
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Trap Ctrl+C and cleanup
cleanup() {
  echo ""
  echo -e "${YELLOW}Shutting down...${NC}"
  if [ -n "${API_PID:-}" ]; then
    echo "  Stopping API server (PID: $API_PID)"
    kill $API_PID 2>/dev/null || true
  fi
  exit 0
}
trap cleanup SIGINT SIGTERM

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                       ║${NC}"
echo -e "${CYAN}║   SCRAPOUILLE v3.0.5 - Phase 1 Development Mode      ║${NC}"
echo -e "${CYAN}║                                                       ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Check prerequisites
echo -e "${BLUE}[1/5]${NC} Checking prerequisites..."

if [ ! -d "venv-isolated" ]; then
  echo -e "${RED}   ✗ venv-isolated not found${NC}"
  echo "   Run: ./setup.sh"
  exit 1
fi
echo -e "${GREEN}   ✓ Python environment found${NC}"

if ! command -v bun &> /dev/null; then
  echo -e "${RED}   ✗ Bun not found${NC}"
  echo "   Install from: https://bun.sh"
  exit 1
fi
echo -e "${GREEN}   ✓ Bun runtime found ($(bun --version))${NC}"

# 2. Check optional services
echo ""
echo -e "${BLUE}[2/5]${NC} Checking backend services..."

if redis-cli ping &> /dev/null; then
  echo -e "${GREEN}   ✓ Redis is running${NC}"
else
  echo -e "${YELLOW}   ⚠  Redis not running (caching disabled)${NC}"
  echo "      Start with: redis-server --daemonize yes"
fi

if curl -s http://localhost:11434/api/tags &> /dev/null; then
  echo -e "${GREEN}   ✓ Ollama is running${NC}"
else
  echo -e "${YELLOW}   ⚠  Ollama not running (scraping will fail)${NC}"
  echo "      Start with: ollama serve"
fi

# 3. Install dependencies
echo ""
echo -e "${BLUE}[3/5]${NC} Installing dependencies..."

# Python dependencies
source venv-isolated/bin/activate
if ! python -c "import fastapi" 2>/dev/null; then
  echo "   Installing FastAPI..."
  pip install -q fastapi uvicorn[standard] python-multipart
fi
echo -e "${GREEN}   ✓ Python dependencies ready${NC}"

# TypeScript dependencies
cd tui
if [ ! -d "node_modules" ]; then
  echo "   Installing Bun dependencies..."
  bun install
fi
echo -e "${GREEN}   ✓ TypeScript dependencies ready${NC}"
cd ..

# 4. Start FastAPI backend
echo ""
echo -e "${BLUE}[4/5]${NC} Starting FastAPI backend..."
echo -e "${GREEN}   → Starting on http://localhost:8000${NC}"
echo -e "${GREEN}   → API docs: http://localhost:8000/docs${NC}"

source venv-isolated/bin/activate
python -m api.main > /tmp/scrapouille-api.log 2>&1 &
API_PID=$!

# Wait for API to be ready
echo "   Waiting for API to start..."
for i in {1..15}; do
  if curl -s http://localhost:8000/health &> /dev/null; then
    echo -e "${GREEN}   ✓ API is ready${NC}"
    break
  fi
  if [ $i -eq 15 ]; then
    echo -e "${RED}   ✗ API failed to start${NC}"
    echo "   Check logs: tail -f /tmp/scrapouille-api.log"
    kill $API_PID 2>/dev/null || true
    exit 1
  fi
  sleep 1
done

# 5. Start TUIjoli frontend
echo ""
echo -e "${BLUE}[5/5]${NC} Starting TUIjoli frontend..."
echo -e "${GREEN}   → Press Ctrl+C to exit${NC}"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd tui
bun run dev

# Cleanup (if we get here via normal exit)
cleanup
