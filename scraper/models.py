"""
Pydantic data models for schema validation
Enhanced with business logic validators for production-grade data quality
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re


class ProductSchema(BaseModel):
    """E-commerce product schema with business logic validation"""
    name: str
    price: float = Field(gt=0, description="Price must be greater than 0")
    in_stock: bool
    rating: Optional[float] = Field(None, ge=0, le=5, description="Rating between 0 and 5")

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Product name cannot be empty')
        # Check suspicious patterns
        if len(v.strip()) < 3:
            raise ValueError('Product name too short (min 3 characters)')
        if v.strip().lower() in ['n/a', 'null', 'none', 'unknown']:
            raise ValueError('Invalid product name placeholder')
        return v.strip()

    @field_validator('price')
    @classmethod
    def price_realistic(cls, v: float) -> float:
        """Validate price is in realistic range"""
        if v < 0.01:
            raise ValueError('Price too low (min $0.01)')
        if v > 1_000_000:
            raise ValueError('Price unrealistically high (max $1M)')
        return round(v, 2)  # Round to 2 decimals

    @field_validator('rating')
    @classmethod
    def rating_valid(cls, v: Optional[float]) -> Optional[float]:
        """Validate rating format"""
        if v is None:
            return v
        # Round to 1 decimal
        return round(v, 1)


class ArticleSchema(BaseModel):
    """News article schema with enhanced validation"""
    title: str
    author: Optional[str] = None
    publication_date: Optional[str] = None
    content: str

    @field_validator('title')
    @classmethod
    def title_valid(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Article title cannot be empty')
        if len(v.strip()) < 5:
            raise ValueError('Title too short (min 5 characters)')
        return v.strip()

    @field_validator('content')
    @classmethod
    def content_substantial(cls, v: str) -> str:
        """Ensure content is meaningful"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Article content cannot be empty')
        if len(v.strip()) < 50:
            raise ValueError('Content too short (min 50 characters for article)')
        return v.strip()

    @field_validator('publication_date')
    @classmethod
    def date_format_check(cls, v: Optional[str]) -> Optional[str]:
        """Validate date is in reasonable format"""
        if v is None:
            return v
        # Check if date contains digits
        if not re.search(r'\d', v):
            raise ValueError('Publication date must contain date information')
        return v.strip()


class JobListingSchema(BaseModel):
    """Job listing schema with validation"""
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
        if len(v.strip()) < 2:
            raise ValueError('Field too short (min 2 characters)')
        return v.strip()

    @field_validator('salary')
    @classmethod
    def salary_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate salary contains numbers"""
        if v is None:
            return v
        # Check if salary contains digits or 'k'
        if not re.search(r'[\d,k$€£¥]', v, re.IGNORECASE):
            raise ValueError('Salary must contain monetary information')
        return v.strip()

    @field_validator('requirements')
    @classmethod
    def requirements_valid(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Clean and validate requirements list"""
        if v is None:
            return v
        # Remove empty strings
        cleaned = [req.strip() for req in v if req and req.strip()]
        if len(cleaned) == 0:
            return None  # Empty list becomes None
        return cleaned


class ResearchPaperSchema(BaseModel):
    """Research paper schema with academic validation"""
    title: str
    authors: List[str]
    abstract: str
    publication_venue: Optional[str] = None

    @field_validator('title')
    @classmethod
    def title_substantial(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Paper title cannot be empty')
        if len(v.strip()) < 10:
            raise ValueError('Title too short for research paper (min 10 chars)')
        return v.strip()

    @field_validator('abstract')
    @classmethod
    def abstract_substantial(cls, v: str) -> str:
        """Ensure abstract is meaningful"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Abstract cannot be empty')
        if len(v.strip()) < 100:
            raise ValueError('Abstract too short (min 100 characters)')
        return v.strip()

    @field_validator('authors')
    @classmethod
    def authors_valid(cls, v: List[str]) -> List[str]:
        """Validate author list"""
        if not v or len(v) == 0:
            raise ValueError('Authors list cannot be empty')
        # Clean author names
        cleaned = [a.strip() for a in v if a and a.strip()]
        if len(cleaned) == 0:
            raise ValueError('No valid author names found')
        return cleaned


class ContactSchema(BaseModel):
    """Contact information schema with format validation"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    @field_validator('email')
    @classmethod
    def email_format(cls, v: Optional[str]) -> Optional[str]:
        """Basic email validation"""
        if v is None:
            return v
        # Simple email regex (not RFC-compliant, but catches obvious errors)
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v.strip()):
            raise ValueError('Invalid email format')
        return v.strip().lower()

    @field_validator('phone')
    @classmethod
    def phone_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone contains digits"""
        if v is None:
            return v
        # Check if phone contains digits
        if not re.search(r'\d', v):
            raise ValueError('Phone number must contain digits')
        return v.strip()

    @field_validator('name')
    @classmethod
    def name_valid(cls, v: Optional[str]) -> Optional[str]:
        """Validate name if provided"""
        if v is None:
            return v
        if len(v.strip()) < 2:
            raise ValueError('Name too short (min 2 characters)')
        return v.strip()


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
