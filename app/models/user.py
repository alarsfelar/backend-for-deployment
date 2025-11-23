from sqlalchemy import Column, String, Boolean, DateTime, Integer, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # MFA
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255))
    
    # Role & Status
    role = Column(String(50), default="user")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Profile
    avatar_url = Column(String(500))
    bio = Column(String(500))
    
    # Subscription
    plan = Column(String(50), default="free")
    storage_used_bytes = Column(BigInteger, default=0)
    storage_quota_bytes = Column(BigInteger, default=5368709120)  # 5GB
    
    # Timestamps
    last_login = Column(DateTime)
    email_verified_at = Column(DateTime)
    phone_verified_at = Column(DateTime)
    deleted_at = Column(DateTime)
    
    # Relationships
    folders = relationship("Folder", back_populates="owner", cascade="all, delete-orphan")
    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")
    sent_shares = relationship("Share", foreign_keys="Share.sender_user_id", back_populates="sender")
    received_shares = relationship("Share", foreign_keys="Share.recipient_user_id", back_populates="recipient")
