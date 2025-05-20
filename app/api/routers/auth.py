from datetime import timedelta
from typing import Any
import sys  # Add this import
import traceback  # Add this import

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import authenticate_user, create_access_token, get_password_hash
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import Token, User as UserSchema, UserCreate

router = APIRouter(tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Validate token and return current user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/auth/register", response_model=UserSchema)
def register_user(
    user_in: UserCreate, db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user
    """
    try:
        print(f"Registering user: {user_in.email}", file=sys.stderr)
        
        # Check if user already exists
        user = db.query(User).filter(User.email == user_in.email).first()
        if user:
            print(f"User already exists: {user_in.email}", file=sys.stderr)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        
        # Create new user
        db_user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            is_active=True,
            is_superuser=False,
            credits=5,  # Give 5 free credits to new users
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        print(f"User registered successfully: {user_in.email}", file=sys.stderr)
        return db_user
    except Exception as e:
        print(f"Error registering user: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        raise


@router.post("/auth/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> Any:
    """
    Get access token for user
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/me", response_model=UserSchema)
def read_users_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user information
    """
    return current_user