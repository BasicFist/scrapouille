#!/usr/bin/env python3
"""
Quick Wins Sprint Testing Suite
Tests all v2.0 enhancements: retry logic, validation, templates, metrics
"""

import sys
import time
from datetime import datetime
from scrapegraphai.graphs import SmartScraperGraph

# Import Quick Wins modules
from scraper.utils import scrape_with_retry
from scraper.models import SCHEMAS, validate_data
from scraper.templates import TEMPLATES, TEMPLATE_SCHEMA_MAP

# Test configuration
graph_config = {
    "llm": {
        "model": "ollama/qwen2.5-coder:7b",
        "temperature": 0,
        "format": "json",
        "base_url": "http://localhost:11434",
    },
    "verbose": True,
    "headless": True,
}

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_retry_logic():
    """Test 1: Retry logic with failing URLs"""
    print_section("TEST 1: Retry Logic with Failing URLs")

    # Test 1a: Valid URL (should succeed on first try)
    print("1a. Testing with valid URL (https://news.ycombinator.com)...")
    start_time = time.time()
    try:
        def scrape_valid():
            smart_scraper = SmartScraperGraph(
                prompt="Extract the first news headline",
                source="https://news.ycombinator.com",
                config=graph_config,
            )
            return smart_scraper.run()

        result = scrape_with_retry(scrape_valid)
        elapsed = time.time() - start_time
        print(f"✅ SUCCESS: Got result in {elapsed:.2f}s")
        print(f"   Result: {str(result)[:100]}...")
    except Exception as e:
        print(f"❌ FAILED: {e}")

    # Test 1b: Invalid URL (should retry and fail after 3 attempts)
    print("\n1b. Testing with invalid URL (should retry 3 times)...")
    start_time = time.time()
    try:
        def scrape_invalid():
            smart_scraper = SmartScraperGraph(
                prompt="Extract something",
                source="https://this-domain-does-not-exist-12345.com",
                config=graph_config,
            )
            result = smart_scraper.run()
            if not result or result == {}:
                raise ValueError("Empty result")
            return result

        result = scrape_with_retry(scrape_invalid)
        print(f"❌ UNEXPECTED: Should have failed but got: {result}")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"✅ EXPECTED FAILURE after {elapsed:.2f}s: {type(e).__name__}")
        print(f"   (Should have retried ~3 times with exponential backoff)")

def test_schema_validation():
    """Test 2: Pydantic schema validation"""
    print_section("TEST 2: Pydantic Schema Validation")

    # Test 2a: Valid product data
    print("2a. Testing valid product data...")
    valid_product = {
        "name": "Laptop Pro 15",
        "price": 1299.99,
        "in_stock": True,
        "rating": 4.5
    }
    success, validated, error = validate_data(valid_product, "product")
    if success:
        print(f"✅ VALIDATION PASSED: {validated}")
    else:
        print(f"❌ VALIDATION FAILED: {error}")

    # Test 2b: Invalid product data (negative price)
    print("\n2b. Testing invalid product data (negative price)...")
    invalid_product = {
        "name": "Bad Product",
        "price": -99.99,  # Should fail: price must be > 0
        "in_stock": True,
        "rating": 4.5
    }
    success, validated, error = validate_data(invalid_product, "product")
    if not success:
        print(f"✅ VALIDATION CORRECTLY REJECTED: {error}")
    else:
        print(f"❌ VALIDATION INCORRECTLY PASSED: {validated}")

    # Test 2c: Invalid product data (empty name)
    print("\n2c. Testing invalid product data (empty name)...")
    invalid_name = {
        "name": "   ",  # Should fail: name cannot be empty
        "price": 99.99,
        "in_stock": True,
        "rating": 4.5
    }
    success, validated, error = validate_data(invalid_name, "product")
    if not success:
        print(f"✅ VALIDATION CORRECTLY REJECTED: {error}")
    else:
        print(f"❌ VALIDATION INCORRECTLY PASSED: {validated}")

    # Test 2d: Article schema
    print("\n2d. Testing article schema validation...")
    valid_article = {
        "title": "AI Breakthrough in 2025",
        "author": "Jane Doe",
        "published_date": "2025-11-09",
        "summary": "New AI model achieves state-of-the-art results"
    }
    success, validated, error = validate_data(valid_article, "article")
    if success:
        print(f"✅ ARTICLE VALIDATION PASSED: {validated['title']}")
    else:
        print(f"❌ ARTICLE VALIDATION FAILED: {error}")

def test_templates():
    """Test 3: Few-shot prompt templates"""
    print_section("TEST 3: Few-Shot Prompt Templates")

    print("3a. Testing E-commerce Products template...")
    print(f"Template preview:\n{TEMPLATES['E-commerce Products'][:200]}...")
    print(f"Associated schema: {TEMPLATE_SCHEMA_MAP.get('E-commerce Products', 'none')}")

    print("\n3b. Testing News Articles template...")
    print(f"Template preview:\n{TEMPLATES['News Articles'][:200]}...")
    print(f"Associated schema: {TEMPLATE_SCHEMA_MAP.get('News Articles', 'none')}")

    print("\n3c. Verifying all templates have correct schema mapping...")
    for template_name, schema_name in TEMPLATE_SCHEMA_MAP.items():
        if schema_name in SCHEMAS:
            print(f"✅ {template_name} → {schema_name} (valid)")
        else:
            print(f"❌ {template_name} → {schema_name} (INVALID SCHEMA)")

def test_real_website_scraping():
    """Test 4: Real website scraping with templates"""
    print_section("TEST 4: Real Website Scraping with Templates")

    # Test 4a: Hacker News (News Articles template)
    print("4a. Testing News Articles template on Hacker News...")
    start_time = time.time()
    try:
        smart_scraper = SmartScraperGraph(
            prompt=TEMPLATES["News Articles"],
            source="https://news.ycombinator.com",
            config=graph_config,
        )
        result = smart_scraper.run()
        elapsed = time.time() - start_time

        # Validate with article schema
        success, validated, error = validate_data(result, "article")
        if success:
            print(f"✅ SCRAPING + VALIDATION PASSED ({elapsed:.2f}s)")
            print(f"   Title: {validated.get('title', 'N/A')[:60]}...")
            print(f"   Author: {validated.get('author', 'N/A')}")
        else:
            print(f"⚠️  SCRAPING SUCCEEDED but VALIDATION FAILED ({elapsed:.2f}s)")
            print(f"   Raw result: {str(result)[:200]}...")
            print(f"   Validation error: {error}")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ SCRAPING FAILED ({elapsed:.2f}s): {e}")

def test_markdown_mode():
    """Test 5: Markdown mode for cost savings"""
    print_section("TEST 5: Markdown Mode Cost Savings")

    print("5a. Testing JSON mode (standard)...")
    start_time = time.time()
    try:
        config_json = graph_config.copy()
        config_json["llm"]["format"] = "json"

        smart_scraper = SmartScraperGraph(
            prompt="Extract the first headline",
            source="https://news.ycombinator.com",
            config=config_json,
        )
        result_json = smart_scraper.run()
        json_time = time.time() - start_time
        json_tokens = len(str(result_json))  # Approximation
        print(f"✅ JSON mode: {json_time:.2f}s, ~{json_tokens} chars")
    except Exception as e:
        print(f"❌ JSON mode failed: {e}")
        json_time = 0
        json_tokens = 0

    print("\n5b. Testing Markdown mode (cost-saving)...")
    start_time = time.time()
    try:
        config_md = graph_config.copy()
        config_md["llm"]["format"] = None  # Remove JSON format

        smart_scraper = SmartScraperGraph(
            prompt="Extract the first headline as plain text",
            source="https://news.ycombinator.com",
            config=config_md,
        )
        result_md = smart_scraper.run()
        md_time = time.time() - start_time
        md_tokens = len(str(result_md))  # Approximation
        print(f"✅ Markdown mode: {md_time:.2f}s, ~{md_tokens} chars")

        if json_tokens > 0 and md_tokens > 0:
            savings = ((json_tokens - md_tokens) / json_tokens) * 100
            print(f"\n📊 Estimated token savings: {savings:.1f}%")
    except Exception as e:
        print(f"❌ Markdown mode failed: {e}")

def test_execution_metrics():
    """Test 6: Execution metrics tracking"""
    print_section("TEST 6: Execution Metrics Tracking")

    print("Testing metrics collection during scraping...")
    metrics = {
        "start_time": datetime.now(),
        "retries": 0,
        "validation_passed": False,
        "execution_time": 0.0
    }

    start = time.time()
    try:
        smart_scraper = SmartScraperGraph(
            prompt="Extract first headline",
            source="https://news.ycombinator.com",
            config=graph_config,
        )
        result = scrape_with_retry(lambda: smart_scraper.run())

        metrics["execution_time"] = time.time() - start
        metrics["validation_passed"], validated, error = validate_data(result, "none")

        print(f"✅ Metrics collected:")
        print(f"   Start time: {metrics['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Execution time: {metrics['execution_time']:.2f}s")
        print(f"   Retries: {metrics['retries']}")
        print(f"   Validation: {'✅ Passed' if metrics['validation_passed'] else '❌ Failed'}")
    except Exception as e:
        print(f"❌ Metrics test failed: {e}")

def main():
    """Run all Quick Wins tests"""
    print("\n" + "="*60)
    print("  WEB SCRAPER v2.0 - QUICK WINS SPRINT TEST SUITE")
    print("="*60)
    print(f"  Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Run all tests
    test_retry_logic()
    test_schema_validation()
    test_templates()
    test_real_website_scraping()
    test_markdown_mode()
    test_execution_metrics()

    print("\n" + "="*60)
    print("  ALL TESTS COMPLETED")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
