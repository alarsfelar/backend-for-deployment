from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List
from app.db.session import get_db
from app.models.user import User
from app.models.file import File
from app.api.v1.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()

class SearchResult(BaseModel):
    id: str
    filename: str
    size_bytes: int
    mime_type: str
    folder_id: str | None
    created_at: str
    ocr_text: str | None

@router.get("/", response_model=List[SearchResult])
async def search_files(
    q: str = Query(..., min_length=2, description="Search query"),
    folder_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search files by filename or OCR text"""
    
    query = select(File).where(
        File.owner_user_id == current_user.id,
        File.deleted_at.is_(None),
        or_(
            File.filename.ilike(f"%{q}%"),
            File.ocr_text.ilike(f"%{q}%")
        )
    )
    
    if folder_id:
        query = query.where(File.folder_id == folder_id)
    
    result = await db.execute(query.order_by(File.created_at.desc()).limit(50))
    files = result.scalars().all()
    
    return [
        {
            "id": str(file.id),
            "filename": file.filename,
            "size_bytes": file.size_bytes,
            "mime_type": file.mime_type,
            "folder_id": str(file.folder_id) if file.folder_id else None,
            "created_at": file.created_at.isoformat(),
            "ocr_text": file.ocr_text[:200] if file.ocr_text else None
        }
        for file in files
    ]
