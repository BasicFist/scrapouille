"""
TUI Integration Module
Connects the TUI to the Scrapouille scraping backend

This module provides a clean API for the TUI to interact with all Scrapouille
backend features:
- Single URL scraping with fallback chain
- Batch processing with concurrent execution
- Metrics collection and analytics
- Cache management
- Health checks for dependencies (Ollama, Redis)

The TUIScraperBackend class acts as a facade, simplifying the TUI layer by
handling all the complexity of coordinating multiple backend modules.

Version: Scrapouille v3.0 Phase 4
"""

import asyncio
from typing import Dict, Any, Optional, List, Tuple

from scrapegraphai.graphs import SmartScraperGraph

from .fallback import ModelFallbackExecutor, ModelConfig, DEFAULT_FALLBACK_CHAIN
from .ratelimit import RateLimiter, RateLimitConfig, RATE_LIMIT_PRESETS
from .cache import ScraperCache
from .metrics import MetricsDB
from .models import SCHEMAS, validate_data
from .stealth import get_stealth_config, StealthHeaders
from .batch import AsyncBatchProcessor, BatchConfig, BatchResult


class TUIScraperBackend:
    """Backend integration for TUI scraping operations"""

    def __init__(
        self,
        cache: Optional[ScraperCache] = None,
        metrics_db: Optional[MetricsDB] = None,
    ):
        """Initialize the backend

        Args:
            cache: Optional ScraperCache instance
            metrics_db: Optional MetricsDB instance
        """
        self.cache = cache or ScraperCache(enabled=False)
        self.metrics_db = metrics_db or MetricsDB()

    async def scrape_single_url(
        self,
        url: str,
        prompt: str,
        model: str = "qwen2.5-coder:7b",
        schema_name: Optional[str] = None,
        rate_limit_mode: str = "normal",
        stealth_level: str = "off",
        use_cache: bool = True,
        markdown_mode: bool = False,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Scrape a single URL

        Args:
            url: URL to scrape
            prompt: Extraction prompt
            model: Primary model to use
            schema_name: Optional validation schema name
            rate_limit_mode: Rate limiting mode (none/aggressive/normal/polite)
            stealth_level: Stealth mode level (off/low/medium/high)
            use_cache: Whether to use caching
            markdown_mode: Whether to use markdown extraction only

        Returns:
            Tuple of (result_data, metadata)
            metadata includes: execution_time, model_used, fallback_attempts, cached, validation_passed
        """
        start_time = asyncio.get_event_loop().time()
        cached = False
        fallback_attempts = 0
        validation_passed = None

        try:
            # Check cache
            cache_key_params = {
                'model': model,
                'schema': schema_name,
                'markdown_mode': markdown_mode,
            }

            if use_cache and self.cache.enabled:
                cached_result = self.cache.get(url, prompt, **cache_key_params)
                if cached_result:
                    execution_time = asyncio.get_event_loop().time() - start_time
                    return cached_result, {
                        'execution_time': execution_time,
                        'model_used': model,
                        'fallback_attempts': 0,
                        'cached': True,
                        'validation_passed': True,
                    }

            # Apply rate limiting
            if rate_limit_mode != "none":
                config = RATE_LIMIT_PRESETS[rate_limit_mode]
                limiter = RateLimiter(config)
                limiter.wait()

            # Build graph configuration
            graph_config = {
                "llm": {
                    "provider": "ollama",
                    "model": model,
                    "base_url": "http://localhost:11434",
                },
                "verbose": False,
                "headless": True,
            }

            # Apply stealth mode
            stealth_config = get_stealth_config(stealth_level)
            if stealth_config.is_enabled():
                headers_gen = StealthHeaders()
                headers = headers_gen.get_headers(stealth_config)
                graph_config["loader_kwargs"] = {"headers": headers}

            # Build fallback chain
            fallback_chain = [
                ModelConfig(name=model),
                *DEFAULT_FALLBACK_CHAIN,
            ]
            # Remove duplicates while preserving order
            seen = set()
            fallback_chain = [
                mc for mc in fallback_chain
                if mc.name not in seen and not seen.add(mc.name)
            ]

            executor = ModelFallbackExecutor(fallback_chain)

            # Execute with fallback
            result, model_used, fallback_attempts = await asyncio.to_thread(
                executor.execute_with_fallback,
                SmartScraperGraph,
                prompt,
                url,
                extraction_mode=markdown_mode,
                **graph_config,
            )

            # Validate if schema provided
            if schema_name and schema_name in SCHEMAS:
                is_valid, validated_data, error_msg = validate_data(result, schema_name)
                validation_passed = is_valid
                if is_valid:
                    result = validated_data.model_dump() if hasattr(validated_data, 'model_dump') else dict(validated_data)
            else:
                validation_passed = None

            # Cache result
            if use_cache and self.cache.enabled:
                self.cache.set(url, prompt, result, ttl_hours=24, **cache_key_params)

            execution_time = asyncio.get_event_loop().time() - start_time

            # Log to metrics
            self.metrics_db.log_scrape(
                url=url,
                prompt=prompt,
                model=model_used,
                execution_time=execution_time,
                fallback_attempts=fallback_attempts,
                validation_passed=validation_passed if validation_passed is not None else True,
                cached=cached,
                schema_used=schema_name,
            )

            metadata = {
                'execution_time': execution_time,
                'model_used': model_used,
                'fallback_attempts': fallback_attempts,
                'cached': cached,
                'validation_passed': validation_passed,
            }

            return result, metadata

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time

            # Log error to metrics
            self.metrics_db.log_scrape(
                url=url,
                prompt=prompt,
                model=model,
                execution_time=execution_time,
                fallback_attempts=fallback_attempts,
                validation_passed=False,
                error_message=str(e),
            )

            raise

    async def scrape_batch(
        self,
        urls: List[str],
        prompt: str,
        model: str = "qwen2.5-coder:7b",
        schema_name: Optional[str] = None,
        max_concurrent: int = 5,
        timeout_per_url: float = 30.0,
        use_cache: bool = True,
        use_rate_limiting: bool = True,
        use_stealth: bool = False,
        progress_callback: Optional[callable] = None,
    ) -> List[BatchResult]:
        """Scrape multiple URLs in batch

        Args:
            urls: List of URLs to scrape
            prompt: Shared extraction prompt
            model: Primary model to use
            schema_name: Optional validation schema name
            max_concurrent: Maximum concurrent requests
            timeout_per_url: Timeout per URL in seconds
            use_cache: Whether to use caching
            use_rate_limiting: Whether to use rate limiting
            use_stealth: Whether to use stealth mode
            progress_callback: Optional callback for progress updates

        Returns:
            List of BatchResult objects
        """
        # Build graph configuration
        graph_config = {
            "llm": {
                "provider": "ollama",
                "model": model,
                "base_url": "http://localhost:11434",
            },
            "verbose": False,
            "headless": True,
        }

        # Apply stealth mode
        if use_stealth:
            stealth_config = get_stealth_config("medium")
            headers_gen = StealthHeaders()
            headers = headers_gen.get_headers(stealth_config)
            graph_config["loader_kwargs"] = {"headers": headers}

        # Build fallback chain
        fallback_chain = [
            ModelConfig(name=model),
            *DEFAULT_FALLBACK_CHAIN,
        ]
        # Remove duplicates
        seen = set()
        fallback_chain = [
            mc for mc in fallback_chain
            if mc.name not in seen and not seen.add(mc.name)
        ]

        # Build batch config
        batch_config = BatchConfig(
            max_concurrent=max_concurrent,
            timeout_per_url=timeout_per_url,
            continue_on_error=True,
            use_cache=use_cache,
            use_rate_limiting=use_rate_limiting,
        )

        # Initialize rate limiter if needed
        rate_limiter = None
        if use_rate_limiting:
            rate_config = RATE_LIMIT_PRESETS["normal"]
            rate_limiter = RateLimiter(rate_config)

        # Create batch processor
        processor = AsyncBatchProcessor(
            fallback_chain=fallback_chain,
            graph_config=graph_config,
            config=batch_config,
            cache=self.cache if use_cache else None,
            metrics_db=self.metrics_db,
            rate_limiter=rate_limiter,
        )

        # Process batch
        results = await processor.process_batch(
            urls=urls,
            prompt=prompt,
            schema_name=schema_name if schema_name else None,
            progress_callback=progress_callback,
        )

        return results

    def get_metrics_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get metrics statistics

        Args:
            days: Number of days to look back

        Returns:
            Dictionary of statistics
        """
        return self.metrics_db.get_stats(days=days)

    def get_recent_scrapes(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent scrape records

        Args:
            limit: Maximum number of records to return

        Returns:
            List of scrape records
        """
        recent_metrics = self.metrics_db.get_recent(limit=limit)
        return [metric.to_dict() for metric in recent_metrics]

    async def check_ollama_connection(self, base_url: str = "http://localhost:11434") -> bool:
        """Check if Ollama is running

        Args:
            base_url: Ollama base URL

        Returns:
            True if connected, False otherwise
        """
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/api/tags", timeout=2.0)
                return response.status_code == 200
        except Exception:
            return False
