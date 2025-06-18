from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from database.db import get_session, check_database_connection
from models.models import User
from api import user_urls, redirect, delete_url, verify_password, updateuser
from api import dashboard_overview
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting up FastAPI application...")
    logger.info(f"DATABASE_URL configured: {bool(os.getenv('DATABASE_URL'))}")
    logger.info(f"SUPABASE_URL configured: {bool(os.getenv('SUPABASE_URL'))}")
    
    # Test database connection
    db_connected = await check_database_connection()
    if db_connected:
        logger.info("✅ Database connection successful on startup")
    else:
        logger.error("❌ Database connection failed on startup")
    
    yield
    
    # Shutdown (optional cleanup)
    logger.info("🛑 Shutting down FastAPI application...")

app = FastAPI(lifespan=lifespan)

# Include all your routers
app.include_router(user_urls.router, tags=["URL Shortener: Guest"])
app.include_router(redirect.router, tags=["URL REDIRECTION"])
app.include_router(dashboard_overview.router, tags=["DASHBOARD SUMMARY"])
app.include_router(verify_password.router, tags=["PASSCODE VERIFICATION"])
app.include_router(updateuser.router, tags=["UPDATE USER DATA"])
app.include_router(delete_url.router, tags=["DELETE URL"])

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Dev
        "https://redirec-to.vercel.app",  # Prod
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/1/health")
async def health_check():
    """Enhanced health check endpoint with database testing"""
    try:
        # Test database connection
        db_connected = await check_database_connection()
        
        if db_connected:
            return {
                "status": "healthy", 
                "database": "connected",
                "message": "All systems operational",
                "environment": "railway" if os.getenv("RAILWAY_ENVIRONMENT") else "local"
            }
        else:
            return {
                "status": "unhealthy", 
                "database": "disconnected",
                "message": "Database connection failed",
                "environment": "railway" if os.getenv("RAILWAY_ENVIRONMENT") else "local"
            }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Health check failed: {str(e)}"
        )