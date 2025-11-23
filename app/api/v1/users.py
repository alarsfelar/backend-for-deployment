from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
from app.api.v1.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()

class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    phone: str | None
    plan: str
    storage_used_bytes: int
    storage_quota_bytes: int
    avatar_url: str | None
    is_verified: bool

@router.get("/me", response_model=UserProfile)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "phone": current_user.phone,
        "plan": current_user.plan,
        "storage_used_bytes": current_user.storage_used_bytes,
        "storage_quota_bytes": current_user.storage_quota_bytes,
        "avatar_url": current_user.avatar_url,
        "is_verified": current_user.is_verified
    }

@router.get("/storage")
async def get_storage_info(current_user: User = Depends(get_current_user)):
    """Get storage usage information"""
    used_gb = current_user.storage_used_bytes / (1024**3)
    quota_gb = current_user.storage_quota_bytes / (1024**3)
    percentage = (current_user.storage_used_bytes / current_user.storage_quota_bytes) * 100
    
    return {
        "used_bytes": current_user.storage_used_bytes,
        "quota_bytes": current_user.storage_quota_bytes,
        "used_gb": round(used_gb, 2),
        "quota_gb": round(quota_gb, 2),
        "percentage": round(percentage, 2),
        "available_bytes": current_user.storage_quota_bytes - current_user.storage_used_bytes
    }
