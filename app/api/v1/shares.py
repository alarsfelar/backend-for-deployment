from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List
from datetime import datetime
from app.db.session import get_db
from app.models.user import User
from app.models.file import File
from app.models.folder import Folder
from app.models.share import Share
from app.api.v1.auth import get_current_user
from app.core.security import generate_transaction_id
from pydantic import BaseModel, EmailStr

router = APIRouter()

class ShareCreate(BaseModel):
    file_id: str
    recipient_email: EmailStr | None = None
    recipient_phone: str | None = None
    target_folder_name: str
    message: str | None = None
    share_type: str = "direct"  # direct, link, qr

class ShareResponse(BaseModel):
    id: str
    transaction_id: str
    file_id: str
    filename: str
    size_bytes: int  # Added size_bytes
    sender_name: str
    recipient_name: str | None
    target_folder_name: str
    status: str
    created_at: str
    message: str | None

# ... (send_file implementation remains mostly the same, but need to ensure it returns size_bytes if it uses ShareResponse)
# Actually send_file returns a dict, so I need to update that too.

@router.post("/", response_model=ShareResponse, status_code=201)
async def send_file(
    share_data: ShareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # ... (existing code) ...
    # ... (after db.refresh(share)) ...
    
    return {
        "id": str(share.id),
        "transaction_id": share.transaction_id,
        "file_id": str(file.id),
        "filename": file.filename,
        "size_bytes": file.size_bytes, # Added
        "sender_name": current_user.name,
        "recipient_name": share.recipient_name,
        "target_folder_name": share.target_folder_name,
        "status": share.status,
        "created_at": share.created_at.isoformat(),
        "message": share.message
    }

@router.get("/sent", response_model=List[ShareResponse])
async def get_sent_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all sent transactions (like bank statement)"""
    
    result = await db.execute(
        select(Share, File)
        .join(File, Share.file_id == File.id)
        .where(Share.sender_user_id == current_user.id)
        .order_by(Share.created_at.desc())
    )
    
    transactions = []
    for share, file in result.all():
        transactions.append({
            "id": str(share.id),
            "transaction_id": share.transaction_id,
            "file_id": str(file.id),
            "filename": file.filename,
            "size_bytes": file.size_bytes, # Added
            "sender_name": share.sender_name,
            "recipient_name": share.recipient_name or share.recipient_email,
            "target_folder_name": share.target_folder_name,
            "status": share.status,
            "created_at": share.created_at.isoformat(),
            "message": share.message
        })
    
    return transactions

@router.get("/received", response_model=List[ShareResponse])
async def get_received_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all received transactions (inbox)"""
    
    result = await db.execute(
        select(Share, File)
        .join(File, Share.file_id == File.id)
        .where(
            or_(
                Share.recipient_user_id == current_user.id,
                Share.recipient_email == current_user.email
            )
        )
        .order_by(Share.created_at.desc())
    )
    
    transactions = []
    for share, file in result.all():
        transactions.append({
            "id": str(share.id),
            "transaction_id": share.transaction_id,
            "file_id": str(file.id),
            "filename": file.filename,
            "size_bytes": file.size_bytes, # Added
            "sender_name": share.sender_name,
            "recipient_name": current_user.name,
            "target_folder_name": share.target_folder_name,
            "status": share.status,
            "created_at": share.created_at.isoformat(),
            "message": share.message
        })
    
    return transactions

@router.get("/{transaction_id}")
async def get_transaction_details(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get transaction details by transaction ID"""
    
    result = await db.execute(
        select(Share, File)
        .join(File, Share.file_id == File.id)
        .where(
            Share.transaction_id == transaction_id,
            or_(
                Share.sender_user_id == current_user.id,
                Share.recipient_user_id == current_user.id
            )
        )
    )
    
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    share, file = row
    
    return {
        "id": str(share.id),
        "transaction_id": share.transaction_id,
        "file": {
            "id": str(file.id),
            "filename": file.filename,
            "size_bytes": file.size_bytes,
            "mime_type": file.mime_type
        },
        "sender": {
            "name": share.sender_name,
            "email": share.sender_email
        },
        "recipient": {
            "name": share.recipient_name,
            "email": share.recipient_email
        },
        "target_folder": share.target_folder_name,
        "message": share.message,
        "status": share.status,
        "created_at": share.created_at.isoformat(),
        "delivered_at": share.delivered_at.isoformat() if share.delivered_at else None,
        "viewed_at": share.first_viewed_at.isoformat() if share.first_viewed_at else None
    }

@router.get("/{transaction_id}/receipt")
async def get_transaction_receipt(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get official transaction receipt data"""
    
    result = await db.execute(
        select(Share, File)
        .join(File, Share.file_id == File.id)
        .where(
            Share.transaction_id == transaction_id,
            or_(
                Share.sender_user_id == current_user.id,
                Share.recipient_user_id == current_user.id
            )
        )
    )
    
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    share, file = row
    
    # Generate a verification signature
    signature_base = f"{share.transaction_id}:{share.created_at.isoformat()}:{share.sender_user_id}:{share.recipient_user_id}:{file.checksum_sha256}"
    signature = hashlib.sha256(signature_base.encode()).hexdigest()
    
    return {
        "receipt_id": f"RCPT-{share.transaction_id[-8:]}",
        "transaction_id": share.transaction_id,
        "timestamp": share.created_at.isoformat(),
        "status": "SUCCESS" if share.status in ["sent", "delivered", "viewed"] else share.status,
        "sender": {
            "name": share.sender_name,
            "id": str(share.sender_user_id)
        },
        "recipient": {
            "name": share.recipient_name or share.recipient_email,
            "id": str(share.recipient_user_id) if share.recipient_user_id else None
        },
        "item": {
            "name": file.filename,
            "size": file.size_bytes,
            "checksum": file.checksum_sha256
        },
        "verification_signature": signature,
        "legal_disclaimer": "This is a computer generated receipt and does not require a physical signature. Verified by FileFlow."
    }
