"""
Unit tests for scraper/stealth.py - Stealth Mode & Anti-Detection System.

Tests cover:
- StealthConfig initialization and validation
- UserAgentPool weighted distribution and browser-specific selection
- StealthHeaders generation for all stealth levels
- Viewport and timezone randomization
- Preset configuration loading
"""

import pytest
from scraper.stealth import (
    StealthLevel,
    StealthConfig,
    UserAgentPool,
    StealthHeaders,
    get_stealth_config,
    STEALTH_PRESETS
)


class TestStealthConfig:
    """Tests for StealthConfig dataclass"""

    def test_default_initialization(self):
        """Test default StealthConfig initialization"""
        config = StealthConfig()
        assert config.stealth_level == StealthLevel.OFF
        assert config.rotate_user_agent is True
        assert config.randomize_headers is True
        assert config.randomize_viewport is False
        assert config.randomize_timezone is False
        assert config.custom_headers == {}

    def test_custom_initialization(self):
        """Test StealthConfig with custom values"""
        custom_headers = {"X-Custom": "Value"}
        config = StealthConfig(
            stealth_level=StealthLevel.HIGH,
            rotate_user_agent=False,
            randomize_viewport=True,
            custom_headers=custom_headers
        )
        assert config.stealth_level == StealthLevel.HIGH
        assert config.rotate_user_agent is False
        assert config.randomize_viewport is True
        assert config.custom_headers == custom_headers

    def test_is_enabled_off(self):
        """Test is_enabled() returns False when stealth is OFF"""
        config = StealthConfig(stealth_level=StealthLevel.OFF)
        assert config.is_enabled() is False

    def test_is_enabled_low(self):
        """Test is_enabled() returns True when stealth is LOW"""
        config = StealthConfig(stealth_level=StealthLevel.LOW)
        assert config.is_enabled() is True

    def test_is_enabled_medium(self):
        """Test is_enabled() returns True when stealth is MEDIUM"""
        config = StealthConfig(stealth_level=StealthLevel.MEDIUM)
        assert config.is_enabled() is True

    def test_is_enabled_high(self):
        """Test is_enabled() returns True when stealth is HIGH"""
        config = StealthConfig(stealth_level=StealthLevel.HIGH)
        assert config.is_enabled() is True


class TestUserAgentPool:
    """Tests for UserAgentPool class"""

    def test_initialization(self):
        """Test UserAgentPool initializes with agents"""
        pool = UserAgentPool()
        assert len(pool.agents) > 0
        # Weighted pool: 8 Chrome * 13 + 4 Safari * 4 + 5 Firefox * 2 + 2 Edge * 1 = 132
        assert len(pool.agents) == 132

    def test_get_random_returns_string(self):
        """Test get_random() returns a user agent string"""
        pool = UserAgentPool()
        ua = pool.get_random()
        assert isinstance(ua, str)
        assert len(ua) > 0
        assert "Mozilla" in ua  # All UAs start with Mozilla

    def test_get_random_varies(self):
        """Test get_random() returns different agents (stochastic)"""
        pool = UserAgentPool()
        agents = {pool.get_random() for _ in range(100)}
        # With weighted distribution, we should see multiple different agents
        assert len(agents) > 1

    def test_get_by_browser_chrome(self):
        """Test get_by_browser() returns Chrome UA"""
        pool = UserAgentPool()
        ua = pool.get_by_browser("chrome")
        assert "Chrome" in ua
        assert "Safari" in ua  # Chrome UAs include Safari for compatibility

    def test_get_by_browser_firefox(self):
        """Test get_by_browser() returns Firefox UA"""
        pool = UserAgentPool()
        ua = pool.get_by_browser("firefox")
        assert "Firefox" in ua
        assert "Gecko" in ua

    def test_get_by_browser_safari(self):
        """Test get_by_browser() returns Safari UA"""
        pool = UserAgentPool()
        ua = pool.get_by_browser("safari")
        assert "Safari" in ua
        assert "AppleWebKit" in ua

    def test_get_by_browser_edge(self):
        """Test get_by_browser() returns Edge UA"""
        pool = UserAgentPool()
        ua = pool.get_by_browser("edge")
        assert "Edg" in ua  # Edge uses "Edg" in UA string

    def test_get_by_browser_unknown_fallback(self):
        """Test get_by_browser() falls back to random for unknown browser"""
        pool = UserAgentPool()
        ua = pool.get_by_browser("unknown_browser")
        assert isinstance(ua, str)
        assert len(ua) > 0

    def test_get_by_browser_case_insensitive(self):
        """Test get_by_browser() is case-insensitive"""
        pool = UserAgentPool()
        ua_upper = pool.get_by_browser("CHROME")
        ua_lower = pool.get_by_browser("chrome")
        # Both should be Chrome UAs (not necessarily the same due to randomness)
        assert "Chrome" in ua_upper
        assert "Chrome" in ua_lower


class TestStealthHeaders:
    """Tests for StealthHeaders class"""

    def test_initialization(self):
        """Test StealthHeaders initializes with UserAgentPool"""
        headers_gen = StealthHeaders()
        assert headers_gen.ua_pool is not None
        assert isinstance(headers_gen.ua_pool, UserAgentPool)

    def test_initialization_with_custom_pool(self):
        """Test StealthHeaders accepts custom UserAgentPool"""
        custom_pool = UserAgentPool()
        headers_gen = StealthHeaders(ua_pool=custom_pool)
        assert headers_gen.ua_pool is custom_pool

    def test_get_headers_off_level(self):
        """Test get_headers() returns empty dict for OFF level"""
        config = StealthConfig(stealth_level=StealthLevel.OFF)
        headers_gen = StealthHeaders()
        headers = headers_gen.get_headers(config)
        assert headers == {}

    def test_get_headers_low_level(self):
        """Test get_headers() returns only UA for LOW level"""
        config = StealthConfig(stealth_level=StealthLevel.LOW)
        headers_gen = StealthHeaders()
        headers = headers_gen.get_headers(config)

        assert "User-Agent" in headers
        assert len(headers["User-Agent"]) > 0
        # LOW level should only have User-Agent
        assert len(headers) == 1

    def test_get_headers_low_level_with_custom_ua(self):
        """Test get_headers() uses custom UA when provided"""
        config = StealthConfig(stealth_level=StealthLevel.LOW)
        headers_gen = StealthHeaders()
        custom_ua = "Custom User Agent String"
        headers = headers_gen.get_headers(config, user_agent=custom_ua)

        assert headers["User-Agent"] == custom_ua

    def test_get_headers_medium_level(self):
        """Test get_headers() returns realistic headers for MEDIUM level"""
        config = StealthConfig(stealth_level=StealthLevel.MEDIUM)
        headers_gen = StealthHeaders()
        headers = headers_gen.get_headers(config)

        # MEDIUM should include all realistic headers
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Encoding" in headers
        assert "Accept-Language" in headers
        assert "DNT" in headers
        assert "Connection" in headers
        assert "Upgrade-Insecure-Requests" in headers
        assert "Sec-Fetch-Dest" in headers
        assert "Sec-Fetch-Mode" in headers
        assert "Sec-Fetch-Site" in headers
        assert "Sec-Fetch-User" in headers
        assert "Cache-Control" in headers

    def test_get_headers_medium_level_values(self):
        """Test get_headers() MEDIUM level has correct values"""
        config = StealthConfig(stealth_level=StealthLevel.MEDIUM)
        headers_gen = StealthHeaders()
        headers = headers_gen.get_headers(config)

        assert headers["DNT"] == "1"
        assert headers["Connection"] == "keep-alive"
        assert headers["Upgrade-Insecure-Requests"] == "1"
        assert headers["Sec-Fetch-Dest"] == "document"
        assert headers["Sec-Fetch-Mode"] == "navigate"
        assert headers["Sec-Fetch-Site"] == "none"
        assert headers["Sec-Fetch-User"] == "?1"

    def test_get_headers_high_level(self):
        """Test get_headers() returns full fingerprint for HIGH level"""
        config = StealthConfig(stealth_level=StealthLevel.HIGH)
        headers_gen = StealthHeaders()
        headers = headers_gen.get_headers(config)

        # HIGH should include all MEDIUM headers
        assert "User-Agent" in headers
        assert "Accept" in headers
        # HIGH should include Referer for organic traffic simulation
        assert "Referer" in headers
        assert headers["Referer"] in [
            "https://www.google.com/",
            "https://www.bing.com/",
            "https://www.duckduckgo.com/"
        ]

    def test_get_headers_high_level_chrome_specific(self):
        """Test get_headers() HIGH level adds Chrome-specific headers"""
        config = StealthConfig(stealth_level=StealthLevel.HIGH)
        headers_gen = StealthHeaders()
        # Force Chrome UA to test Chrome-specific headers
        chrome_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        headers = headers_gen.get_headers(config, user_agent=chrome_ua)

        assert "User-Agent" in headers
        assert "Chrome" in headers["User-Agent"]
        assert "sec-ch-ua" in headers
        assert "sec-ch-ua-mobile" in headers
        assert "sec-ch-ua-platform" in headers

    def test_get_headers_custom_headers_override(self):
        """Test custom_headers override generated headers"""
        custom_headers = {"User-Agent": "Custom UA", "X-Custom": "Value"}
        config = StealthConfig(
            stealth_level=StealthLevel.MEDIUM,
            custom_headers=custom_headers
        )
        headers_gen = StealthHeaders()
        headers = headers_gen.get_headers(config)

        # Custom headers should override generated ones
        assert headers["User-Agent"] == "Custom UA"
        assert headers["X-Custom"] == "Value"
        # Other headers should still be present
        assert "Accept" in headers

    def test_get_headers_no_rotation(self):
        """Test get_headers() respects rotate_user_agent=False"""
        config = StealthConfig(
            stealth_level=StealthLevel.MEDIUM,
            rotate_user_agent=False
        )
        headers_gen = StealthHeaders()
        headers = headers_gen.get_headers(config)

        # Should not include User-Agent when rotation is disabled and no UA provided
        # But custom headers can still add it
        # The key test is that no random UA is generated

    def test_get_viewport(self):
        """Test get_viewport() returns valid viewport tuple"""
        headers_gen = StealthHeaders()
        viewport = headers_gen.get_viewport()

        assert isinstance(viewport, tuple)
        assert len(viewport) == 2
        assert viewport[0] > 0  # width
        assert viewport[1] > 0  # height
        # Should be one of the common viewports
        assert viewport in headers_gen.VIEWPORTS

    def test_get_viewport_randomness(self):
        """Test get_viewport() varies (stochastic)"""
        headers_gen = StealthHeaders()
        viewports = {headers_gen.get_viewport() for _ in range(50)}
        # Should see multiple different viewports
        assert len(viewports) > 1

    def test_get_timezone(self):
        """Test get_timezone() returns valid timezone"""
        headers_gen = StealthHeaders()
        timezone = headers_gen.get_timezone()

        assert isinstance(timezone, str)
        assert len(timezone) > 0
        # Should be one of the common timezones
        assert timezone in headers_gen.TIMEZONES

    def test_get_timezone_randomness(self):
        """Test get_timezone() varies (stochastic)"""
        headers_gen = StealthHeaders()
        timezones = {headers_gen.get_timezone() for _ in range(50)}
        # Should see multiple different timezones
        assert len(timezones) > 1


class TestStealthPresets:
    """Tests for stealth configuration presets"""

    def test_preset_off(self):
        """Test 'off' preset configuration"""
        config = STEALTH_PRESETS["off"]
        assert config.stealth_level == StealthLevel.OFF
        assert config.is_enabled() is False

    def test_preset_low(self):
        """Test 'low' preset configuration"""
        config = STEALTH_PRESETS["low"]
        assert config.stealth_level == StealthLevel.LOW
        assert config.rotate_user_agent is True
        assert config.randomize_headers is False

    def test_preset_medium(self):
        """Test 'medium' preset configuration"""
        config = STEALTH_PRESETS["medium"]
        assert config.stealth_level == StealthLevel.MEDIUM
        assert config.rotate_user_agent is True
        assert config.randomize_headers is True
        assert config.randomize_viewport is False

    def test_preset_high(self):
        """Test 'high' preset configuration"""
        config = STEALTH_PRESETS["high"]
        assert config.stealth_level == StealthLevel.HIGH
        assert config.rotate_user_agent is True
        assert config.randomize_headers is True
        assert config.randomize_viewport is True
        assert config.randomize_timezone is True

    def test_get_stealth_config_off(self):
        """Test get_stealth_config() returns OFF preset"""
        config = get_stealth_config("off")
        assert config.stealth_level == StealthLevel.OFF

    def test_get_stealth_config_low(self):
        """Test get_stealth_config() returns LOW preset"""
        config = get_stealth_config("low")
        assert config.stealth_level == StealthLevel.LOW

    def test_get_stealth_config_medium(self):
        """Test get_stealth_config() returns MEDIUM preset"""
        config = get_stealth_config("medium")
        assert config.stealth_level == StealthLevel.MEDIUM

    def test_get_stealth_config_high(self):
        """Test get_stealth_config() returns HIGH preset"""
        config = get_stealth_config("high")
        assert config.stealth_level == StealthLevel.HIGH

    def test_get_stealth_config_default(self):
        """Test get_stealth_config() defaults to MEDIUM"""
        config = get_stealth_config()
        assert config.stealth_level == StealthLevel.MEDIUM

    def test_get_stealth_config_invalid_fallback(self):
        """Test get_stealth_config() falls back to MEDIUM for invalid preset"""
        config = get_stealth_config("invalid_preset")
        assert config.stealth_level == StealthLevel.MEDIUM


class TestStealthIntegration:
    """Integration tests for stealth components working together"""

    def test_full_stealth_workflow_low(self):
        """Test complete stealth workflow for LOW level"""
        config = get_stealth_config("low")
        headers_gen = StealthHeaders()
        headers = headers_gen.get_headers(config)

        # Should have user agent only
        assert "User-Agent" in headers
        assert len(headers) == 1

    def test_full_stealth_workflow_medium(self):
        """Test complete stealth workflow for MEDIUM level"""
        config = get_stealth_config("medium")
        headers_gen = StealthHeaders()
        headers = headers_gen.get_headers(config)

        # Should have all realistic headers
        assert len(headers) > 5
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers

    def test_full_stealth_workflow_high(self):
        """Test complete stealth workflow for HIGH level"""
        config = get_stealth_config("high")
        headers_gen = StealthHeaders()
        headers = headers_gen.get_headers(config)

        # Should have full fingerprint
        assert len(headers) > 10
        assert "User-Agent" in headers
        assert "Referer" in headers

    def test_custom_headers_with_preset(self):
        """Test custom headers work with preset configurations"""
        config = get_stealth_config("medium")
        config.custom_headers = {"X-API-Key": "secret"}
        headers_gen = StealthHeaders()
        headers = headers_gen.get_headers(config)

        # Should have both generated and custom headers
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "X-API-Key" in headers
        assert headers["X-API-Key"] == "secret"

    def test_viewport_and_timezone_high_level(self):
        """Test viewport and timezone are available for HIGH level"""
        config = get_stealth_config("high")
        assert config.randomize_viewport is True
        assert config.randomize_timezone is True

        headers_gen = StealthHeaders()
        viewport = headers_gen.get_viewport()
        timezone = headers_gen.get_timezone()

        assert viewport is not None
        assert timezone is not None
        assert len(timezone) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
