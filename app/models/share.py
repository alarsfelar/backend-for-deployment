from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base, TimestampMixin

class Share(Base, TimestampMixin):
    """Transaction model - like UPI transactions for files"""
    __tablename__ = "shares"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # What's being shared
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    
    # Sender (Who's sharing)
    sender_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    sender_name = Column(String(255))
    sender_email = Column(String(255))
    
    # Recipient (Who receives)
    recipient_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    recipient_email = Column(String(255))
    recipient_phone = Column(String(20))
    recipient_name = Column(String(255))
    
    # Destination
    target_folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id", ondelete="SET NULL"))
    target_folder_name = Column(String(255))
    
    # Transaction Details
    message = Column(Text)
    share_type = Column(String(50), default="direct")  # direct, link, qr
    transaction_id = Column(String(100), unique=True, index=True)
    
    # Status (Like UPI transaction status)
    status = Column(String(50), default="sent")  # sent, delivered, viewed, failed, revoked
    
    # Link Sharing
    share_token = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    expires_at = Column(DateTime)
    max_views = Column(Integer)
    view_count = Column(Integer, default=0)
    
    # Permissions
    permissions = Column(JSONB, default={"view": True, "download": True, "share": False})
    
    # Timestamps (Transaction timeline)
    delivered_at = Column(DateTime)
    first_viewed_at = Column(DateTime)
    last_viewed_at = Column(DateTime)
    revoked_at = Column(DateTime)
    
    # Audit
    share_metadata = Column(JSONB, default={})
    ip_address = Column(String(50))
    user_agent = Column(Text)
    
    # Relationships
    file = relationship("File", back_populates="shares")
    sender = relationship("User", foreign_keys=[sender_user_id], back_populates="sent_shares")
    recipient = relationship("User", foreign_keys=[recipient_user_id], back_populates="received_shares")
