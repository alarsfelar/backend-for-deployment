from sqlalchemy import Column, String, Boolean, Integer, BigInteger, ForeignKey, Text, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base, TimestampMixin

class File(Base, TimestampMixin):
    __tablename__ = "files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id", ondelete="SET NULL"))
    
    # File Info
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # Storage
    storage_key = Column(Text, nullable=False)
    storage_bucket = Column(String(255), nullable=False)
    checksum_sha256 = Column(String(64), nullable=False, index=True)
    
    # Version Control
    version = Column(Integer, default=1)
    parent_file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="SET NULL"))
    
    # Processing Status
    status = Column(String(50), default="uploaded")
    virus_scan_status = Column(String(50), default="pending")
    virus_scan_at = Column(DateTime)
    
    # Encryption
    encrypted = Column(Boolean, default=False)
    encryption_key_id = Column(String(255))
    
    # OCR & Metadata
    ocr_text = Column(Text)
    ocr_completed = Column(Boolean, default=False)
    extracted_metadata = Column(JSONB, default={})
    thumbnail_url = Column(Text)
    preview_urls = Column(JSONB, default={})
    
    # User Metadata
    tags = Column(ARRAY(String), default=[])
    description = Column(Text)
    custom_metadata = Column(JSONB, default={})
    
    # Timestamps
    accessed_at = Column(DateTime)
    deleted_at = Column(DateTime)
    
    # Relationships
    owner = relationship("User", back_populates="files")
    folder = relationship("Folder", back_populates="files")
    shares = relationship("Share", back_populates="file", cascade="all, delete-orphan")
    versions = relationship("File", backref="parent_version", remote_side=[id])
