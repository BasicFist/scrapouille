#!/usr/bin/env python3
"""
Web Scraping AI Agent v2.0 - Quick Wins Sprint
Enhanced with: retry logic, Pydantic validation, templates, metrics, markdown mode
"""

import streamlit as st
from scrapegraphai.graphs import SmartScraperGraph
from datetime import datetime
import logging

# Import Quick Wins enhancements
from scraper.utils import scrape_with_retry
from scraper.models import SCHEMAS, validate_data
from scraper.templates import TEMPLATES, TEMPLATE_SCHEMA_MAP, list_templates

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize session state for metrics tracking
if 'metrics_history' not in st.session_state:
    st.session_state.metrics_history = []
if 'retry_count' not in st.session_state:
    st.session_state.retry_count = 0

# Page configuration
st.set_page_config(page_title="Web Scraper AI Agent v2.0", page_icon="🕵️‍♂️", layout="wide")

# Header
st.title("Web Scraping AI Agent v2.0 🕵️‍♂️")
st.caption("Enhanced with retry logic, validation, templates, and performance metrics")

# Sidebar configuration
st.sidebar.markdown("### ⚙️ Configuration")

# Model selection
model_choice = st.sidebar.selectbox(
    "LLM Model",
    ["llama3.1", "qwen2.5-coder", "deepseek-coder-v2"],
    help="Choose the local Ollama model"
)

# Markdown mode toggle
markdown_mode = st.sidebar.checkbox(
    "Markdown Mode (Fast & Cheap)",
    value=False,
    help="Skip AI extraction, return raw markdown. 80% cost savings!"
)

if markdown_mode:
    st.sidebar.info("💡 Markdown mode: ~2 credits vs ~10 credits for AI mode")

# Schema validation selector
schema_choice = st.sidebar.selectbox(
    "Validation Schema",
    ["none", "product", "article", "job", "research_paper", "contact"],
    help="Validates extracted data against a schema"
)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    # Template selector
    st.markdown("### 📝 Prompt Template")
    template_choice = st.selectbox(
        "Select Template",
        list_templates(),
        help="Quick-start templates with few-shot examples for better accuracy"
    )

    # Auto-populate prompt from template
    default_prompt = TEMPLATES[template_choice]

    # Auto-select matching schema
    if template_choice in TEMPLATE_SCHEMA_MAP and schema_choice == "none":
        suggested_schema = TEMPLATE_SCHEMA_MAP[template_choice]
        st.info(f"💡 Tip: Consider using '{suggested_schema}' schema for this template")

    # User prompt
    user_prompt = st.text_area(
        "Scraping Prompt",
        value=default_prompt,
        height=200,
        placeholder="e.g., Extract all product names and prices",
        help="Describe what you want to extract. Templates include few-shot examples."
    )

    # URL input
    url = st.text_input(
        "Website URL",
        placeholder="https://example.com",
        help="Enter the full URL of the website to scrape"
    )

with col2:
    # Metrics display
    st.markdown("### 📊 Session Metrics")
    if st.session_state.metrics_history:
        latest = st.session_state.metrics_history[-1]
        st.metric("Last Scrape Time", f"{latest.get('time', 0):.2f}s")
        st.metric("Model Used", latest.get('model', 'N/A'))
        if latest.get('retry_count', 0) > 0:
            st.metric("Retry Attempts", latest['retry_count'], delta="retried")
        st.metric("Total Scrapes", len(st.session_state.metrics_history))
    else:
        st.info("No scraping history yet")

# Scrape button
if st.button("🚀 Scrape Website", type="primary", use_container_width=True):
    if not url or not user_prompt:
        st.error("❌ Please provide both URL and prompt")
    else:
        # Build graph configuration
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
        }

        # Add markdown mode if enabled
        if markdown_mode:
            graph_config["extraction_mode"] = False

        # Start scraping
        start_time = datetime.now()

        with st.spinner(f"Scraping with {model_choice}... (retry enabled)"):
            try:
                # Create SmartScraperGraph
                smart_scraper_graph = SmartScraperGraph(
                    prompt=user_prompt,
                    source=url,
                    config=graph_config
                )

                # Scrape with retry logic
                result = scrape_with_retry(smart_scraper_graph.run)

                # Calculate execution time
                execution_time = (datetime.now() - start_time).total_seconds()

                # Get execution info (if available)
                try:
                    exec_info = smart_scraper_graph.get_execution_info()
                except:
                    exec_info = {}

                # Store metrics
                st.session_state.metrics_history.append({
                    'timestamp': datetime.now(),
                    'url': url,
                    'time': execution_time,
                    'model': model_choice,
                    'retry_count': st.session_state.retry_count,
                    'tokens': exec_info.get('total_tokens', 'N/A'),
                })

                # Reset retry count
                st.session_state.retry_count = 0

                # Display based on mode
                if markdown_mode:
                    st.success("✅ Markdown extraction complete!")
                    st.markdown("### 📄 Markdown Output")
                    st.markdown(result)

                    # Download button
                    st.download_button(
                        "⬇️ Download Markdown",
                        result if isinstance(result, str) else str(result),
                        file_name=f"scraped_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown"
                    )

                else:
                    st.success("✅ Scraping complete!")

                    # Validate if schema selected
                    if schema_choice != "none":
                        st.markdown("### 🔍 Schema Validation")
                        valid, validated_data, error = validate_data(result, schema_choice)

                        if valid:
                            st.success("✓ Data validation passed")
                            result = validated_data
                        else:
                            st.error(f"✗ Validation error: {error}")
                            st.info("Showing unvalidated data below")

                    # Display JSON result
                    st.markdown("### 📦 Extracted Data")
                    st.json(result)

                    # Download JSON button
                    import json
                    st.download_button(
                        "⬇️ Download JSON",
                        json.dumps(result, indent=2),
                        file_name=f"scraped_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )

                # Display execution info
                if exec_info:
                    with st.expander("📊 Detailed Execution Metrics"):
                        st.json(exec_info)

            except Exception as e:
                st.error(f"❌ Error during scraping: {str(e)}")
                st.info("💡 Make sure Ollama is running and models are available")
                logger.error(f"Scraping failed: {e}", exc_info=True)

# Footer
st.markdown("---")
st.markdown(
    """
    **v2.0 Quick Wins Features:**
    - ✅ Retry logic with exponential backoff (3 attempts)
    - ✅ Pydantic schema validation (5 schemas)
    - ✅ Few-shot prompt templates (7 templates)
    - ✅ Markdown extraction mode (80% cost savings)
    - ✅ Real-time execution metrics
    """
)
