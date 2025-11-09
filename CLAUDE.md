# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: Scrapouille v2.0

AI-powered web scraper using local LLMs (Ollama) + scrapegraphai + Streamlit UI.

**Status**: Production-ready v2.0 with Quick Wins enhancements

---

## Critical Environment Requirement

**⚠️ LANGCHAIN COMPATIBILITY ISSUE**

This project requires **langchain 0.3.x** (NOT 1.0+) due to scrapegraphai dependency issue.

**GitHub Issue**: https://github.com/ScrapeGraphAI/Scrapegraph-ai/issues/1017 (OPEN)

**Setup sequence** (MUST follow this order):

```bash
# 1. Create isolated environment
python -m venv venv-isolated
source venv-isolated/bin/activate

# 2. Install scrapegraphai first
pip install scrapegraphai>=1.64.0

# 3. CRITICAL: Downgrade langchain to 0.3.x
pip freeze | grep langchain | xargs pip uninstall -y
pip install 'langchain==0.3.15' 'langchain-community==0.3.13'
pip install 'langchain-ollama==0.2.2' 'langchain-openai==0.2.13' \
            'langchain-aws==0.2.9' 'langchain-mistralai==0.2.4'

# 4. Install remaining dependencies
pip install -r requirements.txt

# 5. Install Playwright browsers
playwright install chromium
```

**Do NOT**:
- Use standard venv (venv/)
- Install langchain 1.0+
- Skip the downgrade step

See `LANGCHAIN-COMPATIBILITY-STATUS.md` for full details and monitoring instructions.

---

## Development Commands

### Run Application
```bash
source venv-isolated/bin/activate
streamlit run scraper.py
# Opens at http://localhost:8501
```

### Testing
```bash
# Quick integration test (5-10s, requires Ollama running)
python test_integration_quick.py

# Module tests (fast, no LLM calls)
python test_quick_wins_simple.py

# Full integration tests (slow, 3-5min, LLM processing)
python test_quick_wins.py
```

### Prerequisites
```bash
# Ollama must be running with models
ollama serve
ollama pull qwen2.5-coder:7b  # Recommended model
```

---

## Architecture

### Core Components

**scraper.py** - Streamlit UI (entry point)
- Model selection (Ollama local + cloud providers)
- Template system integration
- Markdown vs AI mode toggle
- Session history with metrics
- Uses `SmartScraperGraph` from scrapegraphai

**scraper/utils.py** - Retry Logic
- `scrape_with_retry()`: Wraps any scraping function with exponential backoff
- Uses `tenacity` library
- 3 attempts: 2s → 4s → 8s delays
- Handles ConnectionError, TimeoutError, ValueError

**scraper/models.py** - Pydantic Validation Schemas
- 5 pre-built schemas: Product, Article, Job, Research Paper, Contact
- Field validation with type checking
- `validate_data()`: Validates extracted data against schema
- Returns (bool, validated_data, error_msg)

**scraper/templates.py** - Few-Shot Prompt Templates
- 7 templates with 2-3 examples each
- `TEMPLATE_SCHEMA_MAP`: Links templates to recommended schemas
- `get_template()`: Returns template by name
- `get_recommended_schema()`: Suggests schema based on template

### Data Flow

1. **User Input** → URL + (Template OR Custom Prompt) + Optional Schema
2. **Mode Selection** → AI Extraction OR Markdown Conversion
3. **AI Mode**:
   - Build graph_config with LLM settings
   - Create SmartScraperGraph instance
   - Call `scrape_with_retry(graph.run, url)`
   - Validate with Pydantic if schema selected
   - Track metrics (time, tokens, retries)
4. **Markdown Mode**:
   - Direct markdown conversion
   - No LLM processing (80% cost savings)
5. **Display** → JSON result + execution metrics + session history

### Key Design Patterns

**Retry Pattern** (`scraper/utils.py`):
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def scrape_with_retry(scraper_func, *args, **kwargs):
    # Validates non-empty result
    # Re-raises on final failure
```

**Validation Pattern** (`scraper/models.py`):
```python
def validate_data(data: dict, schema_name: str) -> tuple[bool, Any, str]:
    # Returns (success, validated_data, error_message)
    schema_class = SCHEMAS[schema_name]
    validated = schema_class(**data)
```

**Template System** (`scraper/templates.py`):
```python
TEMPLATES = {
    "E-commerce": "Extract products with examples...",
    # ... 6 more templates
}
TEMPLATE_SCHEMA_MAP = {
    "E-commerce": "Product",
    # ... mappings
}
```

---

## Adding Features

### New Validation Schema

1. Add Pydantic model to `scraper/models.py`:
```python
class MySchema(BaseModel):
    field: str
    # Add validators with @field_validator
```

2. Register in `SCHEMAS` dict:
```python
SCHEMAS = {
    "MySchema": MySchema,
    # ...
}
```

3. Update UI dropdown in `scraper.py` (auto-populated from SCHEMAS keys)

### New Template

1. Add to `TEMPLATES` dict in `scraper/templates.py`:
```python
TEMPLATES = {
    "My Use Case": """Extract X, Y, Z.
Examples:
1. Input: ... → Output: ...
2. Input: ... → Output: ...
""",
}
```

2. Link to schema in `TEMPLATE_SCHEMA_MAP`:
```python
TEMPLATE_SCHEMA_MAP = {
    "My Use Case": "MySchema",
}
```

### New LLM Provider

Update `graph_config` dict in `scraper.py`:
```python
graph_config = {
    "llm": {
        "provider": "my_provider",
        "api_key": "...",
        "model": "model_name"
    }
}
```

Supported: ollama (local), openai, anthropic, groq, mistral, bedrock

---

## Testing Notes

**Integration tests require**:
- Ollama running (`ollama serve`)
- Model available (`ollama pull qwen2.5-coder:7b`)

**Test architecture**:
- `test_quick_wins_simple.py`: Unit tests (no LLM)
- `test_integration_quick.py`: Fast integration (markdown mode)
- `test_quick_wins.py`: Full integration (all features, slow)

**Mock testing**: Not implemented - uses real Ollama for integration tests

---

## Monitoring Upstream Fix

**Check scrapegraphai updates**:
```bash
pip index versions scrapegraphai  # Current: 1.64.0
```

**Monitor GitHub Issue #1017**:
- Issue closed = likely fixed
- Check release notes for "langchain 1.0" mention

**Test new version**:
```bash
python -m venv venv-test
source venv-test/bin/activate
pip install scrapegraphai  # Latest
python -c "from scrapegraphai.graphs import SmartScraperGraph; print('✅ Fixed!')"
```

When fixed: Delete `venv-isolated`, use standard venv with langchain 1.0+

---

## Common Issues

**Import error "No module named 'langchain.prompts'"**
→ langchain 1.0+ detected, follow downgrade steps above

**Playwright browsers not installed**
→ `playwright install chromium`

**Ollama connection refused**
→ `ollama serve` in separate terminal

**Empty scraping results**
→ Retry logic handles this (3 attempts with backoff)

**Streamlit port already in use**
→ `streamlit run scraper.py --server.port 8502`

---

## Documentation

- `README.md`: Full user documentation
- `QUICKSTART.md`: Quick reference
- `LANGCHAIN-COMPATIBILITY-STATUS.md`: Dependency issue details
- `ISOLATED-VENV-SETUP.md`: Environment setup guide
- `TESTING-SUMMARY.md`: Test results and coverage
- `QUICK-WINS-IMPLEMENTATION-PLAN.md`: v2.0 feature specifications

---

## Version Context

- **Python**: 3.10+
- **scrapegraphai**: 1.64.0
- **langchain**: 0.3.15 (pinned, NOT 1.0+)
- **streamlit**: 1.28.0+
- **playwright**: 1.40.0+
- **pydantic**: 2.0+
- **tenacity**: 8.2.0+
