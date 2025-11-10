"""
Persistent metrics storage and retrieval
Tracks all scraping operations for analysis and debugging
"""
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
import json
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class ScrapeMetric:
    """Single scrape operation metric"""
    id: Optional[int] = None
    timestamp: str = None
    url: str = ""
    prompt_hash: str = ""  # Hash of prompt for privacy
    model: str = ""
    execution_time_seconds: float = 0.0
    token_count: Optional[int] = None
    retry_count: int = 0
    fallback_attempts: int = 1
    cached: bool = False
    validation_passed: bool = True
    schema_used: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)


class MetricsDB:
    """
    SQLite-based metrics persistence

    Example:
        db = MetricsDB()
        db.log_scrape(url, model, time, ...)
        stats = db.get_stats(days=7)
    """

    def __init__(self, db_path: str = "data/metrics.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        # Create data directory if needed
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scrapes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    url TEXT NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    model TEXT NOT NULL,
                    execution_time_seconds REAL NOT NULL,
                    token_count INTEGER,
                    retry_count INTEGER DEFAULT 0,
                    fallback_attempts INTEGER DEFAULT 1,
                    cached BOOLEAN DEFAULT 0,
                    validation_passed BOOLEAN DEFAULT 1,
                    schema_used TEXT,
                    error TEXT
                )
            """)

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON scrapes(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_url ON scrapes(url)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_model ON scrapes(model)")

            conn.commit()
            logger.info(f"✓ Metrics DB initialized: {self.db_path}")

    def log_scrape(
        self,
        url: str,
        prompt: str,
        model: str,
        execution_time: float,
        token_count: Optional[int] = None,
        retry_count: int = 0,
        fallback_attempts: int = 1,
        cached: bool = False,
        validation_passed: bool = True,
        schema_used: Optional[str] = None,
        error: Optional[str] = None
    ) -> int:
        """
        Log a scraping operation

        Returns:
            int: Row ID of logged metric
        """
        import hashlib

        # Hash prompt for privacy
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

        metric = ScrapeMetric(
            timestamp=datetime.now().isoformat(),
            url=url,
            prompt_hash=prompt_hash,
            model=model,
            execution_time_seconds=execution_time,
            token_count=token_count,
            retry_count=retry_count,
            fallback_attempts=fallback_attempts,
            cached=cached,
            validation_passed=validation_passed,
            schema_used=schema_used,
            error=error
        )

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO scrapes (
                    timestamp, url, prompt_hash, model, execution_time_seconds,
                    token_count, retry_count, fallback_attempts, cached,
                    validation_passed, schema_used, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.timestamp, metric.url, metric.prompt_hash, metric.model,
                metric.execution_time_seconds, metric.token_count, metric.retry_count,
                metric.fallback_attempts, metric.cached, metric.validation_passed,
                metric.schema_used, metric.error
            ))
            conn.commit()
            return cursor.lastrowid

    def get_recent(self, limit: int = 100) -> List[ScrapeMetric]:
        """Get recent scraping operations"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM scrapes
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            return [ScrapeMetric(**dict(row)) for row in cursor.fetchall()]

    def get_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get aggregate statistics

        Args:
            days: Number of days to analyze

        Returns:
            dict with stats: total_scrapes, avg_time, cache_hit_rate, etc.
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Basic stats
            stats = conn.execute("""
                SELECT
                    COUNT(*) as total_scrapes,
                    AVG(execution_time_seconds) as avg_time,
                    SUM(CASE WHEN cached = 1 THEN 1 ELSE 0 END) as cache_hits,
                    SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) as errors,
                    SUM(CASE WHEN validation_passed = 0 THEN 1 ELSE 0 END) as validation_failures,
                    SUM(retry_count) as total_retries,
                    AVG(token_count) as avg_tokens
                FROM scrapes
                WHERE timestamp >= ?
            """, (cutoff_str,)).fetchone()

            # Model usage
            model_stats = conn.execute("""
                SELECT model, COUNT(*) as count
                FROM scrapes
                WHERE timestamp >= ?
                GROUP BY model
                ORDER BY count DESC
            """, (cutoff_str,)).fetchall()

            result = dict(stats)
            result['cache_hit_rate'] = (result['cache_hits'] / result['total_scrapes'] * 100) if result['total_scrapes'] > 0 else 0
            result['error_rate'] = (result['errors'] / result['total_scrapes'] * 100) if result['total_scrapes'] > 0 else 0
            result['model_usage'] = [dict(row) for row in model_stats]

            return result

    def export_csv(self, output_path: str, days: Optional[int] = None):
        """Export metrics to CSV"""
        import csv
        from datetime import timedelta

        where_clause = ""
        params = ()
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            where_clause = "WHERE timestamp >= ?"
            params = (cutoff_date.isoformat(),)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f"SELECT * FROM scrapes {where_clause} ORDER BY timestamp", params)

            rows = cursor.fetchall()
            if not rows:
                logger.warning("No data to export")
                return

            with open(output_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows([dict(row) for row in rows])

            logger.info(f"✓ Exported {len(rows)} rows to {output_path}")
