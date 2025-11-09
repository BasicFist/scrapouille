# Quick Wins Sprint - Implementation Plan

**Sprint**: Quick Wins (Option A)  
**Duration**: 10-15 hours (1-2 days)  
**Approach**: Incremental enhancement without architecture redesign  
**Goal**: Immediate quality, reliability, and usability improvements

---

## 🎯 Sprint Objectives

1. ✅ **95%+ schema validation** pass rate (Pydantic)
2. ✅ **99%+ success rate** with retry logic
3. ✅ **30-50% accuracy** improvement (few-shot prompts)
4. ✅ **80% cost savings** for bulk scraping (markdown mode)
5. ✅ **Performance visibility** (execution metrics)

---

## 📋 Implementation Phases

### Phase 1: Retry Logic Foundation (2-3 hours)

**Why First**: Establishes reliability foundation for all other features

**Tasks**:
1. Update `requirements.txt`:
   ```txt
   tenacity>=8.2.0          # Retry logic
   pydantic>=2.0.0          # Schema validation (already in scrapegraphai)
   python-dotenv>=1.0.0     # Environment variables
   ```

2. Verify `nomic-embed-text` model download completed:
   ```bash
   curl -s http://localhost:11434/api/tags | grep nomic-embed-text
   ```

3. Create `scraper/utils.py`:
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential
   import logging
   
   logger = logging.getLogger(__name__)
   
   @retry(
       stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=2, max=10),
       reraise=True
   )
   def scrape_with_retry(scraper_func, *args, **kwargs):
       """Wrap scraping function with retry logic"""
       try:
           result = scraper_func(*args, **kwargs)
           if not result or result == {}:
               raise ValueError("Empty scraping result")
           return result
       except Exception as e:
           logger.error(f"Scraping attempt failed: {e}")
           raise
   ```

4. Update `scraper.py` to use retry wrapper:
   ```python
   from scraper.utils import scrape_with_retry
   
   # Wrap the run() call
   result = scrape_with_retry(smart_scraper_graph.run)
   ```

5. Add UI indicator for retry attempts in spinner message

**Testing**: Simulate failures, verify retry behavior, check logs

**Deliverable**: Retry logic working, retries visible to user

---

### Phase 2: Pydantic Schema Validation (2-3 hours)

**Why Second**: Ensures data quality after retry logic is established

**Tasks**:
1. Create `scraper/models.py`:
   ```python
   from pydantic import BaseModel, Field, validator
   from typing import Optional, List
   from datetime import datetime
   
   class ProductSchema(BaseModel):
       """E-commerce product schema"""
       name: str
       price: float = Field(gt=0)
       in_stock: bool
       rating: Optional[float] = Field(None, ge=0, le=5)
       
       @validator('name')
       def name_not_empty(cls, v):
           if not v or len(v.strip()) == 0:
               raise ValueError('Product name cannot be empty')
           return v.strip()
   
   class ArticleSchema(BaseModel):
       """News article schema"""
       title: str
       author: Optional[str]
       publication_date: Optional[str]
       content: str
       
       @validator('title')
       def title_not_empty(cls, v):
           if not v or len(v.strip()) == 0:
               raise ValueError('Article title cannot be empty')
           return v.strip()
   
   class JobListingSchema(BaseModel):
       """Job listing schema"""
       title: str
       company: str
       location: Optional[str]
       salary: Optional[str]
       requirements: Optional[List[str]]
   
   # Schema registry
   SCHEMAS = {
       "product": ProductSchema,
       "article": ArticleSchema,
       "job": JobListingSchema,
       "none": None  # No validation
   }
   ```

2. Add schema selector to UI (after model selection):
   ```python
   schema_choice = st.selectbox(
       "Validation Schema (Optional)",
       ["none", "product", "article", "job"],
       help="Validates extracted data against a schema"
   )
   ```

3. Integrate validation in scraper:
   ```python
   from scraper.models import SCHEMAS
   
   # After scraping
   if schema_choice != "none":
       schema = SCHEMAS[schema_choice]
       try:
           validated = schema(**result)
           st.success("✓ Data validation passed")
           result = validated.dict()
       except Exception as e:
           st.error(f"✗ Validation error: {str(e)}")
           st.info("Showing unvalidated data")
   ```

**Testing**: Test each schema type, verify errors are caught, check UI feedback

**Deliverable**: Schema validation working, clear error messages

---

### Phase 3: Execution Metrics (1-2 hours)

**Why Third**: Provides visibility into performance with quality features in place

**Tasks**:
1. Add metrics collection after scraping:
   ```python
   # After result = scraper.run()
   exec_info = smart_scraper_graph.get_execution_info()
   ```

2. Display metrics in Streamlit sidebar:
   ```python
   st.sidebar.markdown("### 📊 Execution Metrics")
   st.sidebar.metric("Tokens Used", exec_info.get('tokens_used', 'N/A'))
   st.sidebar.metric("Execution Time", f"{exec_info.get('execution_time', 0):.2f}s")
   st.sidebar.metric("Model", model_choice)
   
   # If retry happened
   if retry_count > 0:
       st.sidebar.metric("Retry Attempts", retry_count)
   ```

3. Store metrics in session state for history:
   ```python
   if 'metrics_history' not in st.session_state:
       st.session_state.metrics_history = []
   
   st.session_state.metrics_history.append({
       'timestamp': datetime.now(),
       'url': url,
       'tokens': exec_info.get('tokens_used'),
       'time': exec_info.get('execution_time'),
       'model': model_choice
   })
   ```

**Testing**: Verify metrics display correctly, check session persistence

**Deliverable**: Live metrics visible in sidebar

---

### Phase 4: Few-Shot Prompt Templates (2-3 hours)

**Why Fourth**: Builds on validated structure to improve accuracy

**Tasks**:
1. Create template library (add to `scraper.py` or new file):
   ```python
   TEMPLATES = {
       "Custom": "",  # Empty template
       "E-commerce Products": """
   Extract product information from the page. Return JSON with these exact fields:
   - name (string): Product name
   - price (float): Price in USD without $ symbol
   - in_stock (boolean): true if available, false if sold out
   - rating (float): Rating from 0 to 5, or null if not shown
   
   Examples:
   Input HTML: <div><h2>Laptop Pro 15</h2><span class="price">$1,299.99</span><span class="stock">In Stock</span></div>
   Output: {"name": "Laptop Pro 15", "price": 1299.99, "in_stock": true, "rating": null}
   
   Input HTML: <div><h2>Wireless Mouse</h2><span class="price">$29.99</span><span class="stock">Out of Stock</span><div class="rating">★★★★☆ 4.2</div></div>
   Output: {"name": "Wireless Mouse", "price": 29.99, "in_stock": false, "rating": 4.2}
   
   Now extract from the page.
   """,
       "News Articles": """
   Extract article information. Return JSON with:
   - title (string): Article headline
   - author (string or null): Author name
   - publication_date (string or null): When published
   - summary (string): First 2-3 sentences
   
   Examples:
   Input: <article><h1>AI Breakthrough in 2025</h1><span class="author">John Smith</span><time>2025-01-15</time><p>Researchers announced...</p></article>
   Output: {"title": "AI Breakthrough in 2025", "author": "John Smith", "publication_date": "2025-01-15", "summary": "Researchers announced..."}
   
   Now extract from the page.
   """,
       "Job Listings": """
   Extract job posting details. Return JSON with:
   - title (string): Job title
   - company (string): Company name
   - location (string or null): Job location
   - salary (string or null): Salary range
   - requirements (list of strings): Key requirements
   
   Examples:
   Input: <div class="job"><h2>Senior Python Developer</h2><span class="company">TechCorp</span><span class="location">San Francisco, CA</span><span class="salary">$120k-$160k</span><ul><li>5+ years Python</li><li>FastAPI experience</li></ul></div>
   Output: {"title": "Senior Python Developer", "company": "TechCorp", "location": "San Francisco, CA", "salary": "$120k-$160k", "requirements": ["5+ years Python", "FastAPI experience"]}
   
   Now extract from the page.
   """,
       "Research Papers": """
   Extract academic paper metadata. Return JSON with:
   - title (string): Paper title
   - authors (list of strings): Author names
   - abstract (string): Abstract text
   - publication_venue (string or null): Journal/conference name
   
   Now extract from the page.
   """,
       "Contact Information": """
   Extract contact details. Return JSON with:
   - name (string or null): Person/company name
   - email (string or null): Email address
   - phone (string or null): Phone number
   - address (string or null): Physical address
   
   Now extract from the page.
   """
   }
   ```

2. Add template selector in UI (before prompt input):
   ```python
   template_choice = st.selectbox(
       "Prompt Template",
       list(TEMPLATES.keys()),
       help="Quick-start templates with few-shot examples for better accuracy"
   )
   
   # Auto-populate prompt from template
   default_prompt = TEMPLATES[template_choice]
   
   user_prompt = st.text_area(
       "What do you want the AI agent to scrape from the website?",
       value=default_prompt,
       height=200,
       placeholder="e.g., Extract all product names and prices"
   )
   ```

3. Link templates to schemas:
   ```python
   TEMPLATE_SCHEMA_MAP = {
       "E-commerce Products": "product",
       "News Articles": "article",
       "Job Listings": "job",
       # Others default to "none"
   }
   
   # Auto-select matching schema
   if template_choice in TEMPLATE_SCHEMA_MAP:
       default_schema = TEMPLATE_SCHEMA_MAP[template_choice]
   else:
       default_schema = "none"
   ```

**Testing**: Test each template, verify few-shot examples improve accuracy

**Deliverable**: Template library working, auto-population functional

---

### Phase 5: Markdown Extraction Mode (3-4 hours)

**Why Last**: Alternative extraction path, builds on all previous features

**Tasks**:
1. Add markdown mode toggle in UI (in sidebar or above URL input):
   ```python
   st.sidebar.markdown("### ⚙️ Extraction Settings")
   
   markdown_mode = st.sidebar.checkbox(
       "Markdown Mode (Fast & Cheap)",
       value=False,
       help="Skip AI extraction, return raw markdown. 80% cost savings!"
   )
   
   if markdown_mode:
       st.sidebar.info("💡 Markdown mode: 2 credits vs 10 credits for AI mode")
   ```

2. Update graph_config dynamically:
   ```python
   graph_config = {
       "llm": {
           "model": f"ollama/{model_choice}",
           "temperature": 0,
           "format": "json",
           "base_url": "http://localhost:11434",
       },
       "embeddings": {
           "model": "ollama/nomic-embed-text",
           "base_url": "http://localhost:11434",
       },
       "verbose": True,
       "extraction_mode": not markdown_mode  # False for markdown, True for AI
   }
   ```

3. Handle dual output formats:
   ```python
   if markdown_mode:
       st.markdown("### 📄 Markdown Output")
       st.markdown(result)  # Display as markdown
       
       # Download button
       st.download_button(
           "Download Markdown",
           result,
           file_name=f"scraped_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
           mime="text/markdown"
       )
   else:
       st.success("Scraping complete!")
       st.json(result)  # Display as JSON
   ```

4. Disable schema validation in markdown mode:
   ```python
   if not markdown_mode and schema_choice != "none":
       # Validate...
   ```

**Testing**: Compare markdown vs AI mode, verify cost savings, test downloads

**Deliverable**: Markdown mode working, clear UI distinction

---

## 🧪 Testing Strategy

### For Each Phase:
1. **Unit Test**: Test feature in isolation
2. **Integration Test**: Test with previous features
3. **Real-World Test**: Use actual websites (news.ycombinator.com, amazon.com, etc.)

### Test Websites:
- **News**: https://news.ycombinator.com (simple structure)
- **E-commerce**: https://example-shop.com (if accessible)
- **Jobs**: https://news.ycombinator.com/jobs
- **Research**: https://arxiv.org

### Success Criteria:
- ✅ Retry logic handles failures gracefully
- ✅ Pydantic validation catches errors
- ✅ Metrics display accurately
- ✅ Templates improve extraction quality
- ✅ Markdown mode works and saves costs

---

## 📦 Dependencies Installation

```bash
cd /home/miko/LAB/ai/services/web-scraper

# Activate venv
source venv/bin/activate

# Install new dependencies
pip install tenacity>=8.2.0 pydantic>=2.0.0 python-dotenv>=1.0.0

# Verify installation
python -c "import tenacity, pydantic; print('✓ Dependencies ready')"
```

---

## 📂 File Structure (After Quick Wins)

```
ai/services/web-scraper/
├── scraper/
│   ├── __init__.py          # NEW: Package init
│   ├── utils.py             # NEW: Retry logic
│   └── models.py            # NEW: Pydantic schemas
├── scraper.py               # UPDATED: With all Quick Wins features
├── requirements.txt         # UPDATED: New dependencies
├── venv/                    # Virtual environment
├── README.md                # To be updated
├── QUICKSTART.md            # To be updated
├── ENHANCEMENT-WORKFLOW.md
├── OPTIMIZATION-PRIORITIES.md
├── WORKFLOW-SUMMARY.md
└── QUICK-WINS-IMPLEMENTATION-PLAN.md  # This file
```

---

## 🎯 Implementation Sequence

**Recommended Order** (based on dependency and value):

1. **Phase 1** (2-3hrs): Retry Logic
   - Foundation for reliability
   - Independent of other features
   - Immediate value

2. **Phase 2** (2-3hrs): Pydantic Validation
   - Ensures data quality
   - Works with retry logic
   - Foundation for templates

3. **Phase 3** (1-2hrs): Execution Metrics
   - Visibility into performance
   - Works with retry + validation
   - Quick implementation

4. **Phase 4** (2-3hrs): Few-Shot Templates
   - Builds on validation
   - Improves accuracy significantly
   - Links to schemas

5. **Phase 5** (3-4hrs): Markdown Mode
   - Alternative path
   - Independent feature
   - Cost optimization

**Total**: 10-15 hours

---

## 📊 Success Metrics

### Quality:
- ✅ Schema validation: 95%+ pass rate
- ✅ Extraction accuracy: 30-50% improvement with templates
- ✅ Data consistency: Zero corruption with Pydantic

### Reliability:
- ✅ Success rate: 99%+ with retry logic
- ✅ Error handling: Clear, actionable messages
- ✅ Graceful degradation: Fallback to unvalidated data

### Performance:
- ✅ Metrics visibility: Tokens, time, model displayed
- ✅ Cost savings: 80% reduction in markdown mode
- ✅ User experience: Clear feedback at each step

---

## 🚀 Deployment

After Quick Wins Sprint:

1. **Update Documentation**:
   ```bash
   # Update README.md with new features
   # Update QUICKSTART.md with examples
   # Update _infrastructure/docs/web-scraper-setup.md
   ```

2. **Test with Real Use Cases**:
   - Scrape 10+ different websites
   - Test all templates
   - Verify markdown mode savings

3. **Gather Feedback**:
   - Note pain points
   - Identify next priorities
   - Decide on Sprint 2 features

---

## 🔄 Next Steps (After Quick Wins)

**Option 1**: Continue with Phase 1 (Full Foundation)
- Architecture redesign
- Configuration management
- Professional structure

**Option 2**: Jump to high-value features
- Redis caching (4-5hrs, massive performance boost)
- Async batch processing (5-6hrs, 10x throughput)

**Option 3**: Polish and production
- Enhanced UI with tabs
- History management
- CLI interface

---

**Created**: 2025-11-09  
**Status**: Ready to implement  
**Next**: Start Phase 1 (Retry Logic)
