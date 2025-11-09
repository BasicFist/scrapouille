#!/usr/bin/env python3
"""
Quick Wins Sprint Testing Suite - Simplified Version
Tests Quick Wins modules without scrapegraphai dependency issues
"""

import sys
import time
from datetime import datetime

# Import Quick Wins modules only
from scraper.utils import scrape_with_retry
from scraper.models import SCHEMAS, validate_data
from scraper.templates import TEMPLATES, TEMPLATE_SCHEMA_MAP

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_retry_logic():
    """Test 1: Retry logic module (without actual scraping)"""
    print_section("TEST 1: Retry Logic Module")

    print("1a. Testing retry decorator with successful function...")
    call_count = [0]

    def mock_scraper_success():
        call_count[0] += 1
        return {"data": "success", "attempt": call_count[0]}

    start = time.time()
    try:
        result = scrape_with_retry(mock_scraper_success)
        elapsed = time.time() - start
        print(f"✅ SUCCESS on attempt #{call_count[0]} ({elapsed:.3f}s)")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"❌ FAILED: {e}")

    print("\n1b. Testing retry with transient failures (2 failures then success)...")
    call_count[0] = 0

    def mock_scraper_transient():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ValueError(f"Transient error (attempt {call_count[0]})")
        return {"data": "success", "attempt": call_count[0]}

    start = time.time()
    try:
        result = scrape_with_retry(mock_scraper_transient)
        elapsed = time.time() - start
        print(f"✅ SUCCESS after {call_count[0]} attempts ({elapsed:.3f}s)")
        print(f"   Expected ~4s backoff (2s + 4s), actual: {elapsed:.1f}s")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"❌ FAILED: {e}")

    print("\n1c. Testing retry with permanent failure (all 3 attempts fail)...")
    call_count[0] = 0

    def mock_scraper_permanent():
        call_count[0] += 1
        raise ConnectionError(f"Permanent error (attempt {call_count[0]})")

    start = time.time()
    try:
        result = scrape_with_retry(mock_scraper_permanent)
        print(f"❌ UNEXPECTED: Should have failed but got: {result}")
    except ConnectionError as e:
        elapsed = time.time() - start
        print(f"✅ EXPECTED FAILURE after {call_count[0]} attempts ({elapsed:.3f}s)")
        print(f"   Expected ~14s total (2s + 4s + 8s), actual: {elapsed:.1f}s")
        print(f"   Error: {e}")

    print("\n1d. Testing retry with empty result (treated as ValueError)...")
    call_count[0] = 0

    def mock_scraper_empty():
        call_count[0] += 1
        return {}

    start = time.time()
    try:
        result = scrape_with_retry(mock_scraper_empty)
        print(f"❌ UNEXPECTED: Should have rejected empty result: {result}")
    except ValueError as e:
        elapsed = time.time() - start
        print(f"✅ EXPECTED FAILURE after {call_count[0]} attempts ({elapsed:.3f}s)")
        print(f"   Error: {e}")

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
        print(f"✅ VALIDATION PASSED")
        print(f"   Input:  {valid_product}")
        print(f"   Output: {validated}")
    else:
        print(f"❌ VALIDATION FAILED: {error}")

    # Test 2b: Invalid product - negative price
    print("\n2b. Testing invalid product data (negative price)...")
    invalid_product = {
        "name": "Bad Product",
        "price": -99.99,
        "in_stock": True,
        "rating": 4.5
    }
    success, validated, error = validate_data(invalid_product, "product")
    if not success:
        print(f"✅ VALIDATION CORRECTLY REJECTED")
        print(f"   Input: {invalid_product}")
        print(f"   Error: {error}")
    else:
        print(f"❌ VALIDATION INCORRECTLY PASSED: {validated}")

    # Test 2c: Invalid product - empty name
    print("\n2c. Testing invalid product data (empty name after strip)...")
    invalid_name = {
        "name": "   ",
        "price": 99.99,
        "in_stock": True,
        "rating": 4.5
    }
    success, validated, error = validate_data(invalid_name, "product")
    if not success:
        print(f"✅ VALIDATION CORRECTLY REJECTED")
        print(f"   Input: {invalid_name}")
        print(f"   Error: {error}")
    else:
        print(f"❌ VALIDATION INCORRECTLY PASSED: {validated}")

    # Test 2d: Invalid product - rating out of range
    print("\n2d. Testing invalid product data (rating > 5)...")
    invalid_rating = {
        "name": "Product",
        "price": 99.99,
        "in_stock": True,
        "rating": 10.0
    }
    success, validated, error = validate_data(invalid_rating, "product")
    if not success:
        print(f"✅ VALIDATION CORRECTLY REJECTED")
        print(f"   Error: {error}")
    else:
        print(f"❌ VALIDATION INCORRECTLY PASSED")

    # Test 2e: Article schema
    print("\n2e. Testing article schema validation...")
    valid_article = {
        "title": "AI Breakthrough in 2025",
        "author": "Jane Doe",
        "published_date": "2025-11-09",
        "summary": "New AI model achieves state-of-the-art results on multiple benchmarks"
    }
    success, validated, error = validate_data(valid_article, "article")
    if success:
        print(f"✅ ARTICLE VALIDATION PASSED")
        print(f"   Title: {validated['title']}")
        print(f"   Author: {validated['author']}")
    else:
        print(f"❌ ARTICLE VALIDATION FAILED: {error}")

    # Test 2f: Job listing schema
    print("\n2f. Testing job listing schema validation...")
    valid_job = {
        "title": "Senior Python Developer",
        "company": "Tech Corp",
        "location": "San Francisco, CA",
        "salary": "150000-200000",
        "description": "We're looking for an experienced Python developer..."
    }
    success, validated, error = validate_data(valid_job, "job")
    if success:
        print(f"✅ JOB VALIDATION PASSED")
        print(f"   Title: {validated['title']}")
        print(f"   Company: {validated['company']}")
    else:
        print(f"❌ JOB VALIDATION FAILED: {error}")

    # Test 2g: Schema that doesn't exist
    print("\n2g. Testing with non-existent schema...")
    success, validated, error = validate_data({"any": "data"}, "nonexistent")
    if success and validated == {"any": "data"}:
        print(f"✅ NON-EXISTENT SCHEMA CORRECTLY BYPASSED VALIDATION")
    else:
        print(f"❌ UNEXPECTED BEHAVIOR: success={success}, validated={validated}")

def test_templates():
    """Test 3: Few-shot prompt templates"""
    print_section("TEST 3: Few-Shot Prompt Templates")

    print("3a. Verifying all templates exist and have content...")
    for template_name, template_content in TEMPLATES.items():
        if template_name == "Custom":
            print(f"   ⚪ {template_name:<30} (empty by design)")
        elif len(template_content) > 0:
            print(f"   ✅ {template_name:<30} ({len(template_content)} chars)")
        else:
            print(f"   ❌ {template_name:<30} (EMPTY!)")

    print("\n3b. Verifying template-schema mappings...")
    for template_name, schema_name in TEMPLATE_SCHEMA_MAP.items():
        if schema_name in SCHEMAS:
            print(f"   ✅ {template_name:<30} → {schema_name}")
        else:
            print(f"   ❌ {template_name:<30} → {schema_name} (INVALID SCHEMA)")

    print("\n3c. Checking E-commerce Products template structure...")
    ecommerce_template = TEMPLATES["E-commerce Products"]
    has_fields = "name" in ecommerce_template and "price" in ecommerce_template
    has_examples = "Examples:" in ecommerce_template or "Example:" in ecommerce_template
    print(f"   Contains field descriptions: {'✅' if has_fields else '❌'}")
    print(f"   Contains examples: {'✅' if has_examples else '❌'}")
    print(f"   Template preview:\n{ecommerce_template[:300]}...")

    print("\n3d. Checking News Articles template structure...")
    news_template = TEMPLATES["News Articles"]
    has_fields = "title" in news_template and "author" in news_template
    has_examples = "Examples:" in news_template or "Example:" in news_template
    print(f"   Contains field descriptions: {'✅' if has_fields else '❌'}")
    print(f"   Contains examples: {'✅' if has_examples else '❌'}")

def test_module_integration():
    """Test 4: Integration between modules"""
    print_section("TEST 4: Module Integration")

    print("4a. Testing template + schema integration...")
    template_name = "E-commerce Products"
    schema_name = TEMPLATE_SCHEMA_MAP.get(template_name)

    if schema_name:
        print(f"   Template: {template_name}")
        print(f"   Schema: {schema_name}")

        # Simulate what the scraper does
        mock_scraped_data = {
            "name": "Gaming Laptop",
            "price": 1499.99,
            "in_stock": True,
            "rating": 4.8
        }

        success, validated, error = validate_data(mock_scraped_data, schema_name)
        if success:
            print(f"   ✅ INTEGRATION WORKS: Template→Schema→Validation")
            print(f"      Validated: {validated}")
        else:
            print(f"   ❌ INTEGRATION FAILED: {error}")
    else:
        print(f"   ❌ NO SCHEMA MAPPING FOR {template_name}")

    print("\n4b. Testing all 5 schema types...")
    test_cases = [
        ("product", {"name": "Test", "price": 99.99, "in_stock": True, "rating": 4.0}),
        ("article", {"title": "Test", "author": "Author", "published_date": "2025-11-09", "summary": "Summary"}),
        ("job", {"title": "Job", "company": "Co", "location": "SF", "salary": "100k", "description": "Desc"}),
        ("research_paper", {"title": "Paper", "authors": ["A"], "publication_year": 2025, "abstract": "Abs"}),
        ("contact", {"name": "John", "email": "john@example.com", "phone": "123-456-7890"}),
    ]

    for schema_name, test_data in test_cases:
        success, validated, error = validate_data(test_data, schema_name)
        status = "✅" if success else "❌"
        print(f"   {status} {schema_name:<15} {' PASSED' if success else f' FAILED: {error}'}")

def test_metrics_simulation():
    """Test 5: Execution metrics tracking (simulated)"""
    print_section("TEST 5: Execution Metrics Tracking")

    print("5a. Simulating metrics collection during scraping...")

    metrics = {
        "start_time": datetime.now(),
        "retries": 0,
        "validation_passed": False,
        "execution_time": 0.0,
        "schema_used": "product"
    }

    # Simulate scraping with retry
    call_count = [0]

    def mock_scrape():
        call_count[0] += 1
        if call_count[0] < 2:
            metrics["retries"] += 1
            raise ValueError("First attempt failed")
        return {"name": "Product", "price": 99.99, "in_stock": True, "rating": 4.5}

    start = time.time()
    try:
        result = scrape_with_retry(mock_scrape)
        metrics["execution_time"] = time.time() - start

        # Validate
        success, validated, error = validate_data(result, metrics["schema_used"])
        metrics["validation_passed"] = success

        print(f"   ✅ Metrics collected successfully:")
        print(f"      Start time: {metrics['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"      Execution time: {metrics['execution_time']:.3f}s")
        print(f"      Retries: {metrics['retries']}")
        print(f"      Validation: {'✅ Passed' if metrics['validation_passed'] else '❌ Failed'}")
        print(f"      Schema used: {metrics['schema_used']}")
    except Exception as e:
        print(f"   ❌ Metrics test failed: {e}")

    print("\n5b. Verifying metrics are useful for monitoring...")
    useful_metrics = [
        "start_time",
        "execution_time",
        "retries",
        "validation_passed",
        "schema_used"
    ]
    for metric_name in useful_metrics:
        if metric_name in metrics:
            print(f"   ✅ {metric_name:<20} available")
        else:
            print(f"   ❌ {metric_name:<20} MISSING")

def main():
    """Run all Quick Wins tests"""
    print("\n" + "="*60)
    print("  WEB SCRAPER v2.0 - QUICK WINS SPRINT TEST SUITE")
    print("  (Simplified - Module Testing Only)")
    print("="*60)
    print(f"  Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Run all tests
    test_retry_logic()
    test_schema_validation()
    test_templates()
    test_module_integration()
    test_metrics_simulation()

    print("\n" + "="*60)
    print("  ALL TESTS COMPLETED")
    print("="*60)
    print("\nNOTE: These tests verify the Quick Wins modules in isolation.")
    print("Full integration testing requires fixing scrapegraphai dependencies.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
