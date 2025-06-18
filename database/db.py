from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text
from dotenv import load_dotenv
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Railway + Supabase optimized engine configuration
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for debugging SQL queries
    pool_pre_ping=True,          # Verify connections before use
    pool_recycle=300,            # Recycle connections every 5 minutes
    pool_size=3,                 # Smaller pool for Railway
    max_overflow=5,              # Additional connections if needed
    pool_timeout=30,             # Connection timeout in seconds
    connect_args={
        "ssl": "require",        # Force SSL for production
        "server_settings": {
            "application_name": "railway_fastapi_app",
        }
    }
)


async_session_maker = sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

Base = declarative_base()

async def get_session():
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# Health check function for database
async def check_database_connection():
    """Test database connection for health checks"""
    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False