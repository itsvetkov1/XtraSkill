"""
Business Analyst Assistant - FastAPI Application Entry Point.

Provides REST API for AI-assisted requirement discovery and artifact generation.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import close_db, init_db
from app.routes import artifacts, auth, conversations, documents, projects, threads

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize database connection
    - Shutdown: Close database connection and cleanup
    """
    # Startup: Initialize database
    await init_db()
    print("Database initialized")

    yield

    # Shutdown: Cleanup
    await close_db()
    print("Database connection closed")


# Validate configuration before starting
try:
    settings.validate_required()
except ValueError as e:
    logger.error(f"Configuration validation failed: {e}")
    raise

# Create FastAPI application
app = FastAPI(
    title="Business Analyst Assistant API",
    version="1.0.0",
    description="AI-powered conversational assistant for business requirements discovery",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api", tags=["Projects"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(threads.router, prefix="/api", tags=["Threads"])
app.include_router(conversations.router, prefix="/api", tags=["Conversations"])
app.include_router(artifacts.router, prefix="/api", tags=["Artifacts"])


@app.get("/")
async def root():
    """
    Root endpoint providing API information.

    Returns basic API metadata and links to documentation.
    """
    return {
        "message": "Business Analyst Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for deployment verification.

    Used by PaaS platforms (Railway/Render) to verify service is running.
    """
    return {
        "status": "healthy",
        "database": "connected",
        "version": "1.0.0",
    }
