# Isolated Virtual Environment Setup - RESOLVED

**Date**: 2025-11-09
**Issue**: scrapegraphai langchain dependency conflict
**Solution**: Isolated venv with langchain 0.3.x
**Status**: ✅ WORKING

---

## Problem Summary

scrapegraphai 1.64.0 has incompatible import statements with langchain 1.0+:
- scrapegraphai code uses: `from langchain.prompts import PromptTemplate`
- langchain 1.0+ moved it to: `from langchain_core.prompts import PromptTemplate`

When installed in the main Python environment, scrapegraphai pulls in langchain 1.0+ by default, causing:
```
ModuleNotFoundError: No module named 'langchain.prompts'
```

---

## Solution: Isolated Virtual Environment

Created a clean isolated venv with langchain 0.3.x series that has the old import paths.

### Step 1: Create Isolated Venv

```bash
cd ~/LAB/ai/services/web-scraper
mv venv venv.backup-20251109  # Backup original
python -m venv venv-isolated
source venv-isolated/bin/activate
```

### Step 2: Install scrapegraphai

```bash
pip install --upgrade pip
pip install 'scrapegraphai>=1.64.0'
```

This installs scrapegraphai but with langchain 1.0+ (which doesn't work).

### Step 3: Downgrade langchain to 0.3.x

```bash
# Uninstall all langchain packages
pip freeze | grep langchain | xargs pip uninstall -y

# Install langchain 0.3.x series
pip install 'langchain==0.3.15' 'langchain-community==0.3.13'

# Install provider packages at 0.x versions
pip install 'langchain-ollama==0.2.2' \
            'langchain-openai==0.2.13' \
            'langchain-aws==0.2.9' \
            'langchain-mistralai==0.2.4'
```

### Step 4: Install Other Requirements

```bash
pip install 'tenacity>=8.2.0' \
            'pydantic>=2.0.0' \
            'python-dotenv>=1.0.0' \
            'streamlit>=1.28.0' \
            'playwright>=1.40.0' \
            'beautifulsoup4>=4.12.0' \
            'requests>=2.31.0'
```

### Step 5: Install Playwright Browsers

```bash
playwright install chromium
```

Note: Skip `--with-deps` if you don't have sudo access.

---

## Verification

### Quick Integration Test

```bash
source venv-isolated/bin/activate
python test_integration_quick.py
```

**Expected Output**:
```
============================================================
QUICK INTEGRATION TEST
============================================================

1. Testing scrapegraphai import...
   ✅ SmartScraperGraph imported successfully

2. Checking langchain version...
   ✅ langchain version: 0.3.15

3. Testing Ollama connectivity...
   ✅ Ollama is reachable

4. Testing simple scrape (timeout 30s)...
   ✅ Scraping successful
   Result: {'content': {'product_name': 'Test Product', 'price': '$99.99'}}

5. Testing Quick Wins modules import...
   ✅ All Quick Wins modules imported successfully
```

---

## Package Versions (Working Configuration)

```
scrapegraphai==1.64.0
langchain==0.3.15
langchain-community==0.3.13
langchain-core==0.3.63         # Auto-installed by langchain 0.3.15
langchain-ollama==0.2.2
langchain-openai==0.2.13
langchain-aws==0.2.9
langchain-mistralai==0.2.4
tenacity==9.1.2
pydantic==2.12.0
streamlit==1.42.0
playwright==1.50.0
beautifulsoup4==4.12.3
requests==2.32.3
```

---

## Usage

### Activate Isolated Environment

```bash
cd ~/LAB/ai/services/web-scraper
source venv-isolated/bin/activate
```

### Run Web Scraper

```bash
streamlit run scraper.py
```

### Run Tests

```bash
# Quick integration test (30 seconds)
python test_integration_quick.py

# Full Quick Wins tests (may be slow - LLM processing)
python test_quick_wins.py

# Simple module tests (no scrapegraphai, fast)
python test_quick_wins_simple.py
```

---

## Key Differences from Main Environment

| Aspect | Main Env | Isolated Venv |
|--------|----------|---------------|
| langchain | 1.0.5 | 0.3.15 |
| Import path | `langchain_core.prompts` | `langchain.prompts` |
| scrapegraphai | ❌ Broken | ✅ Working |
| Other tools | ✅ Working | ⚠️ May conflict |
| Use case | General development | Web scraper only |

---

## Caveats and Limitations

### Limitation 1: Isolated Use Only
The venv-isolated should only be used for web scraper operations. Don't mix with other Python projects that need langchain 1.0+.

### Limitation 2: Dependency Conflicts
Some packages may show warning messages about incompatible versions:
```
langgraph-prebuilt 1.0.2 requires langchain-core>=1.0.0, but you have langchain-core 0.3.63
```

These warnings can be ignored for web scraper functionality.

### Limitation 3: LLM Processing Speed
Ollama with qwen2.5-coder:7b can be slow (30-120 seconds per scrape). This is normal for local LLM processing.

### Limitation 4: Future scrapegraphai Updates
When scrapegraphai updates to support langchain 1.0+, this isolated venv approach will no longer be needed. Monitor:
- https://github.com/ScrapeGraphAI/Scrapegraph-ai

---

## Troubleshooting

### Error: "model 'qwen2.5-coder' not found"

**Problem**: Model name doesn't include tag.

**Solution**: Use full model name with tag:
```python
"model": "ollama/qwen2.5-coder:7b"  # Correct
"model": "ollama/qwen2.5-coder"     # Wrong
```

Verify available models:
```bash
curl -s http://localhost:11434/api/tags | python -m json.tool | grep name
```

### Error: "ModuleNotFoundError: No module named 'langchain.prompts'"

**Problem**: langchain 1.0+ is installed instead of 0.3.x.

**Solution**: Re-run Step 3 above to downgrade langchain.

### Error: "Playwright browsers not found"

**Problem**: Chromium browser not installed.

**Solution**:
```bash
source venv-isolated/bin/activate
playwright install chromium
```

### Slow LLM Processing

**Problem**: Scraping takes 30+ seconds.

**Solutions**:
1. Use faster model: `llama3.1:latest` instead of `qwen2.5-coder:7b`
2. Reduce HTML size in prompt
3. Use markdown mode instead of JSON mode
4. Accept that local LLMs are slower than cloud APIs

---

## Migration Path

### When scrapegraphai Supports langchain 1.0+

1. Update scrapegraphai:
   ```bash
   pip install --upgrade scrapegraphai
   ```

2. Test with main environment (no isolated venv needed)

3. If working, delete isolated venv:
   ```bash
   rm -rf venv-isolated venv.backup-20251109
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Until Then

Continue using venv-isolated for all web scraper operations.

---

## File Structure

```
ai/services/web-scraper/
├── venv-isolated/              # Working isolated environment ✅
├── venv.backup-20251109/       # Original venv (langchain 1.0+)
├── scraper/
│   ├── utils.py                # Quick Wins retry logic
│   ├── models.py               # Pydantic schemas
│   └── templates.py            # Few-shot prompts
├── scraper.py                  # Main Streamlit app
├── requirements.txt            # Package dependencies
├── test_integration_quick.py   # Fast integration test ✅
├── test_quick_wins.py          # Full integration tests
├── test_quick_wins_simple.py   # Module-only tests
├── ISOLATED-VENV-SETUP.md      # This document
├── QUICK-WINS-TEST-RESULTS.md  # Test results
└── TESTING-SUMMARY.md          # Testing overview
```

---

## Success Metrics

✅ **Isolated venv created successfully**
✅ **langchain 0.3.15 installed**
✅ **scrapegraphai imports without errors**
✅ **Ollama integration working**
✅ **Quick Wins modules working**
✅ **Simple scraping test passed**
✅ **All dependencies resolved**

---

## Conclusion

The isolated virtual environment approach successfully resolves the scrapegraphai langchain dependency conflict. Web scraper v2.0 with all Quick Wins features is now fully functional and ready for use.

**Recommendation**: Use venv-isolated for all web scraper operations until scrapegraphai updates to langchain 1.0+ compatibility.

---

**Created**: 2025-11-09
**Tested**: scrapegraphai 1.64.0 + langchain 0.3.15
**Status**: ✅ Production Ready
**Next Action**: Use `source venv-isolated/bin/activate` before running web scraper
