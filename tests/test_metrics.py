"""
Unit tests for Persistent Metrics System
Tests SQLite database operations and analytics
"""
import pytest
import os
import tempfile
from datetime import datetime, timedelta
from scraper.metrics import MetricsDB, ScrapeMetric


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_metrics.db")
        yield db_path


def test_metrics_db_initialization(temp_db):
    """Test database is initialized correctly"""
    db = MetricsDB(db_path=temp_db)

    # Database file should exist
    assert os.path.exists(temp_db)

    # Check table was created
    import sqlite3
    conn = sqlite3.connect(temp_db)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='scrapes'"
    )
    assert cursor.fetchone() is not None
    conn.close()


def test_scrape_metric_to_dict():
    """Test ScrapeMetric converts to dict correctly"""
    metric = ScrapeMetric(
        id=1,
        timestamp="2025-11-09T12:00:00",
        url="http://test.com",
        prompt_hash="abc123",
        model="qwen2.5-coder:7b",
        execution_time_seconds=5.2,
        cached=False
    )

    data = metric.to_dict()

    assert data['id'] == 1
    assert data['url'] == "http://test.com"
    assert data['model'] == "qwen2.5-coder:7b"
    assert data['execution_time_seconds'] == 5.2


def test_log_scrape_basic(temp_db):
    """Test logging a basic scrape operation"""
    db = MetricsDB(db_path=temp_db)

    row_id = db.log_scrape(
        url="http://test.com",
        prompt="Extract data",
        model="qwen2.5-coder:7b",
        execution_time=5.2
    )

    assert row_id > 0


def test_log_scrape_with_all_fields(temp_db):
    """Test logging with all optional fields"""
    db = MetricsDB(db_path=temp_db)

    row_id = db.log_scrape(
        url="http://test.com",
        prompt="Extract products",
        model="qwen2.5-coder:7b",
        execution_time=10.5,
        token_count=1500,
        retry_count=2,
        fallback_attempts=3,
        cached=True,
        validation_passed=True,
        schema_used="product",
        error=None
    )

    assert row_id > 0

    # Verify data was stored correctly
    metrics = db.get_recent(limit=1)
    assert len(metrics) == 1

    metric = metrics[0]
    assert metric.url == "http://test.com"
    assert metric.model == "qwen2.5-coder:7b"
    assert metric.execution_time_seconds == 10.5
    assert metric.token_count == 1500
    assert metric.retry_count == 2
    assert metric.fallback_attempts == 3
    assert metric.cached is True
    assert metric.validation_passed is True
    assert metric.schema_used == "product"


def test_log_scrape_with_error(temp_db):
    """Test logging a failed scrape"""
    db = MetricsDB(db_path=temp_db)

    row_id = db.log_scrape(
        url="http://test.com",
        prompt="Extract data",
        model="qwen2.5-coder:7b",
        execution_time=2.1,
        validation_passed=False,
        error="Model unavailable"
    )

    assert row_id > 0

    metrics = db.get_recent(limit=1)
    metric = metrics[0]
    assert metric.validation_passed is False
    assert metric.error == "Model unavailable"


def test_prompt_hash_privacy(temp_db):
    """Test prompt is hashed for privacy"""
    db = MetricsDB(db_path=temp_db)

    prompt = "Extract sensitive data"
    db.log_scrape(
        url="http://test.com",
        prompt=prompt,
        model="qwen2.5-coder:7b",
        execution_time=5.0
    )

    metrics = db.get_recent(limit=1)
    metric = metrics[0]

    # Prompt hash should not contain the original prompt
    assert metric.prompt_hash != prompt
    assert len(metric.prompt_hash) == 16  # SHA256 truncated to 16 chars


def test_get_recent_limit(temp_db):
    """Test get_recent respects limit parameter"""
    db = MetricsDB(db_path=temp_db)

    # Add 10 scrapes
    for i in range(10):
        db.log_scrape(
            url=f"http://test{i}.com",
            prompt=f"prompt{i}",
            model="qwen2.5-coder:7b",
            execution_time=1.0
        )

    # Get only 5 most recent
    metrics = db.get_recent(limit=5)

    assert len(metrics) == 5
    # Should be in reverse chronological order (most recent first)
    assert metrics[0].url == "http://test9.com"


def test_get_recent_order(temp_db):
    """Test get_recent returns most recent first"""
    db = MetricsDB(db_path=temp_db)

    # Add scrapes with slight delays
    import time
    for i in range(3):
        db.log_scrape(
            url=f"http://test{i}.com",
            prompt="prompt",
            model="qwen2.5-coder:7b",
            execution_time=1.0
        )
        time.sleep(0.01)  # Small delay to ensure different timestamps

    metrics = db.get_recent(limit=10)

    # Most recent should be first
    assert metrics[0].url == "http://test2.com"
    assert metrics[1].url == "http://test1.com"
    assert metrics[2].url == "http://test0.com"


def test_get_stats_empty_db(temp_db):
    """Test get_stats with empty database"""
    db = MetricsDB(db_path=temp_db)

    stats = db.get_stats(days=7)

    assert stats['total_scrapes'] == 0
    assert stats['avg_time'] is None
    assert stats['cache_hits'] == 0
    assert stats['errors'] == 0
    assert stats['cache_hit_rate'] == 0
    assert stats['error_rate'] == 0


def test_get_stats_basic(temp_db):
    """Test get_stats with basic data"""
    db = MetricsDB(db_path=temp_db)

    # Add 5 successful scrapes
    for i in range(5):
        db.log_scrape(
            url=f"http://test{i}.com",
            prompt="prompt",
            model="qwen2.5-coder:7b",
            execution_time=5.0 + i,  # Varying times
            cached=False
        )

    stats = db.get_stats(days=7)

    assert stats['total_scrapes'] == 5
    assert stats['avg_time'] == 7.0  # (5+6+7+8+9) / 5
    assert stats['cache_hits'] == 0
    assert stats['errors'] == 0
    assert stats['cache_hit_rate'] == 0.0


def test_get_stats_with_cache_hits(temp_db):
    """Test cache hit rate calculation"""
    db = MetricsDB(db_path=temp_db)

    # 3 regular scrapes
    for i in range(3):
        db.log_scrape(
            url=f"http://test{i}.com",
            prompt="prompt",
            model="qwen2.5-coder:7b",
            execution_time=5.0,
            cached=False
        )

    # 7 cache hits
    for i in range(7):
        db.log_scrape(
            url=f"http://cached{i}.com",
            prompt="prompt",
            model="cache",
            execution_time=0.0,
            cached=True
        )

    stats = db.get_stats(days=7)

    assert stats['total_scrapes'] == 10
    assert stats['cache_hits'] == 7
    assert stats['cache_hit_rate'] == 70.0  # 7/10 * 100


def test_get_stats_with_errors(temp_db):
    """Test error rate calculation"""
    db = MetricsDB(db_path=temp_db)

    # 8 successful scrapes
    for i in range(8):
        db.log_scrape(
            url=f"http://test{i}.com",
            prompt="prompt",
            model="qwen2.5-coder:7b",
            execution_time=5.0
        )

    # 2 failed scrapes
    for i in range(2):
        db.log_scrape(
            url=f"http://fail{i}.com",
            prompt="prompt",
            model="qwen2.5-coder:7b",
            execution_time=1.0,
            error="Connection failed"
        )

    stats = db.get_stats(days=7)

    assert stats['total_scrapes'] == 10
    assert stats['errors'] == 2
    assert stats['error_rate'] == 20.0  # 2/10 * 100


def test_get_stats_model_usage(temp_db):
    """Test model usage statistics"""
    db = MetricsDB(db_path=temp_db)

    # 5 qwen scrapes
    for i in range(5):
        db.log_scrape(
            url=f"http://test{i}.com",
            prompt="prompt",
            model="qwen2.5-coder:7b",
            execution_time=5.0
        )

    # 3 llama scrapes
    for i in range(3):
        db.log_scrape(
            url=f"http://test{i}.com",
            prompt="prompt",
            model="llama3.1",
            execution_time=5.0
        )

    # 2 cache hits
    for i in range(2):
        db.log_scrape(
            url=f"http://test{i}.com",
            prompt="prompt",
            model="cache",
            execution_time=0.0,
            cached=True
        )

    stats = db.get_stats(days=7)

    model_usage = {item['model']: item['count'] for item in stats['model_usage']}

    assert model_usage['qwen2.5-coder:7b'] == 5
    assert model_usage['llama3.1'] == 3
    assert model_usage['cache'] == 2


def test_get_stats_date_filtering(temp_db):
    """Test get_stats filters by date correctly"""
    db = MetricsDB(db_path=temp_db)

    # Manually insert old data (8 days ago) by direct SQL
    import sqlite3
    conn = sqlite3.connect(temp_db)
    old_date = (datetime.now() - timedelta(days=8)).isoformat()

    conn.execute("""
        INSERT INTO scrapes (timestamp, url, prompt_hash, model, execution_time_seconds)
        VALUES (?, ?, ?, ?, ?)
    """, (old_date, "http://old.com", "abc123", "qwen2.5-coder:7b", 5.0))
    conn.commit()
    conn.close()

    # Add recent data
    db.log_scrape(
        url="http://recent.com",
        prompt="prompt",
        model="qwen2.5-coder:7b",
        execution_time=5.0
    )

    # Get stats for last 7 days
    stats = db.get_stats(days=7)

    # Should only count the recent scrape, not the 8-day-old one
    assert stats['total_scrapes'] == 1


def test_export_csv_empty(temp_db):
    """Test CSV export with empty database"""
    db = MetricsDB(db_path=temp_db)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_path = f.name

    try:
        db.export_csv(csv_path)
        # Should not create file or should be empty
        assert not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


def test_export_csv_with_data(temp_db):
    """Test CSV export with data"""
    db = MetricsDB(db_path=temp_db)

    # Add test data
    for i in range(3):
        db.log_scrape(
            url=f"http://test{i}.com",
            prompt="prompt",
            model="qwen2.5-coder:7b",
            execution_time=5.0
        )

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_path = f.name

    try:
        db.export_csv(csv_path)

        # File should exist and have content
        assert os.path.exists(csv_path)
        assert os.path.getsize(csv_path) > 0

        # Read and verify CSV
        import csv
        with open(csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

            assert len(rows) == 3
            assert 'url' in rows[0]
            assert 'model' in rows[0]
            assert rows[0]['model'] == "qwen2.5-coder:7b"

    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


def test_export_csv_with_date_filter(temp_db):
    """Test CSV export with date filtering"""
    db = MetricsDB(db_path=temp_db)

    # Manually insert old data
    import sqlite3
    conn = sqlite3.connect(temp_db)
    old_date = (datetime.now() - timedelta(days=10)).isoformat()

    conn.execute("""
        INSERT INTO scrapes (timestamp, url, prompt_hash, model, execution_time_seconds)
        VALUES (?, ?, ?, ?, ?)
    """, (old_date, "http://old.com", "abc123", "qwen2.5-coder:7b", 5.0))
    conn.commit()
    conn.close()

    # Add recent data
    db.log_scrape(
        url="http://recent.com",
        prompt="prompt",
        model="qwen2.5-coder:7b",
        execution_time=5.0
    )

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_path = f.name

    try:
        # Export only last 7 days
        db.export_csv(csv_path, days=7)

        import csv
        with open(csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

            # Should only export recent data
            assert len(rows) == 1
            assert rows[0]['url'] == "http://recent.com"

    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)
