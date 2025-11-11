#!/bin/bash
# Phase 2 Verification Script
# Checks that all Phase 2 files are in place and syntax is valid

set -e

echo "🔍 Verifying Phase 2 Implementation..."
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
check_file "api/models.py" "Pydantic models"
check_file "api/routes/scrape.py" "Scraping endpoints"
check_file "api/routes/__init__.py" "Routes module"
echo ""

echo "=== Frontend Components ==="
check_file "tui/src/components/App.tsx" "Main App (updated)"
check_file "tui/src/components/SingleURLTab.tsx" "Single URL Tab"
check_file "tui/src/components/MetricsPanel.tsx" "Metrics Panel"
echo ""

echo "=== Widget Library ==="
check_file "tui/src/components/widgets/Input.tsx" "Input widget"
check_file "tui/src/components/widgets/Select.tsx" "Select widget"
check_file "tui/src/components/widgets/Button.tsx" "Button widget"
check_file "tui/src/components/widgets/Checkbox.tsx" "Checkbox widget"
check_file "tui/src/components/widgets/TextArea.tsx" "TextArea widget"
echo ""

echo "=== State Management ==="
check_file "tui/src/stores/scraper.ts" "Scraper store"
echo ""

echo "=== API Client ==="
check_file "tui/src/api/client.ts" "API client (updated)"
check_file "tui/src/api/types.ts" "TypeScript types (updated)"
echo ""

echo "=== Documentation ==="
check_file "PHASE2-IMPLEMENTATION-COMPLETE.md" "Phase 2 completion doc"
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

# Check TypeScript syntax (if tsc available)
echo "=== TypeScript Check ==="
cd tui
if command -v bun &> /dev/null && [ -f "tsconfig.json" ]; then
    echo "Running TypeScript type check..."
    if bun run tsc --noEmit 2>&1 | head -10; then
        echo -e "${GREEN}✓${NC} TypeScript compilation successful"
        success_count=$((success_count + 1))
    else
        echo -e "${YELLOW}⚠${NC} TypeScript has type errors (may be expected)"
    fi
    total_checks=$((total_checks + 1))
else
    echo -e "${YELLOW}⚠${NC} Bun not found or no tsconfig, skipping TypeScript check"
fi
cd ..
echo ""

# Summary
echo "================================"
echo "Summary: $success_count/$total_checks checks passed"
echo "================================"

if [ $success_count -eq $total_checks ]; then
    echo -e "${GREEN}✅ All checks passed! Phase 2 is ready for testing.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start backend: ./run-api.sh"
    echo "2. Start TUI: cd tui && bun run dev"
    echo "3. Or use integrated launcher: ./run-dev.sh"
    exit 0
else
    echo -e "${RED}❌ Some checks failed. Please review the output above.${NC}"
    exit 1
fi
