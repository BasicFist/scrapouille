"""
Unit tests for Redis Caching System
Tests cache hit/miss, TTL, and graceful degradation
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from scraper.cache import ScraperCache


def test_cache_disabled_mode():
    """Test cache gracefully degrades when disabled"""
    cache = ScraperCache(enabled=False)

    assert cache.enabled is False
    assert cache.client is None

    # All operations should return None/False gracefully
    assert cache.get("http://test.com", "prompt") is None
    assert cache.set("http://test.com", "prompt", {"data": "test"}) is False


@patch('scraper.cache.redis.Redis')
def test_cache_redis_connection_failure(mock_redis):
    """Test cache degrades gracefully when Redis connection fails"""
    mock_client = Mock()
    mock_client.ping.side_effect = Exception("Connection refused")
    mock_redis.return_value = mock_client

    cache = ScraperCache(enabled=True)

    # Should fallback to disabled mode
    assert cache.enabled is False
    assert cache.client is None


@patch('scraper.cache.redis.Redis')
def test_cache_make_key_deterministic(mock_redis):
    """Test cache key generation is deterministic"""
    mock_client = Mock()
    mock_redis.return_value = mock_client

    cache = ScraperCache()

    # Same inputs should produce same key
    key1 = cache._make_key("http://test.com", "prompt", model="qwen")
    key2 = cache._make_key("http://test.com", "prompt", model="qwen")

    assert key1 == key2
    assert key1.startswith("scrape:")


@patch('scraper.cache.redis.Redis')
def test_cache_make_key_different_inputs(mock_redis):
    """Test different inputs produce different keys"""
    mock_client = Mock()
    mock_redis.return_value = mock_client

    cache = ScraperCache()

    key1 = cache._make_key("http://test1.com", "prompt")
    key2 = cache._make_key("http://test2.com", "prompt")
    key3 = cache._make_key("http://test1.com", "different prompt")

    assert key1 != key2
    assert key1 != key3
    assert key2 != key3


@patch('scraper.cache.redis.Redis')
def test_cache_hit(mock_redis):
    """Test cache returns stored result on hit"""
    mock_client = Mock()
    mock_client.get.return_value = json.dumps({"data": "test"})
    mock_redis.return_value = mock_client

    cache = ScraperCache()
    result = cache.get("http://test.com", "prompt")

    assert result == {"data": "test"}
    assert mock_client.get.called


@patch('scraper.cache.redis.Redis')
def test_cache_miss(mock_redis):
    """Test cache returns None on miss"""
    mock_client = Mock()
    mock_client.get.return_value = None
    mock_redis.return_value = mock_client

    cache = ScraperCache()
    result = cache.get("http://test.com", "prompt")

    assert result is None


@patch('scraper.cache.redis.Redis')
def test_cache_set(mock_redis):
    """Test cache stores result with TTL"""
    mock_client = Mock()
    mock_redis.return_value = mock_client

    cache = ScraperCache()
    result = cache.set("http://test.com", "prompt", {"data": "test"}, ttl_hours=24)

    assert result is True
    assert mock_client.setex.called

    # Check setex was called with correct parameters
    call_args = mock_client.setex.call_args
    assert call_args is not None
    # TTL should be in seconds (24 hours = 86400 seconds)
    assert "data" in call_args[0][2]  # The JSON data


@patch('scraper.cache.redis.Redis')
def test_cache_default_ttl(mock_redis):
    """Test cache uses default TTL when not specified"""
    mock_client = Mock()
    mock_redis.return_value = mock_client

    cache = ScraperCache(default_ttl_hours=48)
    cache.set("http://test.com", "prompt", {"data": "test"})

    assert mock_client.setex.called


@patch('scraper.cache.redis.Redis')
def test_cache_get_stats_enabled(mock_redis):
    """Test cache stats when Redis is enabled"""
    mock_client = Mock()
    mock_client.info.return_value = {
        'keyspace_hits': 100,
        'keyspace_misses': 25,
    }
    mock_client.dbsize.return_value = 50
    mock_redis.return_value = mock_client

    cache = ScraperCache()
    stats = cache.get_stats()

    assert stats['enabled'] is True
    assert stats['keyspace_hits'] == 100
    assert stats['keyspace_misses'] == 25
    assert stats['total_keys'] == 50


def test_cache_get_stats_disabled():
    """Test cache stats when disabled"""
    cache = ScraperCache(enabled=False)
    stats = cache.get_stats()

    assert stats['enabled'] is False


@patch('scraper.cache.redis.Redis')
def test_cache_clear_all(mock_redis):
    """Test clearing all cached results"""
    mock_client = Mock()
    mock_client.scan_iter.return_value = [
        "scrape:abc123",
        "scrape:def456",
        "scrape:ghi789"
    ]
    mock_redis.return_value = mock_client

    cache = ScraperCache()
    result = cache.clear_all()

    assert result is True
    assert mock_client.delete.called
    # Should delete all 3 keys
    assert mock_client.delete.call_args[0] == ("scrape:abc123", "scrape:def456", "scrape:ghi789")


@patch('scraper.cache.redis.Redis')
def test_cache_clear_all_no_keys(mock_redis):
    """Test clearing when no keys exist"""
    mock_client = Mock()
    mock_client.scan_iter.return_value = []
    mock_redis.return_value = mock_client

    cache = ScraperCache()
    result = cache.clear_all()

    assert result is True
    # Should not call delete if no keys
    assert not mock_client.delete.called


@patch('scraper.cache.redis.Redis')
def test_cache_error_handling_on_get(mock_redis):
    """Test cache handles errors gracefully on get"""
    mock_client = Mock()
    mock_client.get.side_effect = Exception("Redis error")
    mock_redis.return_value = mock_client

    cache = ScraperCache()
    result = cache.get("http://test.com", "prompt")

    # Should return None instead of crashing
    assert result is None


@patch('scraper.cache.redis.Redis')
def test_cache_error_handling_on_set(mock_redis):
    """Test cache handles errors gracefully on set"""
    mock_client = Mock()
    mock_client.setex.side_effect = Exception("Redis error")
    mock_redis.return_value = mock_client

    cache = ScraperCache()
    result = cache.set("http://test.com", "prompt", {"data": "test"})

    # Should return False instead of crashing
    assert result is False


@patch('scraper.cache.redis.Redis')
def test_cache_kwargs_included_in_key(mock_redis):
    """Test additional kwargs are included in cache key"""
    mock_client = Mock()
    mock_redis.return_value = mock_client

    cache = ScraperCache()

    key1 = cache._make_key("http://test.com", "prompt", model="qwen", schema="product")
    key2 = cache._make_key("http://test.com", "prompt", model="llama", schema="product")
    key3 = cache._make_key("http://test.com", "prompt", model="qwen", schema="article")

    # Different kwargs should produce different keys
    assert key1 != key2
    assert key1 != key3
    assert key2 != key3
