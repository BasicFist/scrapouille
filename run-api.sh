#!/usr/bin/env bash
#
# Launch FastAPI Server for Scrapouille
# Phase 1: Foundation
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Scrapouille API Server${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. Check if venv exists
if [ ! -d "venv-isolated" ]; then
  echo -e "${RED}Error: venv-isolated not found${NC}"
  echo "Please run setup.sh first"
  exit 1
fi

# 2. Activate venv
echo -e "${YELLOW}Activating Python environment...${NC}"
source venv-isolated/bin/activate

# 3. Check if FastAPI is installed
if ! python -c "import fastapi" 2>/dev/null; then
  echo -e "${YELLOW}Installing FastAPI dependencies...${NC}"
  pip install fastapi uvicorn[standard] python-multipart
fi

# 4. Check Redis (optional, warn if not available)
if ! redis-cli ping &> /dev/null; then
  echo -e "${YELLOW}⚠️  Redis not running - caching will be disabled${NC}"
  echo "   Start Redis with: redis-server --daemonize yes"
  echo ""
fi

# 5. Check Ollama (warn if not available)
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
  echo -e "${YELLOW}⚠️  Ollama not running - scraping will fail${NC}"
  echo "   Start Ollama with: ollama serve"
  echo ""
fi

# 6. Start FastAPI server
echo -e "${GREEN}Starting FastAPI server on http://localhost:8000${NC}"
echo -e "${GREEN}API documentation: http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

python -m api.main
