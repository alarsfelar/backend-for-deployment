from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.db.session import get_db
from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from pydantic import BaseModel, EmailStr

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

class UserRegister(BaseModel):
    email: EmailStr
    phone: str
    name: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register new user and create default folders"""
    
    # Validate password strength
    if len(user_data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if len(user_data.password) > 72:
        raise HTTPException(status_code=400, detail="Password must be less than 72 characters")
    
    # Check if user exists
    result = await db.execute(select(User).where(
        (User.email == user_data.email) | (User.phone == user_data.phone)
    ))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email or phone already registered")
    
    # Create user
    user = User(
        email=user_data.email,
        phone=user_data.phone,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
        is_verified=False
    )
    
    db.add(user)
    await db.flush()
    
    # Create default folders
    from app.models.folder import Folder
    default_folders = [
        {"name": "Bills", "icon": "🧾", "color": "#667eea"},
        {"name": "Hospital Reports", "icon": "🏥", "color": "#f093fb"},
        {"name": "Company", "icon": "🏢", "color": "#4facfe"},
        {"name": "Education", "icon": "🎓", "color": "#43e97b"},
        {"name": "Receipts", "icon": "🧾", "color": "#fa709a"},
        {"name": "Personal", "icon": "👤", "color": "#30cfd0"},
    ]
    
    for idx, folder_data in enumerate(default_folders):
        folder = Folder(
            owner_user_id=user.id,
            name=folder_data["name"],
            icon=folder_data["icon"],
            color=folder_data["color"],
            position=idx
        )
        db.add(folder)
    
    await db.commit()
    await db.refresh(user)

    # Create default "Welcome.txt" file
    try:
        # Find "Personal" folder
        personal_folder = next((f for f in default_folders if f["name"] == "Personal"), None)
        personal_folder_id = None
        
        # We need to query the folder ID since we just added them but didn't refresh all
        # Or we can just look it up
        result = await db.execute(
            select(Folder).where(
                Folder.owner_user_id == user.id,
                Folder.name == "Personal"
            )
        )
        personal_db_folder = result.scalar_one_or_none()
        if personal_db_folder:
            personal_folder_id = personal_db_folder.id

        welcome_content = b"""Welcome to FileFlow!

This is your personal secure cloud storage.
- Upload files and organize them into folders
- Share files securely with other users
- Search your documents instantly

Enjoy!
- The FileFlow Team
"""
        filename = "Welcome.txt"
        
        # Generate storage key
        from app.services.storage import storage_service
        storage_key = storage_service.generate_storage_key(str(user.id), filename)
        
        # Upload content
        import io
        storage_service.upload_file_obj(io.BytesIO(welcome_content), storage_key, "text/plain")
        
        # Create file record
        from app.models.file import File
        from app.config import settings
        
        welcome_file = File(
            owner_user_id=user.id,
            folder_id=personal_folder_id,
            filename=filename,
            original_filename=filename,
            size_bytes=len(welcome_content),
            mime_type="text/plain",
            storage_key=storage_key,
            storage_bucket=settings.B2_BUCKET_NAME,
            checksum_sha256="pending", # TODO: Calculate
            status="uploaded"
        )
        db.add(welcome_file)
        await db.commit()
        
    except Exception as e:
        # Don't fail registration if welcome file fails
        print(f"Failed to create welcome file: {e}")
    
    # Generate tokens
    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "plan": user.plan
        }
    }

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Login user with email/password"""
    
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Generate tokens
    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "plan": user.plan,
            "avatar_url": user.avatar_url
        }
    }

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """Get current authenticated user"""
    from app.core.security import decode_token
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user
