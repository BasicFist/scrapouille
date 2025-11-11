"""
Pydantic Models for API Request/Response
Defines data validation schemas for FastAPI endpoints
"""

from pydantic import BaseModel, HttpUrl, Field, field_validator
from typing import Optional, Dict, Any


# === Scraping Models ===

class ScrapeRequest(BaseModel):
    """Request model for single URL scraping"""

    url: str = Field(..., description="URL to scrape")
    prompt: str = Field(..., description="Extraction prompt")
    model: str = Field(
        default="qwen2.5-coder:7b",
        description="Primary LLM model to use"
    )
    schema_name: Optional[str] = Field(
        default=None,
        description="Validation schema name (e.g., 'Product', 'Article')"
    )
    rate_limit_mode: str = Field(
        default="normal",
        description="Rate limiting mode: 'none', 'aggressive', 'normal', 'polite'"
    )
    stealth_level: str = Field(
        default="off",
        description="Stealth level: 'off', 'low', 'medium', 'high'"
    )
    use_cache: bool = Field(
        default=True,
        description="Enable Redis caching"
    )
    markdown_mode: bool = Field(
        default=False,
        description="Use markdown conversion instead of LLM"
    )

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        if len(v) < 10:
            raise ValueError('URL too short')
        return v

    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Validate prompt length"""
        if len(v.strip()) < 5:
            raise ValueError('Prompt must be at least 5 characters')
        if len(v) > 5000:
            raise ValueError('Prompt too long (max 5000 characters)')
        return v.strip()

    @field_validator('rate_limit_mode')
    @classmethod
    def validate_rate_limit(cls, v: str) -> str:
        """Validate rate limit mode"""
        allowed = ['none', 'aggressive', 'normal', 'polite']
        if v not in allowed:
            raise ValueError(f'rate_limit_mode must be one of: {allowed}')
        return v

    @field_validator('stealth_level')
    @classmethod
    def validate_stealth(cls, v: str) -> str:
        """Validate stealth level"""
        allowed = ['off', 'low', 'medium', 'high']
        if v not in allowed:
            raise ValueError(f'stealth_level must be one of: {allowed}')
        return v


class ScrapeMetadata(BaseModel):
    """Metadata about scrape execution"""

    execution_time: float = Field(description="Execution time in seconds")
    model_used: str = Field(description="Model that successfully scraped")
    fallback_attempts: int = Field(description="Number of fallback attempts")
    cached: bool = Field(description="Whether result was from cache")
    validation_passed: Optional[bool] = Field(
        default=None,
        description="Whether Pydantic validation passed"
    )


class ScrapeResponse(BaseModel):
    """Response model for scraping"""

    success: bool = Field(description="Whether scraping succeeded")
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Scraped data"
    )
    metadata: ScrapeMetadata = Field(description="Execution metadata")
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )


# === Batch Models (Phase 3) ===

class BatchScrapeRequest(BaseModel):
    """Request model for batch scraping"""

    urls: list[str] = Field(..., description="List of URLs to scrape")
    prompt: str = Field(..., description="Extraction prompt")
    model: str = Field(default="qwen2.5-coder:7b")
    schema_name: Optional[str] = None
    max_concurrent: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Max concurrent scraping operations"
    )
    timeout_per_url: float = Field(
        default=30.0,
        ge=10.0,
        le=120.0,
        description="Timeout per URL in seconds"
    )
    use_cache: bool = True
    use_rate_limiting: bool = True
    use_stealth: bool = False

    @field_validator('urls')
    @classmethod
    def validate_urls(cls, v: list[str]) -> list[str]:
        """Validate URL list"""
        if len(v) == 0:
            raise ValueError('At least one URL required')
        if len(v) > 100:
            raise ValueError('Maximum 100 URLs per batch')
        return v


class BatchResult(BaseModel):
    """Individual result from batch scraping"""

    url: str = Field(description="URL that was scraped")
    index: int = Field(description="Original index in batch")
    success: bool = Field(description="Whether scraping succeeded")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Scraped data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time: float = Field(description="Execution time in seconds")
    model_used: Optional[str] = Field(default=None, description="Model used")
    fallback_attempts: int = Field(default=0, description="Fallback attempts")
    cached: bool = Field(default=False, description="From cache")
    validation_passed: Optional[bool] = Field(default=None, description="Validation status")


class BatchScrapeResponse(BaseModel):
    """Response model for batch scraping"""

    success: bool = Field(description="Overall batch success")
    results: list[BatchResult] = Field(description="Individual results")
    summary: Dict[str, Any] = Field(description="Summary statistics")
    error: Optional[str] = Field(default=None, description="Overall error if any")


# === Config Models (Phase 4) ===

class ConfigResponse(BaseModel):
    """Configuration response"""

    ollama_base_url: str
    redis_host: str
    redis_port: int
    default_model: str
    default_rate_limit: str
    default_stealth_level: str


class ConfigUpdateRequest(BaseModel):
    """Configuration update request"""

    ollama_base_url: Optional[str] = None
    redis_host: Optional[str] = None
    redis_port: Optional[int] = None
    default_model: Optional[str] = None
    default_rate_limit: Optional[str] = None
    default_stealth_level: Optional[str] = None
