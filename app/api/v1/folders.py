from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.session import get_db
from app.models.user import User
from app.models.folder import Folder
from app.models.file import File
from app.api.v1.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()

class FolderCreate(BaseModel):
    name: str
    description: str | None = None
    icon: str = "📁"
    color: str = "#667eea"
    parent_folder_id: str | None = None

class FolderResponse(BaseModel):
    id: str
    name: str
    description: str | None
    icon: str
    color: str
    file_count: int = 0
    position: int

@router.get("/", response_model=List[FolderResponse])
async def get_folders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all folders for current user"""
    from sqlalchemy import func
    
    result = await db.execute(
        select(
            Folder.id,
            Folder.name,
            Folder.description,
            Folder.icon,
            Folder.color,
            Folder.position,
            func.count(File.id).label('file_count')
        )
        .outerjoin(File, (File.folder_id == Folder.id) & (File.deleted_at.is_(None)))
        .where(Folder.owner_user_id == current_user.id)
        .group_by(Folder.id, Folder.name, Folder.description, Folder.icon, Folder.color, Folder.position)
        .order_by(Folder.position)
    )
    
    folders = result.all()
    
    return [
        {
            "id": str(row.id),
            "name": row.name,
            "description": row.description,
            "icon": row.icon,
            "color": row.color,
            "file_count": row.file_count or 0,
            "position": row.position
        }
        for row in folders
    ]

@router.post("/", response_model=FolderResponse, status_code=201)
async def create_folder(
    folder_data: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new folder"""
    # Calculate position
    from sqlalchemy import func
    result = await db.execute(
        select(func.max(Folder.position)).where(Folder.owner_user_id == current_user.id)
    )
    max_position = result.scalar()
    new_position = (max_position + 1) if max_position is not None else 0

    folder = Folder(
        owner_user_id=current_user.id,
        name=folder_data.name,
        description=folder_data.description,
        icon=folder_data.icon,
        color=folder_data.color,
        parent_folder_id=folder_data.parent_folder_id,
        position=new_position
    )
    
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    
    return {
        "id": str(folder.id),
        "name": folder.name,
        "description": folder.description,
        "icon": folder.icon,
        "color": folder.color,
        "file_count": 0,
        "position": folder.position
    }

@router.delete("/{folder_id}")
async def delete_folder(
    folder_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete folder"""
    result = await db.execute(
        select(Folder).where(
            Folder.id == folder_id,
            Folder.owner_user_id == current_user.id
        )
    )
    folder = result.scalar_one_or_none()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    await db.delete(folder)
    await db.commit()
    
    return {"message": "Folder deleted successfully"}
