"""
Pydantic data models for schema validation
Provides strict type validation for common scraping scenarios
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class ProductSchema(BaseModel):
    """E-commerce product schema"""
    name: str
    price: float = Field(gt=0, description="Price must be greater than 0")
    in_stock: bool
    rating: Optional[float] = Field(None, ge=0, le=5, description="Rating between 0 and 5")

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Product name cannot be empty')
        return v.strip()


class ArticleSchema(BaseModel):
    """News article schema"""
    title: str
    author: Optional[str] = None
    publication_date: Optional[str] = None
    content: str

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Article title cannot be empty')
        return v.strip()

    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Article content cannot be empty')
        return v.strip()


class JobListingSchema(BaseModel):
    """Job listing schema"""
    title: str
    company: str
    location: Optional[str] = None
    salary: Optional[str] = None
    requirements: Optional[List[str]] = None

    @field_validator('title', 'company')
    @classmethod
    def field_not_empty(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Field cannot be empty')
        return v.strip()


class ResearchPaperSchema(BaseModel):
    """Research paper schema"""
    title: str
    authors: List[str]
    abstract: str
    publication_venue: Optional[str] = None

    @field_validator('title', 'abstract')
    @classmethod
    def field_not_empty(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Field cannot be empty')
        return v.strip()

    @field_validator('authors')
    @classmethod
    def authors_not_empty(cls, v: List[str]) -> List[str]:
        if not v or len(v) == 0:
            raise ValueError('Authors list cannot be empty')
        return v


class ContactSchema(BaseModel):
    """Contact information schema"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


# Schema registry for easy access
SCHEMAS = {
    "none": None,  # No validation
    "product": ProductSchema,
    "article": ArticleSchema,
    "job": JobListingSchema,
    "research_paper": ResearchPaperSchema,
    "contact": ContactSchema,
}


def validate_data(data: dict, schema_name: str) -> tuple[bool, Optional[dict], Optional[str]]:
    """
    Validate data against a schema

    Args:
        data: Dictionary to validate
        schema_name: Name of schema from SCHEMAS registry

    Returns:
        Tuple of (success, validated_data, error_message)
    """
    if schema_name == "none" or schema_name not in SCHEMAS:
        return True, data, None

    schema_class = SCHEMAS[schema_name]

    try:
        validated = schema_class(**data)
        return True, validated.model_dump(), None
    except Exception as e:
        return False, None, str(e)
