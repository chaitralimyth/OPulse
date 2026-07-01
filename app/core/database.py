import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

logger = logging.getLogger("app.core.database")

# Create Async engine with Postgres connection pool configuration
engine = create_async_engine(
    settings.async_database_url,
    echo=False,  # Set to True for SQL log outputs during debugging
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True  # Avoid connection drops in postgres pool
)

# Async session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Declarative Base for models
class Base(DeclarativeBase):
    pass
