from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.api.deps import get_db, get_current_user
from app.schemas.auth import Token, LoginRequest, RegisterRequest
from app.schemas.user import UserResponse
from app.schemas.phone_auth import SendPhoneCodeRequest, VerifyPhoneCodeRequest
from app.core.security import get_password_hash, verify_password, create_access_token

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
    
    # Create user
    user_data = {
        "email": request.email,
        "password_hash": get_password_hash(request.password),
        "role": request.role,
        "age": request.age,
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
            "description": "",
            "total_sales": 0.0,
            "rating": 50.0,
            "created_at": datetime.utcnow()
        }
        await db.merchants.insert_one(merchant_data)
    
    # Create access token with role
    access_token = create_access_token(data={"sub": user_id}, role=request.role)
    
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
    
    # Create access token with role
    user_id = str(user["_id"])
    user_role = user.get("role", "buyer")
    access_token = create_access_token(data={"sub": user_id}, role=user_role)
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get the current authenticated user's information.
    """
    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        role=current_user["role"],
        age=current_user.get("age"),
        preferences=current_user.get("preferences", []),
        good_rate=current_user.get("good_rate", 50.0),
        location=current_user.get("location"),
        created_at=current_user["created_at"]
    )


@router.post("/google")
async def google_auth():
    """
    Initiate Google OAuth authentication.
    
    TODO: Implement Google OAuth flow
    - Redirect to Google OAuth consent screen
    - Handle callback with authorization code
    - Exchange code for tokens
    - Create/login user
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google OAuth is not yet implemented. Please use email/password registration."
    )


@router.post("/apple")
async def apple_auth():
    """
    Initiate Apple Sign In authentication.
    
    TODO: Implement Apple Sign In flow
    - Redirect to Apple authentication
    - Handle callback with authorization code
    - Verify and decode identity token
    - Create/login user
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Apple Sign In is not yet implemented. Please use email/password registration."
    )


@router.post("/phone/send-code")
async def send_phone_code(
    request: SendPhoneCodeRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Send verification code to phone number.
    
    TODO: Implement SMS sending via Twilio or similar service
    - Validate phone number format
    - Generate 6-digit code
    - Store code with expiration (5 minutes)
    - Send SMS via provider
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Phone authentication is not yet implemented. Please use email/password registration."
    )


@router.post("/phone/verify")
async def verify_phone_code(
    request: VerifyPhoneCodeRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Verify phone code and login/register user.
    
    TODO: Implement phone verification
    - Validate code against stored code
    - Check expiration
    - Create user if doesn't exist
    - Generate JWT token
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Phone authentication is not yet implemented. Please use email/password registration."
    )
