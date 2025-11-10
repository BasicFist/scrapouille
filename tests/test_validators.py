"""
Unit tests for Enhanced Pydantic Validators
Tests business logic validation for all schemas
"""
import pytest
from scraper.models import (
    ProductSchema,
    ArticleSchema,
    JobListingSchema,
    ResearchPaperSchema,
    ContactSchema,
    validate_data
)


# ProductSchema Tests
def test_product_valid():
    """Test valid product passes validation"""
    product = ProductSchema(
        name="Laptop Pro",
        price=1299.99,
        in_stock=True,
        rating=4.5
    )
    assert product.name == "Laptop Pro"
    assert product.price == 1299.99
    assert product.rating == 4.5


def test_product_name_too_short():
    """Test product name must be at least 3 characters"""
    with pytest.raises(ValueError) as exc_info:
        ProductSchema(name="AB", price=10.0, in_stock=True)
    assert "too short" in str(exc_info.value).lower()


def test_product_name_placeholder():
    """Test product name rejects placeholders"""
    placeholders = ["n/a", "null", "none", "unknown"]
    for placeholder in placeholders:
        with pytest.raises(ValueError) as exc_info:
            ProductSchema(name=placeholder, price=10.0, in_stock=True)
        assert "placeholder" in str(exc_info.value).lower()


def test_product_price_too_low():
    """Test price must be at least $0.01"""
    with pytest.raises(ValueError) as exc_info:
        ProductSchema(name="Product", price=0.001, in_stock=True)
    assert "too low" in str(exc_info.value).lower()


def test_product_price_too_high():
    """Test price must not exceed $1M"""
    with pytest.raises(ValueError) as exc_info:
        ProductSchema(name="Product", price=2_000_000, in_stock=True)
    assert "unrealistically high" in str(exc_info.value).lower()


def test_product_price_rounding():
    """Test price is rounded to 2 decimals"""
    product = ProductSchema(name="Product", price=9.999, in_stock=True)
    assert product.price == 10.00


def test_product_rating_rounding():
    """Test rating is rounded to 1 decimal"""
    product = ProductSchema(name="Product", price=10.0, in_stock=True, rating=4.567)
    assert product.rating == 4.6


# ArticleSchema Tests
def test_article_valid():
    """Test valid article passes validation"""
    article = ArticleSchema(
        title="Breaking News: Important Event",
        content="This is a substantial article content that meets the minimum length requirement of 50 characters for proper validation.",
        author="John Doe",
        publication_date="2025-11-09"
    )
    assert article.title == "Breaking News: Important Event"
    assert len(article.content) >= 50


def test_article_title_too_short():
    """Test article title must be at least 5 characters"""
    with pytest.raises(ValueError) as exc_info:
        ArticleSchema(
            title="News",
            content="A" * 60
        )
    assert "too short" in str(exc_info.value).lower()


def test_article_content_too_short():
    """Test article content must be at least 50 characters"""
    with pytest.raises(ValueError) as exc_info:
        ArticleSchema(
            title="Valid Title",
            content="Short content"
        )
    assert "too short" in str(exc_info.value).lower()


def test_article_publication_date_must_contain_digits():
    """Test publication date must contain date information"""
    with pytest.raises(ValueError) as exc_info:
        ArticleSchema(
            title="Valid Title",
            content="A" * 60,
            publication_date="Unknown"
        )
    assert "date information" in str(exc_info.value).lower()


def test_article_publication_date_valid_formats():
    """Test various valid date formats"""
    valid_dates = ["2025-11-09", "Nov 9, 2025", "09/11/2025"]
    for date in valid_dates:
        article = ArticleSchema(
            title="Valid Title",
            content="A" * 60,
            publication_date=date
        )
        assert article.publication_date == date


# JobListingSchema Tests
def test_job_listing_valid():
    """Test valid job listing passes validation"""
    job = JobListingSchema(
        title="Software Engineer",
        company="TechCorp",
        location="San Francisco",
        salary="$120k-150k",
        requirements=["Python", "React", "5 years experience"]
    )
    assert job.title == "Software Engineer"
    assert job.company == "TechCorp"


def test_job_title_too_short():
    """Test job title must be at least 2 characters"""
    with pytest.raises(ValueError) as exc_info:
        JobListingSchema(title="A", company="TechCorp")
    assert "too short" in str(exc_info.value).lower()


def test_job_salary_must_contain_monetary_info():
    """Test salary must contain monetary information"""
    with pytest.raises(ValueError) as exc_info:
        JobListingSchema(
            title="Engineer",
            company="TechCorp",
            salary="Competitive"
        )
    assert "monetary information" in str(exc_info.value).lower()


def test_job_salary_valid_formats():
    """Test various valid salary formats"""
    valid_salaries = ["$120k", "100,000 EUR", "£50k-60k", "¥5,000,000"]
    for salary in valid_salaries:
        job = JobListingSchema(
            title="Engineer",
            company="TechCorp",
            salary=salary
        )
        assert job.salary == salary


def test_job_requirements_cleaning():
    """Test requirements list is cleaned of empty strings"""
    job = JobListingSchema(
        title="Engineer",
        company="TechCorp",
        requirements=["Python", "", "  ", "React", None]
    )
    assert job.requirements == ["Python", "React"]


def test_job_requirements_empty_becomes_none():
    """Test empty requirements list becomes None"""
    job = JobListingSchema(
        title="Engineer",
        company="TechCorp",
        requirements=["", "  "]
    )
    assert job.requirements is None


# ResearchPaperSchema Tests
def test_research_paper_valid():
    """Test valid research paper passes validation"""
    paper = ResearchPaperSchema(
        title="Deep Learning Approaches to Natural Language Processing",
        authors=["Alice Smith", "Bob Johnson"],
        abstract="A" * 120,  # Substantial abstract
        publication_venue="NeurIPS 2025"
    )
    assert paper.title == "Deep Learning Approaches to Natural Language Processing"
    assert len(paper.authors) == 2


def test_research_paper_title_too_short():
    """Test paper title must be at least 10 characters"""
    with pytest.raises(ValueError) as exc_info:
        ResearchPaperSchema(
            title="AI Paper",
            authors=["Author"],
            abstract="A" * 120
        )
    assert "too short" in str(exc_info.value).lower()


def test_research_paper_abstract_too_short():
    """Test abstract must be at least 100 characters"""
    with pytest.raises(ValueError) as exc_info:
        ResearchPaperSchema(
            title="A Comprehensive Study",
            authors=["Author"],
            abstract="Short abstract"
        )
    assert "too short" in str(exc_info.value).lower()


def test_research_paper_authors_cleaning():
    """Test authors list is cleaned"""
    paper = ResearchPaperSchema(
        title="A Comprehensive Study",
        authors=["Alice Smith", "  ", "", "Bob Johnson"],
        abstract="A" * 120
    )
    assert paper.authors == ["Alice Smith", "Bob Johnson"]


def test_research_paper_authors_empty():
    """Test authors list cannot be empty"""
    with pytest.raises(ValueError) as exc_info:
        ResearchPaperSchema(
            title="A Comprehensive Study",
            authors=[],
            abstract="A" * 120
        )
    assert "cannot be empty" in str(exc_info.value).lower()


# ContactSchema Tests
def test_contact_valid():
    """Test valid contact passes validation"""
    contact = ContactSchema(
        name="John Doe",
        email="john.doe@example.com",
        phone="+1-555-123-4567",
        address="123 Main St"
    )
    assert contact.name == "John Doe"
    assert contact.email == "john.doe@example.com"


def test_contact_email_format_valid():
    """Test various valid email formats"""
    valid_emails = [
        "user@example.com",
        "test.user@example.co.uk",
        "user+tag@example.com"
    ]
    for email in valid_emails:
        contact = ContactSchema(email=email)
        assert contact.email == email.lower()


def test_contact_email_format_invalid():
    """Test invalid email formats are rejected"""
    invalid_emails = [
        "not-an-email",
        "@example.com",
        "user@",
        "user @example.com"
    ]
    for email in invalid_emails:
        with pytest.raises(ValueError) as exc_info:
            ContactSchema(email=email)
        assert "invalid email" in str(exc_info.value).lower()


def test_contact_email_normalized_to_lowercase():
    """Test email is normalized to lowercase"""
    contact = ContactSchema(email="John.Doe@Example.COM")
    assert contact.email == "john.doe@example.com"


def test_contact_phone_must_contain_digits():
    """Test phone must contain digits"""
    with pytest.raises(ValueError) as exc_info:
        ContactSchema(phone="Call me")
    assert "must contain digits" in str(exc_info.value).lower()


def test_contact_phone_valid_formats():
    """Test various valid phone formats"""
    valid_phones = [
        "+1-555-123-4567",
        "(555) 123-4567",
        "555.123.4567",
        "5551234567"
    ]
    for phone in valid_phones:
        contact = ContactSchema(phone=phone)
        assert contact.phone == phone


def test_contact_name_too_short():
    """Test name must be at least 2 characters"""
    with pytest.raises(ValueError) as exc_info:
        ContactSchema(name="A")
    assert "too short" in str(exc_info.value).lower()


# validate_data() function tests
def test_validate_data_success():
    """Test validate_data returns success for valid data"""
    data = {"name": "Product", "price": 99.99, "in_stock": True}
    valid, validated, error = validate_data(data, "product")

    assert valid is True
    assert validated["name"] == "Product"
    assert error is None


def test_validate_data_failure():
    """Test validate_data returns error for invalid data"""
    data = {"name": "AB", "price": 99.99, "in_stock": True}  # Name too short
    valid, validated, error = validate_data(data, "product")

    assert valid is False
    assert validated is None
    assert "too short" in error.lower()


def test_validate_data_none_schema():
    """Test validate_data with 'none' schema returns data unchanged"""
    data = {"anything": "goes"}
    valid, validated, error = validate_data(data, "none")

    assert valid is True
    assert validated == data
    assert error is None


def test_validate_data_unknown_schema():
    """Test validate_data with unknown schema returns data unchanged"""
    data = {"anything": "goes"}
    valid, validated, error = validate_data(data, "unknown_schema")

    assert valid is True
    assert validated == data
    assert error is None
