"""
Business Analyst Assistant - FastAPI Application Entry Point.

Provides REST API for AI-assisted requirement discovery and artifact generation.
"""

import logging
import shutil
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import close_db, init_db
from app.middleware import LoggingMiddleware
from app.mcp_server import mcp_app
from app.routes import artifacts, auth, conversations, documents, logs, projects, skills, threads
from app.services.logging_service import get_logging_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize database connection, pre-warm Claude CLI process pool
    - Shutdown: Shutdown process pool, close database connection, cleanup logging
    """
    # Startup: Initialize database
    await init_db()
    print("Database initialized")

    # Startup: Initialize Claude CLI process pool (conditional on CLI availability)
    cli_path = shutil.which("claude")
    if cli_path:
        from app.services.llm.claude_cli_adapter import init_process_pool, DEFAULT_MODEL
        await init_process_pool(cli_path=cli_path, model=DEFAULT_MODEL)
        print("Claude CLI process pool initialized")
    else:
        print("Claude CLI not found, process pool not initialized")

    yield

    # Shutdown: Stop Claude CLI process pool before closing database
    from app.services.llm.claude_cli_adapter import shutdown_process_pool
    await shutdown_process_pool()
    print("Claude CLI process pool shutdown")

    # Shutdown: Cleanup database
    await close_db()
    print("Database connection closed")

    # Shutdown logging service
    logging_service = get_logging_service()
    logging_service.shutdown()
    print("Logging service shutdown")


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

# Configure logging middleware (after CORS to log all requests)
app.add_middleware(LoggingMiddleware)

# Register routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api", tags=["Projects"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(threads.router, prefix="/api", tags=["Threads"])
app.include_router(conversations.router, prefix="/api", tags=["Conversations"])
app.include_router(artifacts.router, prefix="/api", tags=["Artifacts"])
app.include_router(skills.router, prefix="/api", tags=["Skills"])
app.include_router(logs.router)

# Mount FastMCP server at /mcp — Claude CLI subprocesses connect here via --mcp-config.
# MUST be at module level (not inside lifespan) so routes are registered before process pool
# warm-up in lifespan. Avoids ECONNREFUSED on first request (Pitfall 4 from research).
app.mount("/mcp", mcp_app.streamable_http_app())


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
