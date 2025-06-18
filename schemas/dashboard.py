from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class URLData(BaseModel):
    id: str
    shortUrl: str
    destination: str
    clicks: int
    ttl: str
    status: str
    protected: bool
    createdAt: str


class RecentClick(BaseModel):
    time: str
    country: str
    flag: str


class SummaryData(BaseModel):
    totalUrls: int
    totalClicks: int
    protectedUrls: int
    recentClick: Optional[RecentClick]


class ClickData(BaseModel):
    day: str
    clicks: int


class CountryData(BaseModel):
    country: str
    clicks: int
    color: str


class Activity(BaseModel):
    id: str
    shortUrl: str
    country: str
    flag: str
    time: str


# Pydantic models
class UserPayload(BaseModel):
    id: str
    is_guest: bool
    email: Optional[str]
    name: Optional[str]
    avatar_url: Optional[str]
    provider: Optional[str]
    provider_id: Optional[str] = None


class CreateUrlRequest(BaseModel):
    long_url: str
    user: UserPayload
    expires_at: Optional[str] = None
    click_limit: Optional[int] = None
    password: Optional[str] = None
    is_protected: Optional[bool] = False


class CreateUrlResponse(BaseModel):
    short_url: str
    long_url: str
    user_id: str


class VerifyPasswordRequest(BaseModel):
    short_code: str
    password: str


class VerifyPasswordResponse(BaseModel):
    destination: str
