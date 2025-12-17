# backend/api/routes/__init__.py
from .videos import router as videos_router
from .metrics import router as metrics_router
from .pipeline import router as pipeline_router
from .claude import router as claude_router
from .scraper import router as scraper_router
from .accounts import router as accounts_router

__all__ = ['videos_router', 'metrics_router', 'pipeline_router', 'claude_router', 'scraper_router', 'accounts_router']
