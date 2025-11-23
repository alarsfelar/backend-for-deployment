from fastapi.responses import FileResponse as FastAPIFileResponse
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import hashlib
from app.db.session import get_db
from app.models.user import User
from app.models.file import File
from app.api.v1.auth import get_current_user
from app.services.storage import storage_service
from app.config import settings
from pydantic import BaseModel

router = APIRouter()

class FileUploadInit(BaseModel):
    filename: str
    size_bytes: int
    mime_type: str
    folder_id: str | None = None

class FileUploadResponse(BaseModel):
    upload_url: str
    storage_key: str
    file_id: str

class FileResponse(BaseModel):
    id: str
    filename: str
    size_bytes: int
    mime_type: str
    folder_id: str | None
    created_at: str
    thumbnail_url: str | None
    view_url: str | None

@router.post("/upload/init", response_model=FileUploadResponse)
async def init_upload(
    upload_data: FileUploadInit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Initialize file upload - returns presigned URL for direct S3 upload"""
    
    # Validate file size
    if upload_data.size_bytes <= 0:
        raise HTTPException(status_code=400, detail="Invalid file size")
    
    # Check storage quota
    if current_user.storage_used_bytes + upload_data.size_bytes > current_user.storage_quota_bytes:
        raise HTTPException(
            status_code=400, 
            detail=f"Storage quota exceeded. Used: {current_user.storage_used_bytes / (1024**3):.2f}GB / {current_user.storage_quota_bytes / (1024**3):.2f}GB"
        )
    
    # Check file size limit
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if upload_data.size_bytes > max_size:
        raise HTTPException(status_code=400, detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit")
    
    # Validate file type (basic security)
    # Validate file type (basic security)
    # dangerous_extensions = ['.exe', '.bat', '.cmd', '.sh', '.ps1']
    # if any(upload_data.filename.lower().endswith(ext) for ext in dangerous_extensions):
    #     raise HTTPException(status_code=400, detail="File type not allowed for security reasons")
    
    # Generate storage key
    storage_key = storage_service.generate_storage_key(str(current_user.id), upload_data.filename)
    
    # Create file record
    file = File(
        owner_user_id=current_user.id,
        folder_id=upload_data.folder_id,
        filename=upload_data.filename,
        original_filename=upload_data.filename,
        size_bytes=upload_data.size_bytes,
        mime_type=upload_data.mime_type,
        storage_key=storage_key,
        storage_bucket=settings.B2_BUCKET_NAME,
        checksum_sha256="pending",
        status="uploading"
    )
    
    db.add(file)
    await db.commit()
    await db.refresh(file)
    
    # Generate presigned upload URL
    upload_url = storage_service.create_presigned_upload_url(storage_key, upload_data.mime_type)
    
    return {
        "upload_url": upload_url,
        "storage_key": storage_key,
        "file_id": str(file.id)
    }

@router.post("/upload/direct", response_model=FileResponse)
async def upload_file_direct(
    file: UploadFile = FastAPIFile(...),
    folder_id: str | None = Form(None),
    is_hidden: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Direct file upload (server-side proxy) to bypass CORS issues"""
    
    # Validate file size (read from header or check chunk by chunk, but for now rely on Nginx/FastAPI limits)
    # Note: FastAPI spools to memory/temp file.
    
    # Check storage quota (approximate since we don't know exact size yet, or use Content-Length)
    # For simplicity in this proxy, we'll check after or assume it fits if small enough.
    # Better: Check Content-Length header if available.
    
    size_bytes = 0
    # We need to calculate size. file.file is a SpooledTemporaryFile.
    file.file.seek(0, 2)
    size_bytes = file.file.tell()
    file.file.seek(0)
    
    if current_user.storage_used_bytes + size_bytes > current_user.storage_quota_bytes:
        raise HTTPException(status_code=400, detail="Storage quota exceeded")

    # Generate storage key
    storage_key = storage_service.generate_storage_key(str(current_user.id), file.filename)
    
    # Upload to S3
    try:
        storage_service.upload_file_obj(file.file, storage_key, file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    # Create file record
    db_file = File(
        owner_user_id=current_user.id,
        folder_id=folder_id,
        filename=file.filename,
        original_filename=file.filename,
        size_bytes=size_bytes,
        mime_type=file.content_type,
        storage_key=storage_key,
        storage_bucket=settings.B2_BUCKET_NAME,
        checksum_sha256="pending",
        status="hidden" if is_hidden else "uploaded"
    )
    
    db.add(db_file)
    
    # Update user storage
    current_user.storage_used_bytes += size_bytes
    
    await db.commit()
    await db.refresh(db_file)
    
    # Trigger background tasks
    from app.workers.tasks import process_file_ocr, generate_thumbnail
    process_file_ocr.delay(str(db_file.id), db_file.storage_key, db_file.mime_type)
    generate_thumbnail.delay(str(db_file.id), db_file.storage_key, db_file.mime_type)
    
    # Generate view URL
    # For B2/S3, we can generate a direct presigned URL for viewing
    if hasattr(storage_service, 'create_presigned_view_url'):
        view_url = storage_service.create_presigned_view_url(db_file.storage_key, db_file.mime_type)
    else:
        # Fallback for local storage or if method missing
        view_url = f"{settings.API_V1_PREFIX}/files/download/proxy?key={db_file.storage_key}&disposition=inline"
    
    return {
        "id": str(db_file.id),
        "filename": db_file.filename,
        "size_bytes": db_file.size_bytes,
        "mime_type": db_file.mime_type,
        "folder_id": str(db_file.folder_id) if db_file.folder_id else None,
        "created_at": db_file.created_at.isoformat(),
        "thumbnail_url": None,
        "view_url": view_url
    }

@router.post("/upload/{file_id}/complete")
async def complete_upload(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark upload as complete and update user storage"""
    
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.owner_user_id == current_user.id
        )
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Update file status
    file.status = "uploaded"
    
    # Update user storage
    current_user.storage_used_bytes += file.size_bytes
    
    await db.commit()
    
    # Trigger background tasks
    from app.workers.tasks import process_file_ocr, generate_thumbnail
    
    process_file_ocr.delay(str(file.id), file.storage_key, file.mime_type)
    generate_thumbnail.delay(str(file.id), file.storage_key, file.mime_type)
    
    return {"message": "Upload completed", "file_id": str(file.id)}

@router.get("/", response_model=List[FileResponse])
async def get_files(
    folder_id: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get files for current user with pagination and search"""
    # Validate pagination
    if limit > 100:
        limit = 100
    if offset < 0:
        offset = 0
    
    query = select(File).where(
        File.owner_user_id == current_user.id, 
        File.deleted_at.is_(None),
        File.status != "hidden"
    )
    
    if folder_id:
        query = query.where(File.folder_id == folder_id)
        
    if search:
        query = query.where(File.filename.ilike(f"%{search}%"))
    
    result = await db.execute(query.order_by(File.created_at.desc()).limit(limit).offset(offset))
    files = result.scalars().all()
    
    return [
        {
            "id": str(file.id),
            "filename": file.filename,
            "size_bytes": file.size_bytes,
            "mime_type": file.mime_type,
            "folder_id": str(file.folder_id) if file.folder_id else None,
            "created_at": file.created_at.isoformat(),
            "thumbnail_url": file.thumbnail_url,
            "thumbnail_url": file.thumbnail_url,
            "view_url": storage_service.create_presigned_view_url(file.storage_key, file.mime_type) if hasattr(storage_service, 'create_presigned_view_url') else f"{settings.API_V1_PREFIX}/files/download/proxy?key={file.storage_key}&disposition=inline"
        }
        for file in files
    ]

@router.get("/download/proxy")
async def download_proxy(
    key: str,
    disposition: str = "attachment",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Proxy download for local storage"""
    # Security check: Ensure the user owns the file associated with this key
    # This is a bit tricky since we only have the key. 
    # Ideally we should look up the file by ID, but the URL structure uses the key.
    # Let's verify the key format or look it up.
    
    # Better approach: The frontend calls /files/{id}/download, which returns this proxy URL.
    # So the user already authenticated there. 
    # But this endpoint itself needs protection.
    # For now, we'll allow it if authenticated, but in production we should verify ownership.
    # We can query the DB to check if any file with this storage_key belongs to the user.
    
    result = await db.execute(
        select(File).where(
            File.storage_key == key,
            File.owner_user_id == current_user.id
        )
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found or access denied")
        
    if not os.path.exists(key):
        raise HTTPException(status_code=404, detail="File not found on server")
        
    return FastAPIFileResponse(
        path=key, 
        filename=file.original_filename if disposition == "attachment" else None,
        media_type=file.mime_type,
        content_disposition_type=disposition
    )

import os

@router.get("/{file_id}/download")
async def get_download_url(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get download URL (direct file stream for local storage)"""
    
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.owner_user_id == current_user.id
        )
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # For local storage, we can just return the file directly if we change the frontend to expect a blob
    # OR we return a URL that points to a download endpoint.
    # Let's use the proxy approach.
    
    # If using LocalStorageService, the URL will be /api/v1/files/download/proxy?key=...
    download_url = storage_service.create_presigned_download_url(
        file.storage_key,
        filename=file.original_filename
    )
    
    # If the URL is relative (starts with /), prepend the API URL if needed, 
    # but since it's an API response, the frontend might expect a full URL.
    # Let's make sure it works.
    if download_url.startswith("/"):
        # It's a local path, construct full URL
        # We need the base URL. For now, let's return it as is and ensure frontend handles it.
        pass

    return {
        "download_url": download_url,
        "filename": file.original_filename,
        "expires_in": settings.S3_PRESIGNED_URL_EXPIRY
    }

@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete file (soft delete)"""
    from datetime import datetime
    
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.owner_user_id == current_user.id
        )
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Soft delete
    file.deleted_at = datetime.utcnow()
    
    # Update user storage
    current_user.storage_used_bytes -= file.size_bytes
    
    await db.commit()
    
    return {"message": "File deleted successfully"}
