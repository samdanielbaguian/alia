"""
File upload routes for Alia marketplace.

Handles file uploads for:
- Product images
- User avatars
- Shop banners
- Merchant documentation
"""

import os
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Request
from fastapi.responses import FileResponse
from app.api.deps import get_current_user, get_db
import logging
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# Create uploads directory if it doesn't exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("", tags=["Uploads"])
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="Image file to upload"),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Upload an image file.
    
    Accepts JPEG, PNG, GIF, WebP images (max 10MB).
    Returns the file URL for use in product/profile data.
    
    **Authentication required**
    """
    # Validate file exists
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Prevent directory traversal in supplied filename
    filename = Path(file.filename).name
    file_ext = Path(filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        mime_extensions = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
        }
        file_ext = mime_extensions.get(file.content_type, "")
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: 10MB"
        )
    
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )
    
    # Generate unique filename
    unique_name = f"{uuid.uuid4()}{file_ext}"
    file_path = (UPLOAD_DIR / unique_name).resolve()
    uploads_root = UPLOAD_DIR.resolve()
    if not str(file_path).startswith(str(uploads_root) + os.sep):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name"
        )
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Build file URL relative to the backend host so the frontend can load uploaded images
    # Normalize 127.0.0.1 -> localhost to avoid origin issues in some dev setups
    try:
        base_url = str(request.base_url).rstrip('/')
        base_url = base_url.replace('127.0.0.1', 'localhost')
    except Exception:
        base_url = getattr(settings, 'BASE_URL', '').rstrip('/') if getattr(settings, 'BASE_URL', None) else ''
    if not base_url:
        base_url = str(request.base_url).rstrip('/').replace('127.0.0.1', 'localhost')
    file_url = f"{base_url}/uploads/{unique_name}"

    # Log upload event
    try:
        user_id = getattr(current_user, '_id', None) or (current_user.get('_id') if isinstance(current_user, dict) else None)
    except Exception:
        user_id = None
    logger.info(f"Upload saved: user={user_id} file={unique_name} size={len(content)} path={file_path}")
    
    return {
        "url": file_url,
        "filename": file.filename,
        "size": len(content),
        "path": str(file_path)
    }


@router.get("/{filename}", tags=["Uploads"])
async def get_file(filename: str):
    """
    Retrieve an uploaded file.
    
    Serves files from the uploads directory.
    """
    file_path = (UPLOAD_DIR / filename).resolve()
    uploads_root = UPLOAD_DIR.resolve()
    if not file_path.exists() or not str(file_path).startswith(str(uploads_root) + os.sep):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileResponse(file_path)
