#!/bin/bash
# Scrapouille TUI Launcher
# Inspired by TUIjoli's example runner architecture

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     Scrapouille TUI - v3.0 Phase 4    ║${NC}"
echo -e "${CYAN}║  AI-Powered Web Scraping Terminal UI  ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv-isolated" ]; then
    echo -e "${RED}✗ Virtual environment not found!${NC}"
    echo -e "${YELLOW}Please run: source venv-isolated/bin/activate${NC}"
    exit 1
fi

# Activate virtual environment
source venv-isolated/bin/activate

# Check if required dependencies are installed
if ! python -c "import textual" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Textual not found. Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Check Ollama connection
echo -e "${CYAN}Checking Ollama connection...${NC}"
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
else
    echo -e "${YELLOW}⚠ Ollama not detected. Please run: ollama serve${NC}"
    echo -e "${YELLOW}  The TUI will still start but scraping will fail.${NC}"
fi

# Check Redis connection
echo -e "${CYAN}Checking Redis connection...${NC}"
if redis-cli ping >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is running (caching enabled)${NC}"
else
    echo -e "${YELLOW}⚠ Redis not detected. Caching will be disabled.${NC}"
fi

echo ""
echo -e "${GREEN}Starting Scrapouille TUI...${NC}"
echo -e "${CYAN}Press Ctrl+Q to quit${NC}"
echo ""

# Launch TUI
python tui.py

echo ""
echo -e "${GREEN}✓ Scrapouille TUI closed${NC}"
