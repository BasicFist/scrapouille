#!/bin/bash
# Colorful Theme Verification Script
# Checks that all theme files and updates are in place

set -e

echo "🎨 Verifying Colorful Theme Implementation..."
echo ""

# Color codes for script output
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
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

check_import() {
    local file=$1
    local import=$2
    local description=$3
    total_checks=$((total_checks + 1))

    if grep -q "$import" "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $description"
        success_count=$((success_count + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $description (MISSING)"
        return 1
    fi
}

echo "=== Theme Configuration ==="
check_file "tui/src/theme.ts" "Theme configuration file"
echo ""

echo "=== Theme Imports ==="
check_import "tui/src/components/StatusBar.tsx" "import theme from '../theme'" "StatusBar imports theme"
check_import "tui/src/components/App.tsx" "import theme from '../theme'" "App imports theme"
check_import "tui/src/components/widgets/Button.tsx" "import theme from '../../theme'" "Button imports theme"
check_import "tui/src/components/widgets/Select.tsx" "import theme from '../../theme'" "Select imports theme"
check_import "tui/src/components/widgets/Input.tsx" "import theme from '../../theme'" "Input imports theme"
check_import "tui/src/components/widgets/TextArea.tsx" "import theme from '../../theme'" "TextArea imports theme"
check_import "tui/src/components/widgets/Checkbox.tsx" "import theme from '../../theme'" "Checkbox imports theme"
echo ""

echo "=== Theme Color Definitions ==="
if grep -q "primary: '#00D9FF'" "tui/src/theme.ts" 2>/dev/null; then
    echo -e "${CYAN}✓${NC} Primary color (Cyan) defined"
    success_count=$((success_count + 1))
else
    echo -e "${RED}✗${NC} Primary color missing"
fi
total_checks=$((total_checks + 1))

if grep -q "secondary: '#7C3AED'" "tui/src/theme.ts" 2>/dev/null; then
    echo -e "${PURPLE}✓${NC} Secondary color (Purple) defined"
    success_count=$((success_count + 1))
else
    echo -e "${RED}✗${NC} Secondary color missing"
fi
total_checks=$((total_checks + 1))

if grep -q "success: '#10B981'" "tui/src/theme.ts" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Success color (Green) defined"
    success_count=$((success_count + 1))
else
    echo -e "${RED}✗${NC} Success color missing"
fi
total_checks=$((total_checks + 1))
echo ""

echo "=== Gradient Definitions ==="
if grep -q "gradients:" "tui/src/theme.ts" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Gradients object defined"
    success_count=$((success_count + 1))
else
    echo -e "${RED}✗${NC} Gradients object missing"
fi
total_checks=$((total_checks + 1))

if grep -q "rainbow:" "tui/src/theme.ts" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Rainbow gradient defined"
    success_count=$((success_count + 1))
else
    echo -e "${RED}✗${NC} Rainbow gradient missing"
fi
total_checks=$((total_checks + 1))
echo ""

echo "=== Component Updates ==="
if grep -q "background: theme.gradients.rainbow" "tui/src/components/App.tsx" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Tab bar uses rainbow gradient"
    success_count=$((success_count + 1))
else
    echo -e "${RED}✗${NC} Tab bar rainbow gradient missing"
fi
total_checks=$((total_checks + 1))

if grep -q "backgroundColor: ollamaConnected() ? theme.success : theme.error" "tui/src/components/StatusBar.tsx" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} StatusBar uses colorful badges"
    success_count=$((success_count + 1))
else
    echo -e "${RED}✗${NC} StatusBar colorful badges missing"
fi
total_checks=$((total_checks + 1))

if grep -q "background: theme.gradients.primary" "tui/src/components/widgets/Button.tsx" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Button uses gradient backgrounds"
    success_count=$((success_count + 1))
else
    echo -e "${RED}✗${NC} Button gradient backgrounds missing"
fi
total_checks=$((total_checks + 1))
echo ""

echo "=== Documentation ==="
check_file "COLORFUL-THEME-BEAUTIFICATION.md" "Beautification documentation"
echo ""

# Summary
echo "======================================"
echo "Summary: $success_count/$total_checks checks passed"
echo "======================================"

if [ $success_count -eq $total_checks ]; then
    echo -e "${CYAN}✅ All checks passed! Colorful theme is ready!${NC}"
    echo ""
    echo "Theme Features:"
    echo -e "${CYAN}  • 8+ vibrant colors (Cyan, Purple, Pink, Green, Amber, Red, Blue, Orange)${NC}"
    echo -e "${PURPLE}  • 7 beautiful gradients${NC}"
    echo -e "${GREEN}  • Glowing shadow effects${NC}"
    echo -e "${YELLOW}  • Colorful badges and icons${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start TUI: cd tui && bun run dev"
    echo "2. Enjoy the beautiful, vibrant interface! 🎨✨"
    echo "3. See COLORFUL-THEME-BEAUTIFICATION.md for full details"
    exit 0
else
    echo -e "${RED}❌ Some checks failed. Please review the output above.${NC}"
    exit 1
fi
