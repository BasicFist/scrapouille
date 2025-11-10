"""
Unit tests for Async Batch Processing System
Tests concurrent scraping, progress tracking, and error handling
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
from scraper.batch import AsyncBatchProcessor, BatchConfig, BatchResult
from scraper.fallback import ModelConfig
from scraper.cache import ScraperCache
from scraper.metrics import MetricsDB
from scraper.ratelimit import RateLimiter, RateLimitConfig


# ============================================================================
# BatchConfig Tests
# ============================================================================

def test_batch_config_defaults():
    """Test BatchConfig default values"""
    config = BatchConfig()

    assert config.max_concurrent == 5
    assert config.timeout_per_url == 30.0
    assert config.continue_on_error is True
    assert config.use_cache is True
    assert config.use_rate_limiting is True
    assert config.use_fallback is True
    assert config.validate_results is True


def test_batch_config_custom_values():
    """Test BatchConfig with custom values"""
    config = BatchConfig(
        max_concurrent=10,
        timeout_per_url=60.0,
        continue_on_error=False,
        use_cache=False,
        use_rate_limiting=False,
        use_fallback=False,
        validate_results=False
    )

    assert config.max_concurrent == 10
    assert config.timeout_per_url == 60.0
    assert config.continue_on_error is False
    assert config.use_cache is False
    assert config.use_rate_limiting is False
    assert config.use_fallback is False
    assert config.validate_results is False


# ============================================================================
# BatchResult Tests
# ============================================================================

def test_batch_result_success():
    """Test BatchResult for successful scrape"""
    result = BatchResult(
        url="http://test.com",
        index=0,
        success=True,
        data={"title": "Test"},
        execution_time=2.5,
        model_used="qwen2.5-coder:7b",
        fallback_attempts=1,
        cached=False
    )

    assert result.url == "http://test.com"
    assert result.index == 0
    assert result.success is True
    assert result.data == {"title": "Test"}
    assert result.error is None
    assert result.execution_time == 2.5
    assert result.model_used == "qwen2.5-coder:7b"
    assert result.fallback_attempts == 1
    assert result.cached is False


def test_batch_result_failure():
    """Test BatchResult for failed scrape"""
    result = BatchResult(
        url="http://test.com",
        index=0,
        success=False,
        error="Timeout",
        execution_time=30.0
    )

    assert result.url == "http://test.com"
    assert result.success is False
    assert result.data is None
    assert result.error == "Timeout"
    assert result.model_used is None


def test_batch_result_cached():
    """Test BatchResult for cached result"""
    result = BatchResult(
        url="http://test.com",
        index=0,
        success=True,
        data={"title": "Cached"},
        cached=True,
        execution_time=0.05,
        model_used="cache"
    )

    assert result.cached is True
    assert result.execution_time < 0.1
    assert result.model_used == "cache"


# ============================================================================
# AsyncBatchProcessor Initialization Tests
# ============================================================================

@patch('scraper.cache.redis.Redis')
def test_processor_initialization(mock_redis):
    """Test AsyncBatchProcessor initialization with default components"""
    mock_client = Mock()
    mock_redis.return_value = mock_client

    fallback_chain = [ModelConfig(name="qwen2.5-coder:7b")]
    graph_config = {"llm": {"model": "qwen2.5-coder:7b"}}

    processor = AsyncBatchProcessor(
        fallback_chain=fallback_chain,
        graph_config=graph_config
    )

    assert processor.fallback_chain == fallback_chain
    assert processor.graph_config == graph_config
    assert processor.cache is not None
    assert processor.metrics_db is not None
    assert processor.rate_limiter is not None
    assert processor.semaphore._value == 5  # default max_concurrent


@patch('scraper.cache.redis.Redis')
def test_processor_custom_concurrency(mock_redis):
    """Test AsyncBatchProcessor with custom concurrency limit"""
    mock_client = Mock()
    mock_redis.return_value = mock_client

    config = BatchConfig(max_concurrent=10)
    fallback_chain = [ModelConfig(name="qwen")]
    graph_config = {"llm": {"model": "qwen"}}

    processor = AsyncBatchProcessor(
        fallback_chain=fallback_chain,
        graph_config=graph_config,
        config=config
    )

    assert processor.semaphore._value == 10


@patch('scraper.cache.redis.Redis')
def test_processor_no_rate_limiting(mock_redis):
    """Test AsyncBatchProcessor without rate limiting"""
    mock_client = Mock()
    mock_redis.return_value = mock_client

    config = BatchConfig(use_rate_limiting=False)
    fallback_chain = [ModelConfig(name="qwen")]
    graph_config = {"llm": {"model": "qwen"}}

    processor = AsyncBatchProcessor(
        fallback_chain=fallback_chain,
        graph_config=graph_config,
        config=config
    )

    assert processor.rate_limiter is None


# ============================================================================
# Batch Processing Tests
# ============================================================================

@pytest.mark.asyncio
@patch('scraper.cache.redis.Redis')
@patch('scraper.batch.asyncio.get_event_loop')
async def test_process_batch_empty_urls(mock_event_loop, mock_redis):
    """Test process_batch raises error for empty URL list"""
    mock_client = Mock()
    mock_redis.return_value = mock_client

    fallback_chain = [ModelConfig(name="qwen")]
    graph_config = {"llm": {"model": "qwen"}}

    processor = AsyncBatchProcessor(
        fallback_chain=fallback_chain,
        graph_config=graph_config
    )

    with pytest.raises(ValueError, match="URLs list cannot be empty"):
        await processor.process_batch(
            urls=[],
            prompt="Extract title"
        )


@pytest.mark.asyncio
@patch('scraper.cache.redis.Redis')
@patch('scraper.batch.asyncio.get_event_loop')
async def test_process_batch_all_cached(mock_event_loop, mock_redis):
    """Test batch processing with all results from cache"""
    # Mock Redis client
    mock_client = Mock()
    mock_client.ping.return_value = True
    mock_redis.return_value = mock_client

    # Create processor with mocked cache
    fallback_chain = [ModelConfig(name="qwen")]
    graph_config = {"llm": {"model": "qwen"}}
    config = BatchConfig(use_cache=True, use_rate_limiting=False)

    processor = AsyncBatchProcessor(
        fallback_chain=fallback_chain,
        graph_config=graph_config,
        config=config
    )

    # Mock cache to return data and ensure it's enabled
    processor.cache.enabled = True
    processor.cache.get = Mock(return_value={"title": "Cached Title"})

    urls = ["http://test1.com", "http://test2.com", "http://test3.com"]
    results = await processor.process_batch(
        urls=urls,
        prompt="Extract title"
    )

    assert len(results) == 3
    assert all(r.success for r in results)
    assert all(r.cached for r in results)
    assert all(r.data == {"title": "Cached Title"} for r in results)


@pytest.mark.asyncio
@patch('scraper.cache.redis.Redis')
@patch('scraper.batch.ModelFallbackExecutor')
@patch('scraper.batch.asyncio.get_event_loop')
async def test_process_batch_with_scraping(mock_event_loop, mock_executor_class, mock_redis):
    """Test batch processing with actual scraping (cache miss)"""
    # Mock Redis
    mock_client = Mock()
    mock_redis.return_value = mock_client

    # Mock event loop executor
    mock_loop = Mock()
    mock_event_loop.return_value = mock_loop

    # Mock scraping results
    mock_loop.run_in_executor = AsyncMock(
        return_value=({"title": "Scraped Title"}, "qwen2.5-coder:7b", 1)
    )

    # Mock ModelFallbackExecutor
    mock_executor_instance = Mock()
    mock_executor_class.return_value = mock_executor_instance

    # Create processor
    fallback_chain = [ModelConfig(name="qwen2.5-coder:7b")]
    graph_config = {"llm": {"model": "qwen2.5-coder:7b"}}
    config = BatchConfig(use_cache=False, use_rate_limiting=False)

    processor = AsyncBatchProcessor(
        fallback_chain=fallback_chain,
        graph_config=graph_config,
        config=config
    )

    urls = ["http://test1.com", "http://test2.com"]
    results = await processor.process_batch(
        urls=urls,
        prompt="Extract title"
    )

    assert len(results) == 2
    assert all(r.success for r in results)
    assert all(not r.cached for r in results)


@pytest.mark.asyncio
@patch('scraper.cache.redis.Redis')
@patch('scraper.batch.asyncio.get_event_loop')
async def test_process_batch_with_errors_continue(mock_event_loop, mock_redis):
    """Test batch processing continues on errors when configured"""
    # Mock Redis
    mock_client = Mock()
    mock_redis.return_value = mock_client

    # Mock event loop - simulate failures
    mock_loop = Mock()
    mock_event_loop.return_value = mock_loop

    # First URL fails, second succeeds
    async def mock_executor(*args):
        if "test1" in str(args):
            raise Exception("Scraping failed")
        return ({"title": "Success"}, "qwen", 1)

    mock_loop.run_in_executor = AsyncMock(side_effect=mock_executor)

    # Create processor
    fallback_chain = [ModelConfig(name="qwen")]
    graph_config = {"llm": {"model": "qwen"}}
    config = BatchConfig(
        continue_on_error=True,
        use_cache=False,
        use_rate_limiting=False
    )

    processor = AsyncBatchProcessor(
        fallback_chain=fallback_chain,
        graph_config=graph_config,
        config=config
    )

    processor.cache.get = Mock(return_value=None)  # Cache miss

    urls = ["http://test1.com", "http://test2.com"]
    results = await processor.process_batch(
        urls=urls,
        prompt="Extract title"
    )

    assert len(results) == 2
    assert results[0].success is False
    assert results[0].error is not None


@pytest.mark.asyncio
@patch('scraper.cache.redis.Redis')
async def test_process_batch_timeout(mock_redis):
    """Test batch processing respects per-URL timeout"""
    # Mock Redis
    mock_client = Mock()
    mock_redis.return_value = mock_client

    # Create processor with very short timeout
    fallback_chain = [ModelConfig(name="qwen")]
    graph_config = {"llm": {"model": "qwen"}}
    config = BatchConfig(
        timeout_per_url=0.001,  # 1ms timeout - will fail
        use_cache=False,
        use_rate_limiting=False
    )

    processor = AsyncBatchProcessor(
        fallback_chain=fallback_chain,
        graph_config=graph_config,
        config=config
    )

    # Mock slow scraping
    async def slow_scrape(*args, **kwargs):
        await asyncio.sleep(1)  # Sleep longer than timeout
        return ({"data": "test"}, "qwen", 1)

    processor._scrape_single = AsyncMock(side_effect=slow_scrape)

    urls = ["http://test1.com"]
    results = await processor.process_batch(
        urls=urls,
        prompt="Extract title"
    )

    assert len(results) == 1
    assert results[0].success is False
    assert "Timeout" in results[0].error


@pytest.mark.asyncio
@patch('scraper.cache.redis.Redis')
async def test_process_batch_progress_callback(mock_redis):
    """Test batch processing invokes progress callback"""
    # Mock Redis
    mock_client = Mock()
    mock_redis.return_value = mock_client

    # Create processor
    fallback_chain = [ModelConfig(name="qwen")]
    graph_config = {"llm": {"model": "qwen"}}
    config = BatchConfig(use_cache=False, use_rate_limiting=False)

    processor = AsyncBatchProcessor(
        fallback_chain=fallback_chain,
        graph_config=graph_config,
        config=config
    )

    # Mock cache to return data (fast execution)
    processor.cache.get = Mock(return_value={"title": "Test"})

    # Track progress callback invocations
    progress_calls = []

    def progress_callback(done, total, url):
        progress_calls.append((done, total, url))

    urls = ["http://test1.com", "http://test2.com", "http://test3.com"]
    results = await processor.process_batch(
        urls=urls,
        prompt="Extract title",
        progress_callback=progress_callback
    )

    # Should have been called 3 times (once per URL)
    assert len(progress_calls) == 3
    assert progress_calls[0][0] == 1  # First completion
    assert progress_calls[1][0] == 2  # Second completion
    assert progress_calls[2][0] == 3  # Third completion
    assert all(total == 3 for _, total, _ in progress_calls)


@pytest.mark.asyncio
@patch('scraper.cache.redis.Redis')
async def test_process_batch_maintains_order(mock_redis):
    """Test batch processing maintains original URL order in results"""
    # Mock Redis
    mock_client = Mock()
    mock_redis.return_value = mock_client

    # Create processor
    fallback_chain = [ModelConfig(name="qwen")]
    graph_config = {"llm": {"model": "qwen"}}
    config = BatchConfig(use_cache=False, use_rate_limiting=False)

    processor = AsyncBatchProcessor(
        fallback_chain=fallback_chain,
        graph_config=graph_config,
        config=config
    )

    # Mock cache with different delays to test ordering
    async def mock_cache_get(url, *args, **kwargs):
        # Return None to force "scraping"
        return None

    processor.cache.get = Mock(side_effect=mock_cache_get)

    # Mock scraping with different data per URL
    call_count = [0]

    async def mock_scrape_single(url, index, *args, **kwargs):
        call_count[0] += 1
        # Simulate varying execution times
        await asyncio.sleep(0.01 * (3 - call_count[0]))  # Reverse order delays

        return BatchResult(
            url=url,
            index=index,
            success=True,
            data={"url": url, "index": index},
            execution_time=0.01
        )

    processor._scrape_single = mock_scrape_single

    urls = ["http://test1.com", "http://test2.com", "http://test3.com"]
    results = await processor.process_batch(
        urls=urls,
        prompt="Extract title"
    )

    # Results should be in original order despite varying execution times
    assert len(results) == 3
    assert results[0].url == "http://test1.com"
    assert results[1].url == "http://test2.com"
    assert results[2].url == "http://test3.com"
    assert results[0].index == 0
    assert results[1].index == 1
    assert results[2].index == 2


# ============================================================================
# Stats Tests
# ============================================================================

@patch('scraper.cache.redis.Redis')
def test_get_stats(mock_redis):
    """Test get_stats returns combined statistics"""
    # Mock Redis
    mock_client = Mock()
    mock_redis.return_value = mock_client

    # Create processor
    fallback_chain = [ModelConfig(name="qwen")]
    graph_config = {"llm": {"model": "qwen"}}

    processor = AsyncBatchProcessor(
        fallback_chain=fallback_chain,
        graph_config=graph_config
    )

    # Mock component stats
    processor.cache.get_stats = Mock(return_value={
        'enabled': True,
        'total_keys': 10,
        'keyspace_hits': 8,
        'keyspace_misses': 2
    })

    processor.rate_limiter.get_stats = Mock(return_value={
        'request_count': 5,
        'total_delay': 15.0
    })

    processor.metrics_db.get_stats = Mock(return_value={
        'total_scrapes': 15,
        'avg_time': 2.5,
        'error_rate': 5.0
    })

    stats = processor.get_stats()

    assert 'cache' in stats
    assert 'rate_limiter' in stats
    assert 'metrics' in stats
    assert stats['cache']['total_keys'] == 10
    assert stats['metrics']['total_scrapes'] == 15


# ============================================================================
# Integration-like Tests
# ============================================================================

@pytest.mark.asyncio
@patch('scraper.cache.redis.Redis')
async def test_full_batch_workflow_mixed_results(mock_redis):
    """Test complete batch workflow with mix of cached, successful, and failed results"""
    # Mock Redis
    mock_client = Mock()
    mock_redis.return_value = mock_client

    # Create processor
    fallback_chain = [ModelConfig(name="qwen")]
    graph_config = {"llm": {"model": "qwen"}}
    config = BatchConfig(
        max_concurrent=3,
        use_cache=True,
        use_rate_limiting=False,
        continue_on_error=True
    )

    processor = AsyncBatchProcessor(
        fallback_chain=fallback_chain,
        graph_config=graph_config,
        config=config
    )

    # Mock cache: first URL cached, others not
    def mock_cache_get(url, *args, **kwargs):
        if "test1" in url:
            return {"title": "Cached"}
        return None

    processor.cache.get = Mock(side_effect=mock_cache_get)
    processor.cache.set = Mock(return_value=True)

    # Mock scraping: second succeeds, third fails
    async def mock_scrape_single(url, index, *args, **kwargs):
        if "test1" in url:
            # Cached result
            return BatchResult(
                url=url, index=index, success=True,
                data={"title": "Cached"}, cached=True, execution_time=0.01
            )
        elif "test2" in url:
            # Successful scrape
            await asyncio.sleep(0.01)
            return BatchResult(
                url=url, index=index, success=True,
                data={"title": "Scraped"}, cached=False,
                model_used="qwen", fallback_attempts=1, execution_time=0.5
            )
        else:
            # Failed scrape
            return BatchResult(
                url=url, index=index, success=False,
                error="Network error", execution_time=0.3
            )

    processor._scrape_single = mock_scrape_single

    urls = ["http://test1.com", "http://test2.com", "http://test3.com"]
    results = await processor.process_batch(
        urls=urls,
        prompt="Extract title"
    )

    assert len(results) == 3

    # First: cached
    assert results[0].success is True
    assert results[0].cached is True
    assert results[0].data == {"title": "Cached"}

    # Second: scraped successfully
    assert results[1].success is True
    assert results[1].cached is False
    assert results[1].data == {"title": "Scraped"}

    # Third: failed
    assert results[2].success is False
    assert results[2].error == "Network error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
