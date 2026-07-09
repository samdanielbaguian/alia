from typing import List
from fastapi import APIRouter, UploadFile, File, Request, HTTPException, status, Depends
from pathlib import Path
from uuid import uuid4
from time import time

from app.api.deps import get_current_merchant

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
# Maximum files allowed per single upload request
MAX_FILES_PER_REQUEST = 9

# Simple in-memory rate limiter: { ip: (count, window_start_seconds) }
_upload_rate = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 30     # max requests per window per IP

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parents[2] / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_files(request: Request, files: List[UploadFile] = File(...), current_merchant: dict = Depends(get_current_merchant)):
    """
    Upload one or more images. Returns list of accessible URLs.
    """
    # Require at least one file
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files uploaded")

    # enforce max files per request
    if len(files) > MAX_FILES_PER_REQUEST:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Too many files: maximum {MAX_FILES_PER_REQUEST} files allowed per upload")

    # basic rate limiting per IP to reduce abuse
    client_ip = request.client.host if request.client else 'unknown'
    now = int(time())
    entry = _upload_rate.get(client_ip)
    if entry:
        count, window_start = entry
        if now - window_start < RATE_LIMIT_WINDOW:
            if count + 1 > RATE_LIMIT_MAX:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many upload requests, slow down")
            _upload_rate[client_ip] = (count + 1, window_start)
        else:
            _upload_rate[client_ip] = (1, now)
    else:
        _upload_rate[client_ip] = (1, now)

    urls = []
    # validate all files first
    errors = []
    for f in files:
        if not f.content_type or not f.content_type.startswith('image/'):
            errors.append(f"{f.filename}: invalid content type {f.content_type}")
            continue
        content = await f.read()
        if len(content) > MAX_FILE_SIZE:
            errors.append(f"{f.filename}: file too large ({len(content)} bytes). Max {MAX_FILE_SIZE} bytes")
        # store the content temporarily on the UploadFile's file pointer for writing below
        f._content_bytes = content

    if errors:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"errors": errors})

    for f in files:
        # write validated content
        ext = Path(f.filename).suffix or '.jpg'
        filename = f"{uuid4().hex}{ext}"
        dest = UPLOAD_DIR / filename
        content = getattr(f, '_content_bytes', await f.read())
        dest.write_bytes(content)
        base = str(request.base_url).rstrip('/')
        urls.append(f"{base}/uploads/{filename}")

    if not urls:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid image files uploaded")

    return {"urls": urls}
