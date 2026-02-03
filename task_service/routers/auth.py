"""Authentication router."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from task_service.database import get_db
from task_service.models import User
from task_service.auth import get_current_user
from task_service.schemas import UserCreate, UserResponse, UserLogin, Token
from task_service.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Register a new user.
    
    - **email**: User's email address (must be unique)
    - **username**: Username (must be unique, 3-100 characters)
    - **password**: Password (minimum 8 characters)
    """
    user = await UserService.create_user(db, user_create)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    user_login: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Login and get access/refresh tokens.
    
    Returns JWT tokens for authenticated requests.
    """
    return await UserService.login(db, user_login)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current authenticated user information."""
    return UserResponse.model_validate(current_user)
