from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.db import get_session
from models.models import User
from api import user_urls, redirect, delete_url, verify_password
from api import dashboard_overview
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(user_urls.router, tags=["URL Shortener: Guest"])
app.include_router(redirect.router, tags=["URL REDIRECTION"])
app.include_router(dashboard_overview.router, tags=["DASHBOARD SUMMARY"])
app.include_router(verify_password.router, tags=["PASSCODE VERIFICATION"])
app.include_router(delete_url.router, tags=["DELETE URL"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/1/health")
async def health_check():
    return {"status": "healthy"}