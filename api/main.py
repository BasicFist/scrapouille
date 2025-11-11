"""
FastAPI Server for Scrapouille Backend Integration
Provides REST API endpoints for TypeScript TUIjoli frontend
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import asyncio

# Lazy imports for backend (Phase 2+)
# This allows Phase 1 to run without full scraper dependencies
try:
    from scraper.cache import ScraperCache
    from scraper.metrics import MetricsDB
    from scraper.tui_integration import TUIScraperBackend
    BACKEND_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Backend imports failed (Phase 1 mode): {e}")
    BACKEND_AVAILABLE = False
    ScraperCache = None
    MetricsDB = None
    TUIScraperBackend = None


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared resources on startup, cleanup on shutdown"""
    print("🚀 Starting Scrapouille API Server...")
    print(f"   Backend mode: {'Full' if BACKEND_AVAILABLE else 'Phase 1 (health check only)'}")

    app.state.start_time = datetime.now()
    app.state.backend_available = BACKEND_AVAILABLE

    # Startup: Initialize shared resources (Phase 2+)
    if BACKEND_AVAILABLE:
        app.state.cache = ScraperCache(enabled=True)
        app.state.metrics_db = MetricsDB()
        app.state.backend = TUIScraperBackend(
            cache=app.state.cache,
            metrics_db=app.state.metrics_db
        )

        # Check Ollama connection
        print("🔌 Checking backend connections...")
        ollama_ok = await app.state.backend.check_ollama_connection()
        redis_ok = app.state.cache.enabled

        print(f"   Ollama: {'✓ Connected' if ollama_ok else '✗ Not available'}")
        print(f"   Redis:  {'✓ Connected' if redis_ok else '✗ Not available (caching disabled)'}")
    else:
        app.state.cache = None
        app.state.metrics_db = None
        app.state.backend = None
        print("   ℹ️  Running in Phase 1 mode - scraping endpoints not available")

    print("✅ API Server ready at http://localhost:8000")
    print("📖 API docs: http://localhost:8000/docs")

    yield

    # Shutdown: Cleanup
    print("🛑 Shutting down API Server...")


# Create FastAPI application
app = FastAPI(
    title="Scrapouille API",
    description="AI-powered web scraping with LLM fallback chain",
    version="3.0.5",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware (for potential browser clients and local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # TUI dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:*",     # Any localhost port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === ROOT ENDPOINTS ===

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Scrapouille API",
        "version": "3.0.5",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint - returns server and backend status

    Used by TUI to check API availability and backend connections
    """
    # Calculate uptime
    uptime = (datetime.now() - app.state.start_time).total_seconds()

    # Phase 1 mode (no backend)
    if not app.state.backend_available:
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": round(uptime, 2),
            "version": "3.0.5 (Phase 1)",
            "connections": {
                "ollama": False,
                "redis": False,
            },
            "backend": {
                "cache_enabled": False,
                "metrics_enabled": False,
                "mode": "phase1"
            }
        }

    # Full mode (Phase 2+)
    # Check backend connections
    ollama_connected = await app.state.backend.check_ollama_connection()
    redis_connected = app.state.cache.enabled

    # Determine overall status
    if ollama_connected and redis_connected:
        status = "healthy"
    elif ollama_connected:
        status = "degraded"  # Ollama works but Redis down
    else:
        status = "unhealthy"  # Ollama down (critical)

    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(uptime, 2),
        "version": "3.0.5",
        "connections": {
            "ollama": ollama_connected,
            "redis": redis_connected,
        },
        "backend": {
            "cache_enabled": app.state.cache.enabled,
            "metrics_enabled": True,
        }
    }


# === API ROUTES ===
# Phase 2: Scraping endpoints
if BACKEND_AVAILABLE:
    from api.routes import scrape
    app.include_router(scrape.router, prefix="/api/v1", tags=["scraping"])
    print("   ✓ Scraping endpoints registered")

# Phase 3+: Additional routes (to be added)
# from api.routes import batch, metrics, config
# app.include_router(batch.router, prefix="/api/v1", tags=["batch"])
# app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
# app.include_router(config.router, prefix="/api/v1", tags=["config"])


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 60)
    print("  SCRAPOUILLE API SERVER - PHASE 1 (Foundation)")
    print("=" * 60)
    print("\nStarting server...")
    print("Press Ctrl+C to stop\n")

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
