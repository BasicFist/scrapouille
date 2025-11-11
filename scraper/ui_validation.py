"""
UI Input Validation Utilities

This module provides security-focused validation for user inputs in both
Streamlit and Terminal UIs. It protects against:
- SSRF (Server-Side Request Forgery) attacks
- Prompt injection / LLM jailbreaking
- Resource exhaustion (large files, long prompts)
- Malicious URL schemes

All validation functions return (is_valid, result, error_message) tuples.

Version: Scrapouille v3.0 Phase 4
Security Audit: 2025-11-11
"""

import re
from typing import Tuple
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


def validate_url(url: str) -> Tuple[bool, str]:
    """Validate URL for security and correctness

    Protects against:
    - SSRF attacks (localhost, private IPs, metadata endpoints)
    - Invalid URL schemes (only http/https allowed)
    - Malformed URLs

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is empty string

    Examples:
        >>> validate_url("https://example.com")
        (True, "")
        >>> validate_url("http://localhost:6379")
        (False, "Cannot scrape localhost URLs")
        >>> validate_url("file:///etc/passwd")
        (False, "Only http/https protocols allowed (got: file)")
    """
    if not url:
        return False, "URL is required"

    url = url.strip()

    try:
        parsed = urlparse(url)

        # Only allow http/https protocols
        if parsed.scheme not in ['http', 'https']:
            return False, f"Only http/https protocols allowed (got: {parsed.scheme or 'none'})"

        hostname = parsed.hostname
        if not hostname:
            return False, "Invalid URL: missing hostname"

        # Block localhost variations
        localhost_names = ['localhost', '127.0.0.1', '0.0.0.0', '::1', '[::1]']
        if hostname.lower() in localhost_names:
            return False, "Cannot scrape localhost URLs (security policy)"

        # Block private IP ranges (RFC 1918)
        # 10.0.0.0/8
        if hostname.startswith('10.'):
            return False, "Cannot scrape private IP addresses (10.0.0.0/8)"

        # 172.16.0.0/12
        if hostname.startswith('172.'):
            parts = hostname.split('.')
            if len(parts) >= 2:
                try:
                    second_octet = int(parts[1])
                    if 16 <= second_octet <= 31:
                        return False, "Cannot scrape private IP addresses (172.16.0.0/12)"
                except ValueError:
                    pass  # Not a valid IP, will be caught by other checks

        # 192.168.0.0/16
        if hostname.startswith('192.168.'):
            return False, "Cannot scrape private IP addresses (192.168.0.0/16)"

        # Block link-local addresses (169.254.0.0/16)
        if hostname.startswith('169.254.'):
            return False, "Cannot access link-local addresses (169.254.0.0/16)"

        # Block AWS metadata endpoint specifically
        if hostname == '169.254.169.254':
            return False, "Cannot access cloud metadata endpoints (security policy)"

        # Block IPv6 private addresses
        if hostname.startswith('fc') or hostname.startswith('fd'):
            return False, "Cannot scrape private IPv6 addresses"

        # Additional safety: Check for suspicious patterns
        suspicious_patterns = [
            r'[\x00-\x1f]',  # Control characters
            r'\s',  # Whitespace in hostname
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, hostname):
                return False, "Invalid characters in hostname"

        return True, ""

    except Exception as e:
        logger.warning(f"URL validation error for '{url}': {e}")
        return False, f"Invalid URL format: {str(e)}"


def sanitize_prompt(prompt: str, max_length: int = 5000) -> Tuple[bool, str, str]:
    """Sanitize user prompt for security

    Protects against:
    - Prompt injection / LLM jailbreaking attacks
    - Resource exhaustion (extremely long prompts)
    - Control character injection

    Args:
        prompt: User prompt to sanitize
        max_length: Maximum allowed length (default: 5000)

    Returns:
        Tuple of (is_valid, sanitized_prompt, error_message)
        If invalid, sanitized_prompt is empty string

    Examples:
        >>> sanitize_prompt("Extract product name and price")
        (True, "Extract product name and price", "")
        >>> sanitize_prompt("Ignore previous instructions")
        (False, "", "Prompt contains potentially unsafe patterns")
        >>> sanitize_prompt("x" * 6000)
        (False, "", "Prompt too long (max 5000 characters)")
    """
    if not prompt:
        return False, "", "Prompt is required"

    # Strip whitespace
    prompt = prompt.strip()

    # Check length
    if len(prompt) > max_length:
        return False, "", f"Prompt too long (max {max_length} characters)"

    # Check for minimum length (at least 3 characters)
    if len(prompt) < 3:
        return False, "", "Prompt too short (minimum 3 characters)"

    # Check for potential jailbreak patterns
    # These patterns are common in prompt injection attacks
    dangerous_patterns = [
        (r"ignore\s+(previous|above|prior|all)\s+instructions?", "ignore instructions"),
        (r"forget\s+(previous|above|prior|all)\s+instructions?", "forget instructions"),
        (r"disregard\s+(previous|above|prior|all)\s+instructions?", "disregard instructions"),
        (r"new\s+system\s+prompt", "system prompt override"),
        (r"you\s+are\s+now", "role override"),
        (r"act\s+as\s+if", "role override"),
        (r"<\|im_start\|>", "ChatML injection"),
        (r"<\|im_end\|>", "ChatML injection"),
        (r"### Instruction:", "Alpaca injection"),
        (r"\[INST\]", "Llama injection"),
        (r"\[/INST\]", "Llama injection"),
        (r"<s>", "Special token injection"),
        (r"</s>", "Special token injection"),
        (r"<<<", "Token injection"),
        (r">>>", "Token injection"),
    ]

    for pattern, description in dangerous_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            logger.warning(f"Blocked prompt with pattern: {description}")
            return False, "", f"Prompt contains potentially unsafe patterns ({description})"

    # Remove control characters except newline, tab, carriage return
    # Keep common whitespace but remove other control chars
    sanitized = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', prompt)

    # Check if sanitization changed the prompt significantly
    if len(sanitized) < len(prompt) * 0.9:
        return False, "", "Prompt contains too many invalid characters"

    return True, sanitized, ""


def validate_csv_upload(file_size: int, max_size: int = 1_000_000) -> Tuple[bool, str]:
    """Validate CSV upload file size

    Protects against:
    - Memory exhaustion from large files
    - DoS attacks via file upload

    Args:
        file_size: Size of uploaded file in bytes
        max_size: Maximum allowed size in bytes (default: 1MB)

    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is empty string

    Examples:
        >>> validate_csv_upload(100_000)
        (True, "")
        >>> validate_csv_upload(2_000_000)
        (False, "File too large (max 1000KB, got 2000KB)")
    """
    if file_size <= 0:
        return False, "File is empty"

    if file_size > max_size:
        max_kb = max_size / 1000
        got_kb = file_size / 1000
        return False, f"File too large (max {max_kb:.0f}KB, got {got_kb:.0f}KB)"

    return True, ""


def validate_batch_urls(urls: list, max_urls: int = 1000) -> Tuple[bool, list, str]:
    """Validate batch of URLs

    Validates each URL and removes duplicates. Enforces max URL limit.

    Args:
        urls: List of URLs to validate
        max_urls: Maximum number of URLs allowed

    Returns:
        Tuple of (all_valid, valid_urls, error_message)
        valid_urls contains deduplicated valid URLs
        If any URL is invalid, all_valid is False but valid_urls still contains valid ones

    Examples:
        >>> validate_batch_urls(["https://example.com", "https://test.com"])
        (True, ["https://example.com", "https://test.com"], "")
        >>> validate_batch_urls(["http://localhost"] * 5)
        (False, [], "5 invalid URLs found")
    """
    if not urls:
        return False, [], "No URLs provided"

    if len(urls) > max_urls:
        return False, [], f"Too many URLs (max {max_urls}, got {len(urls)})"

    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        url_stripped = url.strip()
        if url_stripped and url_stripped not in seen:
            seen.add(url_stripped)
            unique_urls.append(url_stripped)

    # Validate each URL
    valid_urls = []
    invalid_count = 0
    invalid_examples = []

    for url in unique_urls:
        is_valid, error = validate_url(url)
        if is_valid:
            valid_urls.append(url)
        else:
            invalid_count += 1
            if len(invalid_examples) < 3:  # Keep first 3 examples
                invalid_examples.append(f"{url}: {error}")

    # Build error message
    if invalid_count > 0:
        error_msg = f"{invalid_count} invalid URL(s) found"
        if invalid_examples:
            error_msg += f": {'; '.join(invalid_examples)}"
        if invalid_count > 3:
            error_msg += f" (and {invalid_count - 3} more)"

        return False, valid_urls, error_msg

    return True, valid_urls, ""


def validate_model_name(model: str) -> Tuple[bool, str]:
    """Validate LLM model name

    Ensures model name doesn't contain path traversal or injection attempts.

    Args:
        model: Model name to validate

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_model_name("qwen2.5-coder:7b")
        (True, "")
        >>> validate_model_name("../../../etc/passwd")
        (False, "Invalid model name format")
    """
    if not model:
        return False, "Model name is required"

    model = model.strip()

    # Allow alphanumeric, dots, hyphens, colons, underscores
    # This matches Ollama model naming convention
    if not re.match(r'^[a-zA-Z0-9._:-]+$', model):
        return False, "Invalid model name format (use alphanumeric, dots, hyphens, colons)"

    # Block path traversal attempts
    if '..' in model or '/' in model or '\\' in model:
        return False, "Invalid model name format (path traversal detected)"

    # Reasonable length limit
    if len(model) > 100:
        return False, "Model name too long (max 100 characters)"

    return True, ""


def validate_config_value(key: str, value: str) -> Tuple[bool, str, str]:
    """Validate configuration values

    Validates common config values like URLs, ports, hostnames.

    Args:
        key: Configuration key (e.g., 'ollama_url', 'redis_port')
        value: Value to validate

    Returns:
        Tuple of (is_valid, sanitized_value, error_message)

    Examples:
        >>> validate_config_value('redis_port', '6379')
        (True, '6379', "")
        >>> validate_config_value('redis_port', '999999')
        (False, '', "Port number out of range (1-65535)")
    """
    if not value:
        return False, "", f"{key} is required"

    value = value.strip()

    # Validate based on key type
    if 'port' in key.lower():
        try:
            port = int(value)
            if port < 1 or port > 65535:
                return False, "", "Port number out of range (1-65535)"
            return True, str(port), ""
        except ValueError:
            return False, "", "Port must be a number"

    elif 'url' in key.lower():
        # Allow localhost for Ollama/Redis URLs in config
        if not value.startswith('http://') and not value.startswith('https://'):
            return False, "", "URL must start with http:// or https://"

        try:
            parsed = urlparse(value)
            if not parsed.hostname:
                return False, "", "Invalid URL: missing hostname"
            return True, value, ""
        except Exception as e:
            return False, "", f"Invalid URL format: {str(e)}"

    elif 'host' in key.lower():
        # Validate hostname/IP
        # Allow localhost for Redis/Ollama hosts
        if not re.match(r'^[a-zA-Z0-9._-]+$', value):
            return False, "", "Invalid hostname format"

        if len(value) > 255:
            return False, "", "Hostname too long (max 255 characters)"

        return True, value, ""

    else:
        # Generic validation - remove control characters
        sanitized = re.sub(r'[\x00-\x1F\x7F]', '', value)
        if len(sanitized) != len(value):
            return False, "", "Value contains invalid characters"

        return True, sanitized, ""
