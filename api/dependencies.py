"""
FastAPI Dependency Injection
Provides shared resources (cache, metrics, backend) to route handlers
"""

from fastapi import Depends, Request
from scraper.cache import ScraperCache
from scraper.metrics import MetricsDB
from scraper.tui_integration import TUIScraperBackend


def get_cache(request: Request) -> ScraperCache:
    """Get shared cache instance from app state"""
    return request.app.state.cache


def get_metrics_db(request: Request) -> MetricsDB:
    """Get shared metrics database from app state"""
    return request.app.state.metrics_db


def get_backend(request: Request) -> TUIScraperBackend:
    """Get shared scraper backend from app state"""
    return request.app.state.backend
