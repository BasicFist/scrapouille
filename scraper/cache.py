"""
Redis-based caching for scraping results
Dramatically reduces LLM costs and response times
"""
import redis
import json
import hashlib
from typing import Optional, Any
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class ScraperCache:
    """
    Redis-based cache for scraping results

    Example:
        cache = ScraperCache()
        result = cache.get(url, prompt)
        if result is None:
            result = expensive_scrape()
            cache.set(url, prompt, result, ttl_hours=24)
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        enabled: bool = True,
        default_ttl_hours: int = 24
    ):
        self.enabled = enabled
        self.default_ttl_hours = default_ttl_hours

        if not enabled:
            self.client = None
            logger.info("Cache disabled")
            return

        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=2
            )
            # Test connection
            self.client.ping()
            logger.info(f"✓ Connected to Redis at {host}:{port}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Cache disabled.")
            self.client = None
            self.enabled = False

    def _make_key(self, url: str, prompt: str, **kwargs) -> str:
        """
        Generate cache key from URL + prompt + kwargs

        Returns:
            str: "scrape:<hash>"
        """
        # Combine all inputs
        key_data = {
            'url': url,
            'prompt': prompt,
            **kwargs
        }
        # Create deterministic hash
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_str.encode()).hexdigest()[:16]

        return f"scrape:{key_hash}"

    def get(self, url: str, prompt: str, **kwargs) -> Optional[dict]:
        """
        Get cached result

        Args:
            url: Target URL
            prompt: Scraping prompt
            **kwargs: Additional parameters (model, schema, etc.)

        Returns:
            Cached result dict or None if not found
        """
        if not self.enabled or self.client is None:
            return None

        try:
            key = self._make_key(url, prompt, **kwargs)
            cached = self.client.get(key)

            if cached:
                logger.info(f"✓ Cache HIT: {key}")
                return json.loads(cached)
            else:
                logger.info(f"✗ Cache MISS: {key}")
                return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(
        self,
        url: str,
        prompt: str,
        result: Any,
        ttl_hours: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        Cache a scraping result

        Args:
            url: Target URL
            prompt: Scraping prompt
            result: Scraping result to cache
            ttl_hours: Time-to-live in hours (default: 24)
            **kwargs: Additional parameters for key generation

        Returns:
            bool: True if cached successfully
        """
        if not self.enabled or self.client is None:
            return False

        try:
            key = self._make_key(url, prompt, **kwargs)
            ttl = ttl_hours or self.default_ttl_hours

            # Serialize result
            cached_data = json.dumps(result)

            # Set with TTL
            self.client.setex(
                key,
                timedelta(hours=ttl),
                cached_data
            )

            logger.info(f"✓ Cached result: {key} (TTL: {ttl}h)")
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.enabled or self.client is None:
            return {'enabled': False}

        try:
            info = self.client.info('stats')
            return {
                'enabled': True,
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_keys': self.client.dbsize(),
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'enabled': False, 'error': str(e)}

    def clear_all(self) -> bool:
        """Clear all cached results (use with caution!)"""
        if not self.enabled or self.client is None:
            return False

        try:
            # Only clear keys with our prefix
            pattern = "scrape:*"
            keys = list(self.client.scan_iter(match=pattern))
            if keys:
                self.client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cached results")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
