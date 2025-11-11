#!/bin/bash
# Phase 3 Verification Script
# Checks that all Phase 3 files are in place and syntax is valid

set -e

echo "🔍 Verifying Phase 3 Implementation..."
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success_count=0
total_checks=0

check_file() {
    local file=$1
    local description=$2
    total_checks=$((total_checks + 1))

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description: $file"
        success_count=$((success_count + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $description: $file (MISSING)"
        return 1
    fi
}

echo "=== Backend Files ==="
check_file "api/models.py" "Pydantic models (updated)"
check_file "api/routes/scrape.py" "Scraping endpoints (updated)"
echo ""

echo "=== Frontend Components ==="
check_file "tui/src/components/App.tsx" "Main App (3 tabs)"
check_file "tui/src/components/BatchProcessingTab.tsx" "Batch Processing Tab"
echo ""

echo "=== State Management ==="
check_file "tui/src/stores/batch.ts" "Batch store"
echo ""

echo "=== API Client ==="
check_file "tui/src/api/client.ts" "API client (scrapeBatch method)"
echo ""

echo "=== Documentation ==="
check_file "PHASE3-IMPLEMENTATION-COMPLETE.md" "Phase 3 completion doc"
echo ""

# Check Python syntax
echo "=== Python Syntax Check ==="
if command -v python3 &> /dev/null; then
    if python3 -m py_compile api/models.py 2>/dev/null; then
        echo -e "${GREEN}✓${NC} api/models.py syntax valid"
        success_count=$((success_count + 1))
    else
        echo -e "${RED}✗${NC} api/models.py syntax invalid"
    fi
    total_checks=$((total_checks + 1))

    if python3 -m py_compile api/routes/scrape.py 2>/dev/null; then
        echo -e "${GREEN}✓${NC} api/routes/scrape.py syntax valid"
        success_count=$((success_count + 1))
    else
        echo -e "${RED}✗${NC} api/routes/scrape.py syntax invalid"
    fi
    total_checks=$((total_checks + 1))
else
    echo -e "${YELLOW}⚠${NC} Python3 not found, skipping syntax check"
fi
echo ""

# Check batch endpoint functionality
echo "=== Batch Endpoint Validation ==="
echo "Checking BatchResult model fields..."
if python3 -c "from api.models import BatchResult; br = BatchResult(url='test', index=0, success=True, execution_time=1.0); print('✓ BatchResult model OK')" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} BatchResult model instantiates correctly"
    success_count=$((success_count + 1))
else
    echo -e "${RED}✗${NC} BatchResult model has issues"
fi
total_checks=$((total_checks + 1))

echo "Checking BatchScrapeResponse model fields..."
if python3 -c "from api.models import BatchScrapeResponse; bsr = BatchScrapeResponse(success=True, results=[], summary={}); print('✓ BatchScrapeResponse model OK')" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} BatchScrapeResponse model instantiates correctly"
    success_count=$((success_count + 1))
else
    echo -e "${RED}✗${NC} BatchScrapeResponse model has issues"
fi
total_checks=$((total_checks + 1))
echo ""

# Verify URL parsing in batch store
echo "=== Batch Store Validation ==="
echo "Checking batch store exports..."
if grep -q "export const \[batchUrls" "tui/src/stores/batch.ts" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Batch store exports found"
    success_count=$((success_count + 1))
else
    echo -e "${RED}✗${NC} Batch store exports missing"
fi
total_checks=$((total_checks + 1))

if grep -q "loadUrlsFromFile" "tui/src/stores/batch.ts" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} File upload helper found"
    success_count=$((success_count + 1))
else
    echo -e "${RED}✗${NC} File upload helper missing"
fi
total_checks=$((total_checks + 1))
echo ""

# Verify API client method
echo "=== API Client Validation ==="
if grep -q "scrapeBatch" "tui/src/api/client.ts" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} scrapeBatch method found in API client"
    success_count=$((success_count + 1))
else
    echo -e "${RED}✗${NC} scrapeBatch method missing from API client"
fi
total_checks=$((total_checks + 1))
echo ""

# Verify App integration
echo "=== App Integration Validation ==="
if grep -q "BatchProcessingTab" "tui/src/components/App.tsx" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} BatchProcessingTab imported in App"
    success_count=$((success_count + 1))
else
    echo -e "${RED}✗${NC} BatchProcessingTab not imported in App"
fi
total_checks=$((total_checks + 1))

if grep -q "'Single URL', 'Batch', 'Metrics'" "tui/src/components/App.tsx" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} 3 tabs configured in App (including Batch)"
    success_count=$((success_count + 1))
else
    echo -e "${RED}✗${NC} Batch tab not added to tabs array"
fi
total_checks=$((total_checks + 1))
echo ""

# Summary
echo "================================"
echo "Summary: $success_count/$total_checks checks passed"
echo "================================"

if [ $success_count -eq $total_checks ]; then
    echo -e "${GREEN}✅ All checks passed! Phase 3 is ready for testing.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start backend: ./run-api.sh"
    echo "2. Start TUI: cd tui && bun run dev"
    echo "3. Navigate to 'Batch' tab (second tab)"
    echo "4. Test batch processing with 2-5 URLs"
    echo ""
    echo "Quick test:"
    echo "  URLs: https://example.com, https://httpbin.org/html"
    echo "  Prompt: Extract the page title"
    echo "  Click 'Start Batch' and watch progress!"
    exit 0
else
    echo -e "${RED}❌ Some checks failed. Please review the output above.${NC}"
    exit 1
fi
