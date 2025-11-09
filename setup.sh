#!/bin/bash
set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Web Scraping AI Agent${NC}"
echo "========================================"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Ollama is running
echo -e "\n${YELLOW}[1/4]${NC} Checking Ollama service..."
if ! pgrep -f ollama > /dev/null; then
    echo "Error: Ollama service is not running"
    echo "Start it with: systemctl --user start ollama"
    exit 1
fi
echo "✓ Ollama is running"

# Pull required embedding model
echo -e "\n${YELLOW}[2/4]${NC} Downloading nomic-embed-text model..."
if ollama pull nomic-embed-text; then
    echo "✓ Embedding model downloaded"
else
    echo "Warning: Failed to download embedding model"
    echo "You may need to download it manually: ollama pull nomic-embed-text"
fi

# Create virtual environment
echo -e "\n${YELLOW}[3/4]${NC} Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Install dependencies
echo -e "\n${YELLOW}[4/4]${NC} Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null
pip install -r requirements.txt

# Install playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

echo -e "\n${GREEN}Setup complete!${NC}"
echo ""
echo "To run the scraper:"
echo "  1. source venv/bin/activate"
echo "  2. streamlit run scraper.py"
echo ""
echo "Available models:"
echo "  - llama3.1 (recommended)"
echo "  - qwen2.5-coder (good for technical content)"
echo "  - deepseek-coder-v2"
