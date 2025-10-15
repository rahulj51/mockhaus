"""
This module configures and initializes the FastAPI application for the Mockhaus server.

It sets up the application lifecycle, middleware, and API routers, creating a
cohesive server that emulates the Snowflake SQL REST API while using DuckDB as
its backend.

Key responsibilities include:
- Defining the application's startup and shutdown events, such as initializing
  the ConcurrentSessionManager.
- Configuring middleware for CORS, request logging, and optional debug logging.
- Including API routers for different versions and functionalities, such as the
  v1 health and query endpoints, and the v2 Snowflake API endpoints.
- Providing a root endpoint for basic server information.
"""

import os
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends

from ..banner import print_server_banner
from .middleware.cors import add_cors_middleware
from .middleware.debug_logging import add_debug_logging_middleware
from .middleware.logging import add_logging_middleware
from .routes import health, query, sessions
from .snowflake_api import routes as snowflake_routes
from .state import server_state
from .concurrent_session_manager import ConcurrentSessionManager, SessionContext
from .dependencies import get_session_manager


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle."""
    # Startup: initialize server state and print banner
    host = os.environ.get("MOCKHAUS_HOST", "0.0.0.0")
    port = int(os.environ.get("MOCKHAUS_PORT", "8080"))
    print_server_banner(host, port)
    await get_session_manager().start()
    yield
    # Shutdown: cleanup server state
    await server_state.shutdown()
    await get_session_manager().shutdown()


# Create FastAPI application
app = FastAPI(
    title="Mockhaus Server",
    description="Snowflake proxy with DuckDB backend - HTTP API for SQL translation and execution",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add middleware
add_cors_middleware(app)
add_logging_middleware(app)

# Add debug logging if MOCKHAUS_DEBUG is set
debug_enabled = os.environ.get("MOCKHAUS_DEBUG", "").lower() in ("true", "1", "yes")
add_debug_logging_middleware(app, debug=debug_enabled)

# Include routers
app.include_router(query.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(snowflake_routes.router, prefix="/api/v2")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with basic server information."""
    return {
        "name": "Mockhaus Server",
        "version": "0.3.0",
        "description": "Snowflake proxy with DuckDB backend",
        "docs_url": "/docs",
        "health_url": "/api/v1/health",
    }
