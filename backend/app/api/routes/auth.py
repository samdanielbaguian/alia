from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.schemas.auth import Token, LoginRequest, RegisterRequest
from app.schemas.user import UserResponse
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
    
    # Create access token
    access_token = create_access_token(data={"sub": user_id})
    
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
    
    # Create access token
    user_id = str(user["_id"])
    access_token = create_access_token(data={"sub": user_id})
    
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
