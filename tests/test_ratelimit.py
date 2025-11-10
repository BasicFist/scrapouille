"""
Unit tests for Rate Limiting System
Tests ethical scraping rate limits and delays
"""
import pytest
import time
from datetime import datetime
from scraper.ratelimit import RateLimiter, RateLimitConfig, RATE_LIMIT_PRESETS


def test_rate_limit_config_defaults():
    """Test RateLimitConfig default values"""
    config = RateLimitConfig()
    assert config.requests_per_second == 0.5
    assert config.min_delay_seconds == 2.0
    assert config.max_delay_seconds == 5.0


def test_rate_limit_config_get_delay():
    """Test get_delay returns value within min/max bounds"""
    config = RateLimitConfig(
        requests_per_second=0.5,
        min_delay_seconds=2.0,
        max_delay_seconds=5.0
    )

    # Test multiple times due to jitter randomness
    for _ in range(10):
        delay = config.get_delay()
        assert delay >= 2.0
        assert delay <= 5.0


def test_rate_limit_config_custom_values():
    """Test RateLimitConfig with custom values"""
    config = RateLimitConfig(
        requests_per_second=1.0,
        min_delay_seconds=1.0,
        max_delay_seconds=2.0
    )
    assert config.requests_per_second == 1.0
    assert config.min_delay_seconds == 1.0


def test_rate_limiter_first_request_no_delay():
    """Test first request has no delay"""
    limiter = RateLimiter()

    start = time.time()
    delay = limiter.wait()
    elapsed = time.time() - start

    assert delay == 0.0
    assert elapsed < 0.1  # Should be instant


def test_rate_limiter_enforces_delay():
    """Test rate limiter waits minimum delay"""
    config = RateLimitConfig(min_delay_seconds=1.0, max_delay_seconds=1.5)
    limiter = RateLimiter(config)

    # First request
    limiter.wait()

    # Second request should wait ~1 second
    start = time.time()
    delay = limiter.wait()
    elapsed = time.time() - start

    assert delay >= 1.0
    assert elapsed >= 0.9  # Allow small timing variance


def test_rate_limiter_no_wait_if_enough_time_passed():
    """Test rate limiter doesn't wait if enough time has passed"""
    config = RateLimitConfig(min_delay_seconds=0.5)
    limiter = RateLimiter(config)

    # First request
    limiter.wait()

    # Wait longer than required delay
    time.sleep(0.6)

    # Second request should not wait
    start = time.time()
    delay = limiter.wait()
    elapsed = time.time() - start

    assert elapsed < 0.1  # Should be instant
    assert delay >= 0.5  # Delay tracks actual time since last request


def test_rate_limiter_tracks_request_count():
    """Test rate limiter tracks number of requests"""
    limiter = RateLimiter()

    assert limiter.request_count == 0

    limiter.wait()
    assert limiter.request_count == 1

    limiter.wait()
    assert limiter.request_count == 2


def test_rate_limiter_tracks_last_request_time():
    """Test rate limiter tracks last request timestamp"""
    limiter = RateLimiter()

    assert limiter.last_request_time is None

    before = datetime.now()
    limiter.wait()
    after = datetime.now()

    assert limiter.last_request_time is not None
    assert before <= limiter.last_request_time <= after


def test_rate_limiter_get_stats():
    """Test rate limiter statistics"""
    config = RateLimitConfig(min_delay_seconds=2.0)
    limiter = RateLimiter(config)

    limiter.wait()
    limiter.wait()

    stats = limiter.get_stats()

    assert stats['total_requests'] == 2
    assert stats['avg_delay'] >= 2.0
    assert stats['last_request'] is not None


def test_rate_limit_presets_exist():
    """Test all rate limit presets are defined"""
    assert "aggressive" in RATE_LIMIT_PRESETS
    assert "normal" in RATE_LIMIT_PRESETS
    assert "polite" in RATE_LIMIT_PRESETS
    assert "none" in RATE_LIMIT_PRESETS


def test_rate_limit_preset_aggressive():
    """Test aggressive preset configuration"""
    config = RATE_LIMIT_PRESETS["aggressive"]
    assert config.requests_per_second == 1.0
    assert config.min_delay_seconds == 1.0
    assert config.max_delay_seconds == 2.0


def test_rate_limit_preset_normal():
    """Test normal preset configuration"""
    config = RATE_LIMIT_PRESETS["normal"]
    assert config.requests_per_second == 0.5
    assert config.min_delay_seconds == 2.0
    assert config.max_delay_seconds == 4.0


def test_rate_limit_preset_polite():
    """Test polite preset configuration"""
    config = RATE_LIMIT_PRESETS["polite"]
    assert config.requests_per_second == 0.2
    assert config.min_delay_seconds == 5.0
    assert config.max_delay_seconds == 10.0


def test_rate_limit_preset_none():
    """Test none preset is None"""
    assert RATE_LIMIT_PRESETS["none"] is None


def test_rate_limiter_multiple_sequential_requests():
    """Test rate limiter with multiple sequential requests"""
    config = RateLimitConfig(min_delay_seconds=0.5, max_delay_seconds=0.6)
    limiter = RateLimiter(config)

    start = time.time()

    # Make 3 requests
    limiter.wait()  # No delay
    limiter.wait()  # ~0.5s delay
    limiter.wait()  # ~0.5s delay

    total_elapsed = time.time() - start

    # Should take at least 1 second (2 delays of 0.5s each)
    assert total_elapsed >= 0.9
    assert limiter.request_count == 3


def test_rate_limiter_jitter_variation():
    """Test rate limiter applies jitter (delays vary)"""
    config = RateLimitConfig(
        requests_per_second=1.0,
        min_delay_seconds=1.0,
        max_delay_seconds=2.0
    )

    delays = []
    for _ in range(5):
        limiter = RateLimiter(config)
        limiter.wait()  # First request
        limiter.wait()  # Get delay
        delays.append(limiter.config.get_delay())

    # Due to jitter, delays should vary
    # (This test might occasionally fail due to randomness, but very unlikely)
    assert len(set(delays)) > 1  # At least 2 different values


def test_rate_limiter_respects_config_changes():
    """Test rate limiter uses updated config"""
    config1 = RateLimitConfig(min_delay_seconds=1.0)
    limiter = RateLimiter(config1)

    assert limiter.config.min_delay_seconds == 1.0

    # Update config
    limiter.config = RateLimitConfig(min_delay_seconds=2.0)

    assert limiter.config.min_delay_seconds == 2.0
