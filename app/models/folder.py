from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base, TimestampMixin

class Folder(Base, TimestampMixin):
    __tablename__ = "folders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id", ondelete="CASCADE"))
    
    # Folder Info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    icon = Column(String(50), default="📁")
    color = Column(String(20), default="#667eea")
    
    # Settings
    visibility = Column(String(20), default="private")
    default_retention_days = Column(Integer, default=365)
    auto_categorize = Column(Boolean, default=True)
    position = Column(Integer, default=0)
    
    # Relationships
    owner = relationship("User", back_populates="folders")
    files = relationship("File", back_populates="folder", cascade="all, delete-orphan")
    subfolders = relationship("Folder", backref="parent", remote_side=[id])
