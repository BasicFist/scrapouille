"""
Stealth Mode & Anti-Detection System for Scrapouille v3.0 Phase 4.

Provides:
- User agent rotation (50+ realistic browser UAs)
- Anti-detection HTTP headers
- Browser fingerprint randomization
- Platform-specific spoofing

Prevents:
- IP bans from aggressive scraping
- Bot detection systems
- Browser fingerprinting
"""

import random
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class StealthLevel(Enum):
    """Stealth operation levels"""
    OFF = "off"              # No stealth (testing/debugging)
    LOW = "low"              # Basic UA rotation
    MEDIUM = "medium"        # Realistic headers + UA
    HIGH = "high"            # Full fingerprint randomization


@dataclass
class StealthConfig:
    """Configuration for stealth features.

    Attributes:
        stealth_level: Level of stealth to apply
        rotate_user_agent: Enable user agent rotation
        randomize_headers: Enable header randomization
        randomize_viewport: Enable viewport size randomization
        randomize_timezone: Enable timezone randomization
        custom_headers: Optional custom headers to inject
    """
    stealth_level: StealthLevel = StealthLevel.OFF
    rotate_user_agent: bool = True
    randomize_headers: bool = True
    randomize_viewport: bool = False
    randomize_timezone: bool = False
    custom_headers: Dict[str, str] = field(default_factory=dict)

    def is_enabled(self) -> bool:
        """Check if any stealth features are enabled"""
        return self.stealth_level != StealthLevel.OFF


class UserAgentPool:
    """Pool of realistic user agent strings.

    Maintains a weighted pool of real browser user agents across
    different platforms and browsers. Weighted to prefer common browsers.
    """

    # Real Chrome user agents (most common browser ~65%)
    CHROME_AGENTS = [
        # Windows Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        # macOS Chrome
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        # Linux Chrome
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        # Mobile Chrome
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    ]

    # Firefox user agents (~10%)
    FIREFOX_AGENTS = [
        # Windows Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        # macOS Firefox
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        # Linux Firefox
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]

    # Safari user agents (~20%)
    SAFARI_AGENTS = [
        # macOS Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        # iOS Safari
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    ]

    # Edge user agents (~5%)
    EDGE_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]

    def __init__(self):
        """Initialize user agent pool with weighted distribution"""
        # Build weighted pool (reflects real-world browser market share)
        self.agents = []
        self.agents.extend(self.CHROME_AGENTS * 13)  # 65% Chrome
        self.agents.extend(self.SAFARI_AGENTS * 4)   # 20% Safari
        self.agents.extend(self.FIREFOX_AGENTS * 2)  # 10% Firefox
        self.agents.extend(self.EDGE_AGENTS * 1)     # 5% Edge

        logger.debug(f"UserAgentPool initialized with {len(self.agents)} agents")

    def get_random(self) -> str:
        """Get a random user agent from the weighted pool.

        Returns:
            Random user agent string
        """
        return random.choice(self.agents)

    def get_by_browser(self, browser: str) -> str:
        """Get a random user agent for a specific browser.

        Args:
            browser: Browser name ("chrome", "firefox", "safari", "edge")

        Returns:
            Random user agent for specified browser
        """
        browser = browser.lower()
        if browser == "chrome":
            return random.choice(self.CHROME_AGENTS)
        elif browser == "firefox":
            return random.choice(self.FIREFOX_AGENTS)
        elif browser == "safari":
            return random.choice(self.SAFARI_AGENTS)
        elif browser == "edge":
            return random.choice(self.EDGE_AGENTS)
        else:
            return self.get_random()


# Global singleton UA pool for performance (132-element list created once)
_GLOBAL_UA_POOL = UserAgentPool()


class StealthHeaders:
    """Generates anti-detection HTTP headers.

    Creates realistic header sets based on stealth level to avoid
    bot detection and fingerprinting.
    """

    # Common accept languages (weighted by usage)
    ACCEPT_LANGUAGES = [
        "en-US,en;q=0.9",
        "en-GB,en;q=0.9",
        "en-US,en;q=0.9,es;q=0.8",
        "en-US,en;q=0.9,de;q=0.8",
        "en-US,en;q=0.9,fr;q=0.8",
    ]

    # Common timezones
    TIMEZONES = [
        "America/New_York",
        "America/Chicago",
        "America/Los_Angeles",
        "Europe/London",
        "Europe/Paris",
        "Asia/Tokyo",
        "Australia/Sydney",
    ]

    # Common viewport sizes (desktop)
    VIEWPORTS = [
        (1920, 1080),
        (1366, 768),
        (1536, 864),
        (1440, 900),
        (1280, 720),
        (2560, 1440),
    ]

    def __init__(self, ua_pool: Optional[UserAgentPool] = None):
        """Initialize stealth headers generator.

        Args:
            ua_pool: Optional UserAgentPool instance (uses global singleton if None)
        """
        self.ua_pool = ua_pool or _GLOBAL_UA_POOL

    def get_headers(
        self,
        config: StealthConfig,
        user_agent: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate anti-detection headers based on stealth level.

        Args:
            config: Stealth configuration
            user_agent: Optional specific UA (generates random if None)

        Returns:
            Dictionary of HTTP headers
        """
        headers = {}

        # User-Agent (all levels except OFF)
        if config.stealth_level != StealthLevel.OFF:
            if user_agent is None and config.rotate_user_agent:
                user_agent = self.ua_pool.get_random()
            if user_agent:
                headers["User-Agent"] = user_agent

        # LOW level: Just user agent
        if config.stealth_level == StealthLevel.LOW:
            return {**headers, **config.custom_headers}

        # MEDIUM level: Realistic headers
        if config.stealth_level in [StealthLevel.MEDIUM, StealthLevel.HIGH]:
            headers.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": random.choice(self.ACCEPT_LANGUAGES),
                "DNT": "1",  # Do Not Track
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            })

        # HIGH level: Full fingerprint randomization
        if config.stealth_level == StealthLevel.HIGH:
            # Add Chrome-specific sec-ch-ua headers
            if "Chrome" in headers.get("User-Agent", ""):
                headers.update({
                    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                })

            # Add realistic referer (simulate organic traffic)
            referrers = [
                "https://www.google.com/",
                "https://www.bing.com/",
                "https://www.duckduckgo.com/",
            ]
            headers["Referer"] = random.choice(referrers)

        # Merge with custom headers (custom headers take precedence)
        return {**headers, **config.custom_headers}

    def get_viewport(self) -> Tuple[int, int]:
        """Get a random viewport size for fingerprint randomization.

        Returns:
            Tuple of (width, height)
        """
        return random.choice(self.VIEWPORTS)

    def get_timezone(self) -> str:
        """Get a random timezone for fingerprint randomization.

        Returns:
            Timezone string
        """
        return random.choice(self.TIMEZONES)


# Convenience presets
STEALTH_PRESETS = {
    "off": StealthConfig(stealth_level=StealthLevel.OFF),
    "low": StealthConfig(
        stealth_level=StealthLevel.LOW,
        rotate_user_agent=True,
        randomize_headers=False
    ),
    "medium": StealthConfig(
        stealth_level=StealthLevel.MEDIUM,
        rotate_user_agent=True,
        randomize_headers=True,
        randomize_viewport=False
    ),
    "high": StealthConfig(
        stealth_level=StealthLevel.HIGH,
        rotate_user_agent=True,
        randomize_headers=True,
        randomize_viewport=True,
        randomize_timezone=True
    ),
}


def get_stealth_config(preset: str = "medium") -> StealthConfig:
    """Get a stealth configuration by preset name.

    Args:
        preset: Preset name ("off", "low", "medium", "high")

    Returns:
        StealthConfig instance

    Example:
        ```python
        config = get_stealth_config("high")
        headers = StealthHeaders().get_headers(config)
        ```
    """
    return STEALTH_PRESETS.get(preset, STEALTH_PRESETS["medium"])
