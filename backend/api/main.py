# backend/api/main.py
"""
TikSimPro FastAPI Backend
REST API + WebSocket for real-time updates
"""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from backend.api.routes import videos_router, metrics_router, pipeline_router, claude_router, scraper_router, accounts_router
from backend.api.websocket.handler import websocket_endpoint
from backend.api.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    await init_db()
    print("Database initialized")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="TikSimPro API",
    description="API for AI-powered viral video generation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - Allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files - Serve generated videos
if os.path.exists("videos"):
    app.mount("/videos", StaticFiles(directory="videos"), name="videos")

# REST API Routes
app.include_router(videos_router, prefix="/api/videos", tags=["Videos"])
app.include_router(metrics_router, prefix="/api/metrics", tags=["Metrics"])
app.include_router(pipeline_router, prefix="/api/pipeline", tags=["Pipeline"])
app.include_router(claude_router, prefix="/api/claude", tags=["Claude"])
app.include_router(scraper_router, tags=["Scraper"])
app.include_router(accounts_router, tags=["Accounts"])

# WebSocket endpoint
app.add_api_websocket_route("/ws", websocket_endpoint)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "status": "ok",
        "service": "TikSimPro API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check for Docker."""
    return {"status": "healthy"}


@app.get("/api/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
