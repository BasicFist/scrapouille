"""
Scraping Routes
Endpoints for single URL scraping
"""

from fastapi import APIRouter, Depends, HTTPException
from api.models import (
    ScrapeRequest, ScrapeResponse, ScrapeMetadata,
    BatchScrapeRequest, BatchScrapeResponse, BatchResult
)
from api.dependencies import get_backend
from scraper.tui_integration import TUIScraperBackend
import time

router = APIRouter()


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(
    request: ScrapeRequest,
    backend: TUIScraperBackend = Depends(get_backend)
) -> ScrapeResponse:
    """
    Scrape a single URL with LLM extraction

    **Parameters**:
    - url: URL to scrape
    - prompt: Extraction prompt
    - model: LLM model to use (default: qwen2.5-coder:7b)
    - schema_name: Optional Pydantic schema for validation
    - rate_limit_mode: Rate limiting (none, aggressive, normal, polite)
    - stealth_level: Anti-detection level (off, low, medium, high)
    - use_cache: Enable Redis caching
    - markdown_mode: Use markdown conversion instead of LLM

    **Returns**:
    - success: Whether scraping succeeded
    - data: Scraped data (JSON object)
    - metadata: Execution metadata (time, model, fallback attempts, cached, validation)
    - error: Error message if failed

    **Example**:
    ```json
    {
      "url": "https://example.com/product",
      "prompt": "Extract product name, price, and rating",
      "model": "qwen2.5-coder:7b",
      "schema_name": "Product",
      "use_cache": true
    }
    ```
    """
    start_time = time.time()

    try:
        # Call backend scraping function
        result, metadata = await backend.scrape_single_url(
            url=request.url,
            prompt=request.prompt,
            model=request.model,
            schema_name=request.schema_name,
            rate_limit_mode=request.rate_limit_mode,
            stealth_level=request.stealth_level,
            use_cache=request.use_cache,
            markdown_mode=request.markdown_mode,
        )

        # Build metadata response
        scrape_metadata = ScrapeMetadata(
            execution_time=metadata.get('execution_time', 0.0),
            model_used=metadata.get('model_used', request.model),
            fallback_attempts=metadata.get('fallback_attempts', 0),
            cached=metadata.get('cached', False),
            validation_passed=metadata.get('validation_passed'),
        )

        return ScrapeResponse(
            success=True,
            data=result,
            metadata=scrape_metadata,
            error=None
        )

    except ValueError as e:
        # Validation or scraping error
        execution_time = time.time() - start_time
        return ScrapeResponse(
            success=False,
            data=None,
            metadata=ScrapeMetadata(
                execution_time=execution_time,
                model_used=request.model,
                fallback_attempts=0,
                cached=False,
                validation_passed=False,
            ),
            error=str(e)
        )

    except Exception as e:
        # Unexpected error
        execution_time = time.time() - start_time
        return ScrapeResponse(
            success=False,
            data=None,
            metadata=ScrapeMetadata(
                execution_time=execution_time,
                model_used=request.model,
                fallback_attempts=0,
                cached=False,
                validation_passed=None,
            ),
            error=f"Unexpected error: {str(e)}"
        )


@router.post("/scrape/batch", response_model=BatchScrapeResponse)
async def scrape_batch(
    request: BatchScrapeRequest,
    backend: TUIScraperBackend = Depends(get_backend)
) -> BatchScrapeResponse:
    """
    Scrape multiple URLs concurrently with progress tracking

    **Parameters**:
    - urls: List of URLs to scrape (1-100)
    - prompt: Shared extraction prompt for all URLs
    - model: LLM model to use (default: qwen2.5-coder:7b)
    - schema_name: Optional Pydantic schema for validation
    - max_concurrent: Max concurrent operations (1-20, default: 5)
    - timeout_per_url: Timeout per URL in seconds (10-120, default: 30)
    - use_cache: Enable Redis caching
    - use_rate_limiting: Enable rate limiting
    - use_stealth: Enable stealth mode

    **Returns**:
    - success: Overall batch success (true if at least one succeeded)
    - results: List of BatchResult objects (one per URL)
    - summary: Statistics (total, successful, failed, cached, timing)
    - error: Overall error message if complete failure

    **Example**:
    ```json
    {
      "urls": ["https://example.com/1", "https://example.com/2"],
      "prompt": "Extract title and main content",
      "model": "qwen2.5-coder:7b",
      "max_concurrent": 5,
      "use_cache": true
    }
    ```
    """
    start_time = time.time()

    try:
        # Call backend batch scraping function
        results = await backend.scrape_batch(
            urls=request.urls,
            prompt=request.prompt,
            model=request.model,
            schema_name=request.schema_name,
            max_concurrent=request.max_concurrent,
            timeout_per_url=request.timeout_per_url,
            use_cache=request.use_cache,
            use_rate_limiting=request.use_rate_limiting,
            use_stealth=request.use_stealth,
        )

        # Convert backend results to API models
        batch_results = []
        for result in results:
            batch_results.append(BatchResult(
                url=result.get('url', ''),
                index=result.get('index', 0),
                success=result.get('success', False),
                data=result.get('data'),
                error=result.get('error'),
                execution_time=result.get('execution_time', 0.0),
                model_used=result.get('model_used'),
                fallback_attempts=result.get('fallback_attempts', 0),
                cached=result.get('cached', False),
                validation_passed=result.get('validation_passed'),
            ))

        # Calculate summary statistics
        total_time = time.time() - start_time
        successful = sum(1 for r in batch_results if r.success)
        failed = len(batch_results) - successful
        cached = sum(1 for r in batch_results if r.cached)
        avg_time = total_time / len(batch_results) if batch_results else 0.0

        summary = {
            "total": len(batch_results),
            "successful": successful,
            "failed": failed,
            "cached": cached,
            "total_time": round(total_time, 2),
            "avg_time_per_url": round(avg_time, 2),
        }

        return BatchScrapeResponse(
            success=successful > 0,
            results=batch_results,
            summary=summary,
            error=None if successful > 0 else "All URLs failed to scrape"
        )

    except Exception as e:
        # Unexpected error
        execution_time = time.time() - start_time
        return BatchScrapeResponse(
            success=False,
            results=[],
            summary={
                "total": len(request.urls),
                "successful": 0,
                "failed": len(request.urls),
                "cached": 0,
                "total_time": round(execution_time, 2),
                "avg_time_per_url": 0.0,
            },
            error=f"Batch scraping failed: {str(e)}"
        )


@router.get("/models")
async def list_models():
    """
    List available LLM models

    Returns list of models available for scraping
    """
    # Placeholder for Phase 2
    # In full version, query Ollama API for available models
    return {
        "models": [
            "qwen2.5-coder:7b",
            "llama3.1",
            "deepseek-coder-v2",
        ],
        "default": "qwen2.5-coder:7b",
        "fallback_chain": [
            "qwen2.5-coder:7b",
            "llama3.1",
            "deepseek-coder-v2",
        ]
    }


@router.get("/templates")
async def list_templates():
    """
    List available prompt templates

    Returns template names and descriptions
    """
    from scraper.templates import TEMPLATES, TEMPLATE_SCHEMA_MAP

    return {
        "templates": {
            name: {
                "prompt": template[:200] + "..." if len(template) > 200 else template,
                "recommended_schema": TEMPLATE_SCHEMA_MAP.get(name)
            }
            for name, template in TEMPLATES.items()
        }
    }


@router.get("/schemas")
async def list_schemas():
    """
    List available validation schemas

    Returns schema names and field definitions
    """
    from scraper.models import SCHEMAS

    return {
        "schemas": list(SCHEMAS.keys()),
        "definitions": {
            name: {
                "fields": list(schema.model_fields.keys())
            }
            for name, schema in SCHEMAS.items()
        }
    }
