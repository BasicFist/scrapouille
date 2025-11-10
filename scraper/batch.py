"""
Async batch processing module for Scrapouille v3.0 Phase 3.

Provides concurrent scraping of multiple URLs with:
- Configurable concurrency limits (asyncio.Semaphore)
- Progress tracking via callbacks
- Integration with Phase 1 & 2 features (fallback, cache, metrics, rate limiting)
- Graceful error handling and result aggregation
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Any, Dict, TYPE_CHECKING
from datetime import datetime
import time

# Lazy import to avoid langchain issues in tests
if TYPE_CHECKING:
    from scrapegraphai.graphs import SmartScraperGraph

from scraper.fallback import ModelFallbackExecutor, ModelConfig
from scraper.cache import ScraperCache
from scraper.metrics import MetricsDB
from scraper.ratelimit import RateLimiter, RateLimitConfig
from scraper.models import validate_data, SCHEMAS
from scraper.stealth import StealthConfig, StealthHeaders

logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """Configuration for batch processing operations.

    Attributes:
        max_concurrent: Maximum number of concurrent scrapes (default: 5)
        timeout_per_url: Timeout for each URL in seconds (default: 30.0)
        continue_on_error: Continue processing if individual URLs fail (default: True)
        use_cache: Enable cache lookups/storage (default: True)
        use_rate_limiting: Apply rate limiting between requests (default: True)
        use_fallback: Enable model fallback chain (default: True)
        validate_results: Validate results against schema if provided (default: True)
        use_stealth: Enable stealth mode anti-detection (default: False)
    """
    max_concurrent: int = 5
    timeout_per_url: float = 30.0
    continue_on_error: bool = True
    use_cache: bool = True
    use_rate_limiting: bool = True
    use_fallback: bool = True
    validate_results: bool = True
    use_stealth: bool = False


@dataclass
class BatchResult:
    """Result for a single URL in batch processing.

    Attributes:
        url: The URL that was scraped
        index: Original position in the batch (for ordering)
        success: Whether the scrape succeeded
        data: Extracted data (None if failed)
        error: Error message (None if succeeded)
        execution_time: Time taken in seconds
        model_used: LLM model that succeeded (None if failed)
        fallback_attempts: Number of fallback attempts made
        cached: Whether result came from cache
        timestamp: When the scrape completed
        validation_passed: Whether schema validation passed (None if no schema)
    """
    url: str
    index: int
    success: bool = False
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    model_used: Optional[str] = None
    fallback_attempts: int = 0
    cached: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    validation_passed: Optional[bool] = None


class AsyncBatchProcessor:
    """Async batch processor for concurrent web scraping.

    Features:
    - Concurrent processing with semaphore-based throttling
    - Integration with ModelFallbackExecutor for reliability
    - Cache checking before processing (ScraperCache)
    - Rate limiting between requests (RateLimiter)
    - Metrics logging per result (MetricsDB)
    - Real-time progress callbacks
    - Graceful error handling

    Example:
        ```python
        processor = AsyncBatchProcessor(
            fallback_chain=[ModelConfig(name="qwen2.5-coder:7b")],
            graph_config={"llm": {"model": "qwen2.5-coder:7b"}},
            config=BatchConfig(max_concurrent=10)
        )

        results = await processor.process_batch(
            urls=["https://example.com", "https://example.org"],
            prompt="Extract the title",
            progress_callback=lambda done, total, url: print(f"{done}/{total}: {url}")
        )
        ```
    """

    def __init__(
        self,
        fallback_chain: List[ModelConfig],
        graph_config: Dict[str, Any],
        config: BatchConfig = BatchConfig(),
        cache: Optional[ScraperCache] = None,
        metrics_db: Optional[MetricsDB] = None,
        rate_limiter: Optional[RateLimiter] = None,
        stealth_config: Optional[StealthConfig] = None
    ):
        """Initialize async batch processor.

        Args:
            fallback_chain: List of model configs for fallback chain
            graph_config: ScrapegraphAI graph configuration
            config: Batch processing configuration
            cache: Optional cache instance (created if None and enabled)
            metrics_db: Optional metrics database (created if None)
            rate_limiter: Optional rate limiter (created if None and enabled)
            stealth_config: Optional stealth configuration (created if None and enabled)
        """
        self.fallback_chain = fallback_chain
        self.graph_config = graph_config
        self.config = config

        # Initialize Phase 2 components
        self.cache = cache if cache is not None else ScraperCache(enabled=config.use_cache)
        self.metrics_db = metrics_db if metrics_db is not None else MetricsDB()

        # Initialize rate limiter if enabled
        if config.use_rate_limiting and rate_limiter is None:
            # Default to "polite" rate limiting for batch processing
            rate_config = RateLimitConfig(min_delay_seconds=5.0, max_delay_seconds=10.0)
            self.rate_limiter = RateLimiter(rate_config)
        else:
            self.rate_limiter = rate_limiter

        # Initialize Phase 4: Stealth mode
        if config.use_stealth and stealth_config is None:
            # Default to MEDIUM stealth for batch processing
            from scraper.stealth import get_stealth_config
            self.stealth_config = get_stealth_config("medium")
        else:
            self.stealth_config = stealth_config

        self.stealth_headers = StealthHeaders() if config.use_stealth else None

        # Concurrency control
        self.semaphore = asyncio.Semaphore(config.max_concurrent)

        logger.info(f"AsyncBatchProcessor initialized: max_concurrent={config.max_concurrent}, "
                   f"cache={config.use_cache}, rate_limiting={config.use_rate_limiting}, "
                   f"stealth={config.use_stealth}")

    async def _scrape_single(
        self,
        url: str,
        index: int,
        prompt: str,
        schema_name: Optional[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        total_urls: int = 0
    ) -> BatchResult:
        """Scrape a single URL with full integration (cache, fallback, rate limit, metrics).

        Args:
            url: URL to scrape
            index: Position in batch
            prompt: Extraction prompt
            schema_name: Optional schema for validation
            progress_callback: Optional callback(completed, total, current_url)
            total_urls: Total number of URLs in batch

        Returns:
            BatchResult with scrape outcome
        """
        start_time = time.time()
        result = BatchResult(url=url, index=index)

        try:
            # Step 1: Check cache if enabled
            if self.config.use_cache and self.cache.enabled:
                cache_key_params = {
                    'model': self.fallback_chain[0].name if self.fallback_chain else 'unknown',
                    'schema': schema_name or 'none'
                }
                cached_data = self.cache.get(url, prompt, **cache_key_params)

                if cached_data:
                    result.success = True
                    result.data = cached_data
                    result.cached = True
                    result.execution_time = time.time() - start_time
                    result.model_used = cache_key_params['model']

                    logger.info(f"Cache HIT for {url} ({result.execution_time:.2f}s)")

                    # Invoke progress callback
                    if progress_callback:
                        progress_callback(index + 1, total_urls, url)

                    return result

            # Step 2: Apply rate limiting if enabled
            if self.config.use_rate_limiting and self.rate_limiter:
                # Run rate limiter wait in executor to avoid blocking event loop
                await asyncio.get_event_loop().run_in_executor(
                    None, self.rate_limiter.wait
                )

            # Step 2.5: Apply stealth headers if enabled
            scraping_config = self.graph_config.copy()
            if self.config.use_stealth and self.stealth_headers and self.stealth_config:
                stealth_hdrs = self.stealth_headers.get_headers(self.stealth_config)

                # Inject stealth headers into graph config
                if "loader_kwargs" not in scraping_config:
                    scraping_config["loader_kwargs"] = {}
                scraping_config["loader_kwargs"]["headers"] = stealth_hdrs

                logger.debug(f"Applied stealth headers: UA={stealth_hdrs.get('User-Agent', 'N/A')[:50]}...")

            # Step 3: Execute scraping with fallback chain
            if self.config.use_fallback:
                # Lazy import only when actually scraping
                from scrapegraphai.graphs import SmartScraperGraph

                executor = ModelFallbackExecutor(self.fallback_chain)

                # Run synchronous scraping in executor to avoid blocking
                scrape_result, model_used, attempts = await asyncio.get_event_loop().run_in_executor(
                    None,
                    executor.execute_with_fallback,
                    SmartScraperGraph,
                    prompt,
                    {"user_prompt": prompt, "url": url},
                    scraping_config  # Use stealth-enhanced config
                )

                result.data = scrape_result
                result.model_used = model_used
                result.fallback_attempts = attempts
            else:
                # Direct scraping without fallback
                from scrapegraphai.graphs import SmartScraperGraph

                graph = SmartScraperGraph(
                    prompt=prompt,
                    source=url,
                    config=scraping_config  # Use stealth-enhanced config
                )

                scrape_result = await asyncio.get_event_loop().run_in_executor(
                    None, graph.run
                )

                result.data = scrape_result
                result.model_used = self.graph_config.get("llm", {}).get("model", "unknown")
                result.fallback_attempts = 1

            # Step 4: Validate if schema provided
            if schema_name and self.config.validate_results:
                is_valid, validated_data, error_msg = validate_data(result.data, schema_name)
                result.validation_passed = is_valid

                if is_valid:
                    result.data = validated_data  # Already a dict from validate_data()
                else:
                    logger.warning(f"Validation failed for {url}: {error_msg}")

            # Step 5: Cache result if enabled and successful
            if self.config.use_cache and self.cache.enabled and result.data:
                cache_key_params = {
                    'model': result.model_used,
                    'schema': schema_name or 'none'
                }
                self.cache.set(url, prompt, result.data, **cache_key_params)

            result.success = True
            result.execution_time = time.time() - start_time

            logger.info(f"Scraped {url} successfully with {result.model_used} "
                       f"({result.execution_time:.2f}s, attempts={result.fallback_attempts})")

        except asyncio.TimeoutError:
            result.success = False
            result.error = f"Timeout after {self.config.timeout_per_url}s"
            result.execution_time = time.time() - start_time
            logger.error(f"Timeout scraping {url}")

        except Exception as e:
            result.success = False
            result.error = str(e)
            result.execution_time = time.time() - start_time
            logger.error(f"Error scraping {url}: {e}", exc_info=True)

        finally:
            # Step 6: Log to metrics database
            self.metrics_db.log_scrape(
                url=url,
                prompt=prompt,
                model=result.model_used or "unknown",
                execution_time=result.execution_time,
                fallback_attempts=result.fallback_attempts,
                validation_passed=result.validation_passed if result.validation_passed is not None else True,
                schema_used=schema_name or "",
                error=result.error or "",
                cached=result.cached
            )

            # Invoke progress callback
            if progress_callback:
                progress_callback(index + 1, total_urls, url)

        return result

    async def _scrape_with_semaphore(
        self,
        url: str,
        index: int,
        prompt: str,
        schema_name: Optional[str],
        progress_callback: Optional[Callable[[int, int, str], None]],
        total_urls: int
    ) -> BatchResult:
        """Wrapper to enforce concurrency limit via semaphore.

        Args:
            url: URL to scrape
            index: Position in batch
            prompt: Extraction prompt
            schema_name: Optional schema name
            progress_callback: Progress callback
            total_urls: Total URLs in batch

        Returns:
            BatchResult
        """
        async with self.semaphore:
            try:
                return await asyncio.wait_for(
                    self._scrape_single(url, index, prompt, schema_name, progress_callback, total_urls),
                    timeout=self.config.timeout_per_url
                )
            except asyncio.TimeoutError:
                return BatchResult(
                    url=url,
                    index=index,
                    success=False,
                    error=f"Timeout after {self.config.timeout_per_url}s",
                    execution_time=self.config.timeout_per_url
                )

    async def process_batch(
        self,
        urls: List[str],
        prompt: str,
        schema_name: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[BatchResult]:
        """Process a batch of URLs concurrently.

        Args:
            urls: List of URLs to scrape
            prompt: Extraction prompt (same for all URLs)
            schema_name: Optional schema name for validation
            progress_callback: Optional callback(completed_count, total_count, current_url)

        Returns:
            List of BatchResult objects in original order

        Raises:
            ValueError: If urls list is empty
        """
        if not urls:
            raise ValueError("URLs list cannot be empty")

        logger.info(f"Starting batch processing: {len(urls)} URLs, "
                   f"max_concurrent={self.config.max_concurrent}")

        # Create tasks for all URLs
        tasks = [
            self._scrape_with_semaphore(
                url=url,
                index=i,
                prompt=prompt,
                schema_name=schema_name,
                progress_callback=progress_callback,
                total_urls=len(urls)
            )
            for i, url in enumerate(urls)
        ]

        # Execute all tasks concurrently
        if self.config.continue_on_error:
            # Gather with exception handling
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Convert exceptions to failed BatchResults
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(BatchResult(
                        url=urls[i],
                        index=i,
                        success=False,
                        error=str(result),
                        execution_time=0.0
                    ))
                else:
                    processed_results.append(result)

            results = processed_results
        else:
            # Stop on first exception
            results = await asyncio.gather(*tasks)

        # Sort results by original index
        results.sort(key=lambda r: r.index)

        # Log summary
        successful = sum(1 for r in results if r.success)
        cached = sum(1 for r in results if r.cached)
        total_time = sum(r.execution_time for r in results)

        logger.info(f"Batch complete: {successful}/{len(results)} successful, "
                   f"{cached} from cache, total_time={total_time:.2f}s")

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from integrated components.

        Returns:
            Dictionary with cache stats, rate limiter stats, and metrics stats
        """
        stats = {}

        if self.cache and self.cache.enabled:
            stats['cache'] = self.cache.get_stats()

        if self.rate_limiter:
            stats['rate_limiter'] = self.rate_limiter.get_stats()

        stats['metrics'] = self.metrics_db.get_stats(days=7)

        return stats
