"""
FileFlow - Quick Start Script
Run this to start the development server
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting FileFlow API Server")
    print("=" * 60)
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    print(f"🌐 Server: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"📖 ReDoc: http://{settings.HOST}:{settings.PORT}/redoc")
    print("=" * 60)
    print("\n⚠️  Make sure you have:")
    print("  ✓ PostgreSQL running")
    print("  ✓ Redis running")
    print("  ✓ .env file configured")
    print("  ✓ Database migrations run (alembic upgrade head)")
    print("\n🔥 Press CTRL+C to stop\n")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
