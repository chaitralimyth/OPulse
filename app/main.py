from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.jobs import start_scheduler, shutdown_scheduler
from app.middleware import RequestLoggingMiddleware, setup_exception_handlers
from app.routers import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    setup_logging()
    start_scheduler()
    yield
    # Shutdown actions
    shutdown_scheduler()

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Scalable Clean Architecture backend for the OPulse AI-powered productivity platform.",
    version="1.0.0",
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

# Set CORS middleware (Production setups would configure specific origins via settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom TIMED logging middleware for API requests
app.add_middleware(RequestLoggingMiddleware)

# Setup Global exception handling responses
setup_exception_handlers(app)

# Include central versioned API router under prefix /api/v1
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint to check service health."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENV,
        "docs_url": f"{settings.API_V1_STR}/docs"
    }
