from sqlalchemy import Column, Boolean, DateTime, String, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database.db import Base
import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import TIMESTAMP


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    is_guest = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)
    email = Column(String, nullable=True, unique=True)
    name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    provider_id = Column(String, nullable=True)

    # Relationship to URLs
    urls = relationship("URL", back_populates="user", cascade="all, delete-orphan")


class URL(Base):
    __tablename__ = "urls"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    short_code = Column(String, unique=True, nullable=False, index=True)
    destination = Column(String, nullable=False)
    is_protected = Column(Boolean, default=False)
    password_hash = Column(Text, nullable=True)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)
    click_limit = Column(Integer, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships to USERS & URL
    user = relationship("User", back_populates="urls")
    clicks = relationship("Click", back_populates="url", cascade="all, delete-orphan")


class Click(Base):
    __tablename__ = "clicks"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    url_id = Column(UUID(as_uuid=True), ForeignKey("urls.id", ondelete="CASCADE"))
    country = Column(String, nullable=True)
    flag = Column(String, nullable=True)
    timestamp = Column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationship to URL
    url = relationship("URL", back_populates="clicks")
