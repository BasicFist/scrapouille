"""
Few-shot prompt templates for common scraping scenarios
Templates include examples to improve extraction accuracy
"""

TEMPLATES = {
    "Custom": "",  # Empty template for custom prompts

    "E-commerce Products": """Extract product information from the page. Return JSON with these exact fields:
- name (string): Product name
- price (float): Price in USD without $ symbol
- in_stock (boolean): true if available, false if sold out
- rating (float): Rating from 0 to 5, or null if not shown

Examples:
Input HTML: <div><h2>Laptop Pro 15</h2><span class="price">$1,299.99</span><span class="stock">In Stock</span></div>
Output: {"name": "Laptop Pro 15", "price": 1299.99, "in_stock": true, "rating": null}

Input HTML: <div><h2>Wireless Mouse</h2><span class="price">$29.99</span><span class="stock">Out of Stock</span><div class="rating">★★★★☆ 4.2</div></div>
Output: {"name": "Wireless Mouse", "price": 29.99, "in_stock": false, "rating": 4.2}

Now extract from the page.""",

    "News Articles": """Extract article information. Return JSON with:
- title (string): Article headline
- author (string or null): Author name
- publication_date (string or null): When published
- content (string): Article text content

Examples:
Input: <article><h1>AI Breakthrough in 2025</h1><span class="author">John Smith</span><time>2025-01-15</time><p>Researchers announced a major breakthrough...</p></article>
Output: {"title": "AI Breakthrough in 2025", "author": "John Smith", "publication_date": "2025-01-15", "content": "Researchers announced a major breakthrough..."}

Input: <article><h1>Climate Change Report</h1><p>A new study shows...</p></article>
Output: {"title": "Climate Change Report", "author": null, "publication_date": null, "content": "A new study shows..."}

Now extract from the page.""",

    "Job Listings": """Extract job posting details. Return JSON with:
- title (string): Job title
- company (string): Company name
- location (string or null): Job location
- salary (string or null): Salary range
- requirements (list of strings): Key requirements

Examples:
Input: <div class="job"><h2>Senior Python Developer</h2><span class="company">TechCorp</span><span class="location">San Francisco, CA</span><span class="salary">$120k-$160k</span><ul><li>5+ years Python</li><li>FastAPI experience</li></ul></div>
Output: {"title": "Senior Python Developer", "company": "TechCorp", "location": "San Francisco, CA", "salary": "$120k-$160k", "requirements": ["5+ years Python", "FastAPI experience"]}

Input: <div class="job"><h2>Data Scientist</h2><span class="company">DataCo</span><ul><li>Machine Learning</li><li>Python/R</li></ul></div>
Output: {"title": "Data Scientist", "company": "DataCo", "location": null, "salary": null, "requirements": ["Machine Learning", "Python/R"]}

Now extract from the page.""",

    "Research Papers": """Extract academic paper metadata. Return JSON with:
- title (string): Paper title
- authors (list of strings): Author names
- abstract (string): Abstract text
- publication_venue (string or null): Journal/conference name

Examples:
Input: <div class="paper"><h1>Deep Learning for NLP</h1><div class="authors">Jane Doe, John Smith</div><div class="abstract">This paper presents...</div><span class="venue">ACL 2025</span></div>
Output: {"title": "Deep Learning for NLP", "authors": ["Jane Doe", "John Smith"], "abstract": "This paper presents...", "publication_venue": "ACL 2025"}

Now extract from the page.""",

    "Contact Information": """Extract contact details. Return JSON with:
- name (string or null): Person/company name
- email (string or null): Email address
- phone (string or null): Phone number
- address (string or null): Physical address

Examples:
Input: <div class="contact"><h3>John Doe</h3><p>Email: john@example.com</p><p>Phone: +1-555-0123</p></div>
Output: {"name": "John Doe", "email": "john@example.com", "phone": "+1-555-0123", "address": null}

Input: <footer><p>Contact us at info@company.com</p><p>123 Main St, City, State 12345</p></footer>
Output: {"name": null, "email": "info@company.com", "phone": null, "address": "123 Main St, City, State 12345"}

Now extract from the page.""",

    "Social Media Posts": """Extract social media post information. Return JSON with:
- text (string): Post content
- author (string): Author username or name
- timestamp (string or null): When posted
- likes (int or null): Number of likes
- comments (int or null): Number of comments

Examples:
Input: <div class="post"><span class="author">@techuser</span><p>Excited about the new AI features!</p><time>2h ago</time><span>142 likes</span><span>23 comments</span></div>
Output: {"text": "Excited about the new AI features!", "author": "@techuser", "timestamp": "2h ago", "likes": 142, "comments": 23}

Now extract from the page.""",

    "Event Listings": """Extract event information. Return JSON with:
- title (string): Event name
- date (string or null): Event date
- location (string or null): Event location
- description (string): Event description
- price (string or null): Ticket price

Examples:
Input: <div class="event"><h2>Tech Conference 2025</h2><time>March 15, 2025</time><span>San Francisco</span><p>Join us for...</p><span>$299</span></div>
Output: {"title": "Tech Conference 2025", "date": "March 15, 2025", "location": "San Francisco", "description": "Join us for...", "price": "$299"}

Now extract from the page.""",
}


# Map templates to recommended schemas
TEMPLATE_SCHEMA_MAP = {
    "E-commerce Products": "product",
    "News Articles": "article",
    "Job Listings": "job",
    "Research Papers": "research_paper",
    "Contact Information": "contact",
    # Others default to "none"
}


def get_template(template_name: str) -> str:
    """Get template by name"""
    return TEMPLATES.get(template_name, "")


def get_recommended_schema(template_name: str) -> str:
    """Get recommended schema for a template"""
    return TEMPLATE_SCHEMA_MAP.get(template_name, "none")


def list_templates() -> list[str]:
    """Get list of available template names"""
    return list(TEMPLATES.keys())
