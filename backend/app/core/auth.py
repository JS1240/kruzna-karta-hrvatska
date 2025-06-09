import secrets
import string
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..models.user import User
from .config import settings
from .database import get_db

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT security
security = HTTPBearer()

# Token types
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
EMAIL_VERIFICATION_TYPE = "email_verification"
PASSWORD_RESET_TYPE = "password_reset"


class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def generate_random_token(length: int = 32) -> str:
    """Generate a random token for email verification, password reset, etc."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create an access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update(
        {"exp": expire, "type": ACCESS_TOKEN_TYPE, "iat": datetime.utcnow()}
    )
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a refresh token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=30)  # Refresh tokens last 30 days

    to_encode.update(
        {"exp": expire, "type": REFRESH_TOKEN_TYPE, "iat": datetime.utcnow()}
    )
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_email_verification_token(email: str) -> str:
    """Create an email verification token."""
    expire = datetime.utcnow() + timedelta(
        hours=24
    )  # Email verification expires in 24 hours
    to_encode = {
        "email": email,
        "exp": expire,
        "type": EMAIL_VERIFICATION_TYPE,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_password_reset_token(email: str) -> str:
    """Create a password reset token."""
    expire = datetime.utcnow() + timedelta(hours=1)  # Password reset expires in 1 hour
    to_encode = {
        "email": email,
        "exp": expire,
        "type": PASSWORD_RESET_TYPE,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def verify_token(token: str, expected_type: str) -> Optional[dict]:
    """Verify and decode a token."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        if payload.get("type") != expected_type:
            return None
        return payload
    except JWTError:
        return None


def get_user_from_token(token: str, db: Session) -> Optional[User]:
    """Get user from access token."""
    payload = verify_token(token, ACCESS_TOKEN_TYPE)
    if payload is None:
        return None

    user_id: int = payload.get("sub")
    if user_id is None:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user with email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get the current authenticated user."""
    token = credentials.credentials
    user = get_user_from_token(token, db)

    if user is None:
        raise AuthenticationError()

    if not user.is_active:
        raise AuthenticationError("User account is disabled")

    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current verified user."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=400,
            detail="Email not verified. Please verify your email address.",
        )
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Get the current superuser."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user


def check_user_permission(user: User, permission: str) -> bool:
    """Check if user has a specific permission."""
    if user.is_superuser:
        return True

    # TODO: Implement role-based permissions
    # This would check the user's roles and their permissions
    return False


def require_permission(permission: str):
    """Decorator to require a specific permission."""

    async def permission_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not check_user_permission(current_user, permission):
            raise HTTPException(
                status_code=403, detail=f"Permission '{permission}' required"
            )
        return current_user

    return permission_checker
