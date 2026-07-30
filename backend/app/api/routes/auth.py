from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import random
import logging

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.schemas.auth import Token, LoginRequest, RegisterRequest
from app.schemas.user import UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.verification import VerificationCode

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Register a new user (merchant or buyer).
    
    For merchants, a shop_name is required and a merchant profile is created.
    """
    # Check if user already exists
    existing_user = await db.users.find_one({"email": request.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate role
    if request.role not in ["merchant", "buyer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be either 'merchant' or 'buyer'"
        )
    
    # Validate merchant requirements
    if request.role == "merchant" and not request.shop_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="shop_name is required for merchants"
        )
    
    # Create user with all available fields
    user_data = {
        "email": request.email,
        "password_hash": get_password_hash(request.password),
        "role": request.role,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "age": request.age,
        "birth_date": request.birth_date,
        "phone": request.phone,
        "address": request.address,
        "city": request.city,
        "country": request.country,
        "preferences": request.preferences,
        "good_rate": 50.0,  # Default rating
        "created_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_data)
    user_id = str(result.inserted_id)
    
    # Create merchant profile if role is merchant
    if request.role == "merchant":
        merchant_data = {
            "user_id": user_id,
            "shop_name": request.shop_name,
            "description": request.description or "",
            "phone": request.phone,
            "address": request.address,
            "city": request.city,
            "country": request.country,
            "total_sales": 0.0,
            "rating": 50.0,
            "verified": False,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        await db.merchants.insert_one(merchant_data)
    
    # Create access token with role and user details
    token_data = {
        "sub": user_id,
        "email": new_user["email"],
        "first_name": request.first_name,
        "last_name": request.last_name,
    }
    access_token = create_access_token(data=token_data, role=request.role)
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=Token)
async def login(
    request: LoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Login with email and password.
    
    Returns a JWT access token on success.
    """
    # Find user by email
    user = await db.users.find_one({"email": request.email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token with role and user details
    user_id = str(user["_id"])
    user_role = user.get("role", "buyer")
    token_data = {
        "sub": user_id,
        "email": user["email"],
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
    }
    access_token = create_access_token(data=token_data, role=user_role)
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/google")
async def auth_google():
    """
    Redirect endpoint kept for frontend compatibility.
    """
    return RedirectResponse(url=f"{settings.BASE_URL}/auth/google")


@router.get("/apple")
async def auth_apple():
    """
    Redirect endpoint kept for frontend compatibility.
    """
    return RedirectResponse(url=f"{settings.BASE_URL}/auth/apple")


@router.post("/phone/send-code")
async def send_phone_code(
    payload: dict,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Send a verification code to a phone number.
    
    Generates a random 6-digit code, stores it in the database with a 5-minute expiration,
    and returns the code (for development/testing).
    
    **Request body:**
    ```json
    {
        "phone_number": "+2250712345678"
    }
    ```
    
    **Returns:**
    ```json
    {
        "message": "Verification code sent",
        "phone_number": "+2250712345678",
        "code": "123456",
        "expires_in_seconds": 300,
        "expires_at": "2024-01-15T10:35:00Z"
    }
    ```
    """
    phone_number = payload.get("phone_number")
    if not phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="phone_number is required"
        )
    
    # Delete any existing unverified code for this phone
    await db.verification_codes.delete_many({
        "phone_number": phone_number,
        "verified": {"$ne": True}
    })
    
    # Generate random 6-digit code
    code = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    verification_record = {
        "phone_number": phone_number,
        "code": code,
        "verified": False,
        "attempts": 0,
        "max_attempts": 3,
        "blocked_until": None,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at
    }
    
    result = await db.verification_codes.insert_one(verification_record)
    logger.info(f"Verification code sent to {phone_number} (ID: {result.inserted_id})")
    
    return {
        "message": "Verification code sent",
        "phone_number": phone_number,
        "code": code,  # Return code for development (remove in production)
        "expires_in_seconds": 300,
        "expires_at": expires_at.isoformat()
    }


@router.post("/phone/verify")
async def verify_phone_code(
    payload: dict,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Verify a phone verification code.
    
    Checks if the provided code matches the one sent to the phone number.
    Includes rate limiting and attempt tracking.
    
    **Request body:**
    ```json
    {
        "phone_number": "+2250712345678",
        "code": "123456"
    }
    ```
    
    **Returns:**
    ```json
    {
        "verified": true,
        "phone_number": "+2250712345678",
        "message": "Phone number verified successfully"
    }
    ```
    """
    phone_number = payload.get("phone_number")
    code = payload.get("code")
    
    if not phone_number or not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="phone_number and code are required"
        )
    
    # Find the latest verification record
    verification = await db.verification_codes.find_one(
        {"phone_number": phone_number},
        sort=[("created_at", -1)]
    )
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No verification request found for this phone number"
        )
    
    # Check if blocked due to too many attempts
    if verification.get("blocked_until"):
        blocked_until = verification["blocked_until"]
        if datetime.utcnow() < blocked_until:
            remaining_seconds = int((blocked_until - datetime.utcnow()).total_seconds())
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed attempts. Try again in {remaining_seconds} seconds"
            )
    
    # Check if expired
    if verification["expires_at"] < datetime.utcnow():
        await db.verification_codes.delete_one({"_id": verification["_id"]})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired. Request a new one."
        )
    
    # Check if already verified
    if verification.get("verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This code has already been verified"
        )
    
    # Verify code
    if verification["code"] != code:
        attempts = verification.get("attempts", 0) + 1
        max_attempts = verification.get("max_attempts", 3)
        
        # Check if max attempts exceeded
        if attempts >= max_attempts:
            blocked_until = datetime.utcnow() + timedelta(minutes=15)
            await db.verification_codes.update_one(
                {"_id": verification["_id"]},
                {
                    "$set": {
                        "attempts": attempts,
                        "blocked_until": blocked_until
                    }
                }
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed attempts. Account locked for 15 minutes."
            )
        
        # Update attempt counter
        await db.verification_codes.update_one(
            {"_id": verification["_id"]},
            {"$set": {"attempts": attempts}}
        )
        
        remaining_attempts = max_attempts - attempts
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verification code. {remaining_attempts} attempts remaining."
        )
    
    # Code is valid - mark as verified
    await db.verification_codes.update_one(
        {"_id": verification["_id"]},
        {
            "$set": {
                "verified": True,
                "verified_at": datetime.utcnow()
            }
        }
    )
    
    logger.info(f"Phone number {phone_number} verified successfully")
    
    return {
        "verified": True,
        "phone_number": phone_number,
        "message": "Phone number verified successfully"
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get the current authenticated user's information.
    """
    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        first_name=current_user.get("first_name"),
        last_name=current_user.get("last_name"),
        role=current_user["role"],
        age=current_user.get("age"),
        phone=current_user.get("phone"),
        address=current_user.get("address"),
        city=current_user.get("city"),
        country=current_user.get("country"),
        preferences=current_user.get("preferences", []),
        good_rate=current_user.get("good_rate", 50.0),
        location=current_user.get("location"),
        created_at=current_user["created_at"]
    )


@router.put("/change-password")
async def change_password(
    payload: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Change the current user's password.
    
    Requires the old password to be verified before allowing the change.
    
    **Request body:**
    ```json
    {
        "old_password": "CurrentPassword123!",
        "new_password": "NewPassword456!"
    }
    ```
    
    **Returns:**
    ```json
    {
        "message": "Password changed successfully"
    }
    ```
    """
    old_password = payload.get("old_password")
    new_password = payload.get("new_password")
    
    if not old_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="old_password and new_password are required"
        )
    
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    
    # Verify old password
    if not verify_password(old_password, current_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Old password is incorrect"
        )
    
    # Hash and update new password
    new_password_hash = get_password_hash(new_password)
    await db.users.update_one(
        {"_id": ObjectId(current_user["_id"])},
        {
            "$set": {
                "password_hash": new_password_hash,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Password changed successfully"}
