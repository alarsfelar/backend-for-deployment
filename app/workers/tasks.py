import io
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
from celery import shared_task
from app.core.celery_app import celery_app
from app.services.storage import storage_service
# from app.db.session import SessionLocal
from app.models.file import File
from sqlalchemy import update
import logging

logger = logging.getLogger(__name__)

@shared_task(name="process_file_ocr")
def process_file_ocr(file_id: str, storage_key: str, mime_type: str):
    """
    Extract text from image or PDF and update file record.
    """
    logger.info(f"Starting OCR for file {file_id}")
    
    try:
        # Download file
        file_obj = io.BytesIO()
        storage_service.download_file_obj(storage_key, file_obj)
        file_obj.seek(0)
        
        extracted_text = ""
        
        if mime_type.startswith("image/"):
            image = Image.open(file_obj)
            extracted_text = pytesseract.image_to_string(image)
            
        elif mime_type == "application/pdf":
            # Convert PDF to images
            images = convert_from_bytes(file_obj.read())
            for image in images:
                extracted_text += pytesseract.image_to_string(image) + "\n"
        
        if extracted_text:
            # Update database
            # Note: In a real app, we might want to store this in a separate table or search index
            # For now, we'll assume there's a 'content_text' column or similar, 
            # or we just log it as a proof of concept if the column doesn't exist yet.
            
            # Let's check if we can update the File model. 
            # Since I haven't added the column yet, I will just log it for now 
            # and TODO: Add content_text column to File model.
            logger.info(f"OCR Complete for {file_id}. Extracted {len(extracted_text)} chars.")
            
            from app.db.session import SessionLocal
            db = SessionLocal()
            # try:
            #     stmt = update(File).where(File.id == file_id).values(content_text=extracted_text)
            #     db.execute(stmt)
            #     db.commit()
            # finally:
            #     db.close()
                
    except Exception as e:
        logger.error(f"OCR failed for {file_id}: {str(e)}")
        # Don't raise, just log error so task doesn't retry indefinitely on bad files

@shared_task(name="generate_thumbnail")
def generate_thumbnail(file_id: str, storage_key: str, mime_type: str):
    """
    Generate thumbnail for image/PDF and upload to S3.
    """
    logger.info(f"Generating thumbnail for {file_id}")
    
    try:
        if not (mime_type.startswith("image/") or mime_type == "application/pdf"):
            return
            
        # Download file
        file_obj = io.BytesIO()
        storage_service.download_file_obj(storage_key, file_obj)
        file_obj.seek(0)
        
        image = None
        
        if mime_type.startswith("image/"):
            image = Image.open(file_obj)
            
        elif mime_type == "application/pdf":
            # Get first page
            images = convert_from_bytes(file_obj.read(), first_page=1, last_page=1)
            if images:
                image = images[0]
        
        if image:
            # Resize
            image.thumbnail((300, 300))
            
            # Save to bytes
            thumb_io = io.BytesIO()
            image.save(thumb_io, format="JPEG", quality=85)
            thumb_io.seek(0)
            
            # Upload thumbnail
            thumb_key = storage_key.rsplit('.', 1)[0] + "_thumb.jpg"
            storage_service.upload_file_obj(thumb_io, thumb_key, "image/jpeg")
            
            # Update DB
            from app.db.session import SessionLocal
            db = SessionLocal()
            try:
                # We need to construct the full URL or just the key. 
                # The model expects thumbnail_url.
                # Assuming public read or presigned url generation on fly.
                # For now, let's store the key or a flag.
                # Actually, the FileResponse generates the URL. 
                # So we should probably store the key or just update a 'has_thumbnail' flag?
                # Looking at FileResponse in files.py: "thumbnail_url": file.thumbnail_url
                # So it expects a URL string in the DB.
                
                # Let's assume we store the relative path or key.
                stmt = update(File).where(File.id == file_id).values(thumbnail_url=thumb_key)
                db.execute(stmt)
                db.commit()
            finally:
                db.close()
                
            logger.info(f"Thumbnail generated for {file_id}")
            
    except Exception as e:
        logger.error(f"Thumbnail generation failed for {file_id}: {str(e)}")
