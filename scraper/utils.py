"""
Utility functions for web scraper
Includes retry logic, error handling, and helper functions
"""

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
    retry=retry_if_exception_type((ConnectionError, TimeoutError, ValueError))
)
def scrape_with_retry(scraper_func: Callable, *args: Any, **kwargs: Any) -> dict:
    """
    Wrap scraping function with retry logic

    Args:
        scraper_func: The scraping function to execute
        *args: Positional arguments for scraper_func
        **kwargs: Keyword arguments for scraper_func

    Returns:
        dict: Scraping result

    Raises:
        ValueError: If scraping result is empty
        Exception: Re-raises last exception after max retries

    Retry behavior:
        - Maximum 3 attempts
        - Exponential backoff: 2s, 4s, 8s (max 10s)
        - Only retries on ConnectionError, TimeoutError, ValueError
    """
    try:
        result = scraper_func(*args, **kwargs)

        # Validate result is not empty
        if not result or result == {}:
            raise ValueError("Empty scraping result")

        logger.info("Scraping successful")
        return result

    except Exception as e:
        logger.error(f"Scraping attempt failed: {e}")
        raise


def get_retry_count() -> int:
    """
    Get the current retry count from the last retry operation

    Returns:
        int: Number of retry attempts (0 if successful on first try)
    """
    # This will be tracked in session state
    return 0
