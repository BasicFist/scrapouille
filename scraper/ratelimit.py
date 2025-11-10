"""
Rate limiting utilities for ethical web scraping
Prevents overwhelming target servers and IP bans
"""
import time
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_second: float = 0.5  # Max 1 request per 2 seconds (default)
    min_delay_seconds: float = 2.0    # Minimum delay between requests
    max_delay_seconds: float = 5.0    # Maximum delay (for jitter)

    def get_delay(self) -> float:
        """Get delay to use (includes jitter)"""
        import random
        # Add random jitter (±20%) to avoid patterns
        delay = 1.0 / self.requests_per_second if self.requests_per_second > 0 else self.min_delay_seconds
        jitter = random.uniform(0.8, 1.2)
        actual_delay = delay * jitter

        # Clamp to min/max
        return max(self.min_delay_seconds, min(actual_delay, self.max_delay_seconds))


class RateLimiter:
    """
    Simple rate limiter with adaptive delays

    Example:
        limiter = RateLimiter(config)
        limiter.wait()  # Blocks until safe to proceed
    """

    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.last_request_time: Optional[datetime] = None
        self.request_count = 0

    def wait(self) -> float:
        """
        Wait until safe to make next request

        Returns:
            float: Actual delay waited (seconds)
        """
        if self.last_request_time is None:
            # First request, no delay
            self.last_request_time = datetime.now()
            self.request_count += 1
            return 0.0

        # Calculate required delay
        required_delay = self.config.get_delay()

        # Calculate time since last request
        elapsed = (datetime.now() - self.last_request_time).total_seconds()

        # Wait if needed
        if elapsed < required_delay:
            wait_time = required_delay - elapsed
            logger.info(f"Rate limit: waiting {wait_time:.2f}s")
            time.sleep(wait_time)
            actual_delay = required_delay
        else:
            actual_delay = elapsed

        # Update tracking
        self.last_request_time = datetime.now()
        self.request_count += 1

        return actual_delay

    def get_stats(self) -> dict:
        """Get rate limiter statistics"""
        return {
            'total_requests': self.request_count,
            'avg_delay': self.config.get_delay(),
            'last_request': self.last_request_time.isoformat() if self.last_request_time else None,
        }


# Preset configurations
RATE_LIMIT_PRESETS = {
    "aggressive": RateLimitConfig(
        requests_per_second=1.0,
        min_delay_seconds=1.0,
        max_delay_seconds=2.0
    ),
    "normal": RateLimitConfig(
        requests_per_second=0.5,
        min_delay_seconds=2.0,
        max_delay_seconds=4.0
    ),
    "polite": RateLimitConfig(
        requests_per_second=0.2,
        min_delay_seconds=5.0,
        max_delay_seconds=10.0
    ),
    "none": None,  # Disable rate limiting
}
