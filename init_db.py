"""Initialize database - Run this once to create all tables"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings
from app.db.base import Base
from app.models import user, folder, file, share

async def init_db():
    print("Creating database tables...")
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Drop all tables
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
