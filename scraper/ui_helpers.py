"""
UI Helper Utilities

Common utility functions used across Streamlit and Terminal UIs.
Reduces code duplication and centralizes business logic.

Version: Scrapouille v3.0 Phase 4
"""

from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime

from .fallback import ModelConfig, DEFAULT_FALLBACK_CHAIN


def build_fallback_chain(primary_model: str) -> List[ModelConfig]:
    """
    Build deduplicated fallback chain with primary model first

    Constructs a fallback chain starting with the specified primary model,
    followed by default fallback models, removing any duplicates while
    preserving order.

    Args:
        primary_model: Name of the primary model (e.g., "qwen2.5-coder:7b")

    Returns:
        List of ModelConfig objects with primary model first, no duplicates

    Example:
        >>> chain = build_fallback_chain("qwen2.5-coder:7b")
        >>> [m.name for m in chain]
        ['qwen2.5-coder:7b', 'llama3.1', 'deepseek-coder-v2']

        >>> chain = build_fallback_chain("llama3.1")  # llama3.1 already in defaults
        >>> [m.name for m in chain]
        ['llama3.1', 'qwen2.5-coder:7b', 'deepseek-coder-v2']
    """
    # Start with primary model
    primary = ModelConfig(name=primary_model)
    chain = [primary] + DEFAULT_FALLBACK_CHAIN

    # Remove duplicates while preserving order
    seen = set()
    unique_chain = []
    for model_config in chain:
        if model_config.name not in seen:
            seen.add(model_config.name)
            unique_chain.append(model_config)

    return unique_chain


def format_execution_time(seconds: float) -> str:
    """
    Format execution time in human-readable format

    Args:
        seconds: Execution time in seconds

    Returns:
        Formatted string (e.g., "2.5s", "1m 30s", "1h 5m")

    Examples:
        >>> format_execution_time(2.5)
        "2.5s"
        >>> format_execution_time(90)
        "1m 30s"
        >>> format_execution_time(3665)
        "1h 1m 5s"
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        remaining_seconds = int(seconds % 60)
        return f"{hours}h {minutes}m {remaining_seconds}s"


def format_timestamp(dt: datetime) -> str:
    """
    Format datetime for display in UI

    Args:
        dt: Datetime object

    Returns:
        Formatted string (e.g., "2025-11-11 14:30")

    Example:
        >>> from datetime import datetime
        >>> dt = datetime(2025, 11, 11, 14, 30, 45)
        >>> format_timestamp(dt)
        "2025-11-11 14:30"
    """
    return dt.strftime("%Y-%m-%d %H:%M")


def calculate_success_rate(successful: int, total: int) -> float:
    """
    Calculate success rate as percentage

    Args:
        successful: Number of successful operations
        total: Total number of operations

    Returns:
        Success rate as percentage (0-100)

    Example:
        >>> calculate_success_rate(8, 10)
        80.0
        >>> calculate_success_rate(0, 0)
        0.0
    """
    if total == 0:
        return 0.0
    return (successful / total) * 100


def truncate_url(url: str, max_length: int = 50) -> str:
    """
    Truncate URL for display with ellipsis

    Args:
        url: URL to truncate
        max_length: Maximum length (default: 50)

    Returns:
        Truncated URL with "..." if too long

    Example:
        >>> truncate_url("https://example.com/very/long/path/to/page", 30)
        "https://example.com/very/lo..."
    """
    if len(url) <= max_length:
        return url
    return url[:max_length - 3] + "..."


def deduplicate_urls(urls: List[str]) -> List[str]:
    """
    Remove duplicate URLs while preserving order

    Args:
        urls: List of URLs (may contain duplicates)

    Returns:
        List of unique URLs in original order

    Example:
        >>> deduplicate_urls(["http://a.com", "http://b.com", "http://a.com"])
        ["http://a.com", "http://b.com"]
    """
    seen = set()
    unique_urls = []
    for url in urls:
        url_stripped = url.strip()
        if url_stripped and url_stripped not in seen:
            seen.add(url_stripped)
            unique_urls.append(url_stripped)
    return unique_urls


def parse_urls_from_text(text: str) -> List[str]:
    """
    Parse URLs from text (one per line)

    Args:
        text: Text containing URLs separated by newlines

    Returns:
        List of URLs (empty lines removed, deduplicated)

    Example:
        >>> parse_urls_from_text("http://a.com\\n\\nhttp://b.com\\nhttp://a.com")
        ["http://a.com", "http://b.com"]
    """
    urls = [line.strip() for line in text.split('\n') if line.strip()]
    return deduplicate_urls(urls)
