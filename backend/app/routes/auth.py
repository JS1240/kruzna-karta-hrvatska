from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from ..core.database import get_db
from ..core.auth import (
    authenticate_user, create_access_token, create_refresh_token,
    get_password_hash, verify_token, create_email_verification_token,
    create_password_reset_token, get_current_user, get_current_active_user,
    ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE, EMAIL_VERIFICATION_TYPE,
    PASSWORD_RESET_TYPE, AuthenticationError
)
from ..core.config import settings
from ..models.user import User, UserProfile
from ..models.user_schemas import (
    UserLogin, UserRegister, Token, TokenRefresh, PasswordChange,
    PasswordReset, PasswordResetConfirm, EmailVerification,
    ResendEmailVerification, AuthResponse, UserResponse, User as UserSchema
)

router = APIRouter(prefix="/auth", tags=["authentication"])


def send_verification_email(email: str, token: str):
    """Send email verification email (placeholder for actual email service)."""
    # TODO: Implement actual email sending
    print(f"Verification email for {email}: {settings.frontend_url}/verify-email?token={token}")


def send_password_reset_email(email: str, token: str):
    """Send password reset email (placeholder for actual email service)."""
    # TODO: Implement actual email sending
    print(f"Password reset email for {email}: {settings.frontend_url}/reset-password?token={token}")


@router.post("/register", response_model=AuthResponse)
def register(
    user_data: UserRegister,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )
    
    # Check username uniqueness if provided
    if user_data.username:
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )
    
    # Create user
    user_dict = user_data.model_dump()
    del user_dict['password']
    del user_dict['confirm_password']
    
    user = User(
        **user_dict,
        hashed_password=get_password_hash(user_data.password),
        is_active=True,
        is_verified=False
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create user profile
    profile = UserProfile(user_id=user.id)
    db.add(profile)
    db.commit()
    
    # Create email verification token
    verification_token = create_email_verification_token(user.email)
    user.email_verification_token = verification_token
    db.commit()
    
    # Send verification email
    background_tasks.add_task(send_verification_email, user.email, verification_token)
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    token = Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60
    )
    
    return AuthResponse(
        user=user,
        token=token,
        message="Registration successful. Please check your email to verify your account."
    )


@router.post("/login", response_model=AuthResponse)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return tokens."""
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    token = Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60
    )
    
    return AuthResponse(
        user=user,
        token=token,
        message="Login successful"
    )


@router.post("/refresh", response_model=Token)
def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    payload = verify_token(token_data.refresh_token, REFRESH_TOKEN_TYPE)
    if payload is None:
        raise AuthenticationError("Invalid refresh token")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise AuthenticationError("Invalid refresh token")
    
    # Verify user exists and is active
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    
    # Create new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/verify-email")
def verify_email(verification_data: EmailVerification, db: Session = Depends(get_db)):
    """Verify user email address."""
    payload = verify_token(verification_data.token, EMAIL_VERIFICATION_TYPE)
    if payload is None:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    
    email = payload.get("email")
    if email is None:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    user.is_verified = True
    user.email_verification_token = None
    db.commit()
    
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
def resend_verification(
    resend_data: ResendEmailVerification,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Resend email verification."""
    user = db.query(User).filter(User.email == resend_data.email).first()
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a verification email has been sent"}
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Create new verification token
    verification_token = create_email_verification_token(user.email)
    user.email_verification_token = verification_token
    db.commit()
    
    # Send verification email
    background_tasks.add_task(send_verification_email, user.email, verification_token)
    
    return {"message": "Verification email sent"}


@router.post("/forgot-password")
def forgot_password(
    reset_data: PasswordReset,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request password reset."""
    user = db.query(User).filter(User.email == reset_data.email).first()
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a password reset email has been sent"}
    
    # Create password reset token
    reset_token = create_password_reset_token(user.email)
    user.password_reset_token = reset_token
    user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    # Send reset email
    background_tasks.add_task(send_password_reset_email, user.email, reset_token)
    
    return {"message": "Password reset email sent"}


@router.post("/reset-password")
def reset_password(reset_data: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Reset password using token."""
    payload = verify_token(reset_data.token, PASSWORD_RESET_TYPE)
    if payload is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    email = payload.get("email")
    if email is None:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if token hasn't expired (double check)
    if user.password_reset_expires and user.password_reset_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token expired")
    
    # Update password
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()
    
    return {"message": "Password reset successful"}


@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    from ..core.auth import verify_password
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse(user=current_user)


@router.post("/logout")
def logout():
    """Logout user (client should discard tokens)."""
    return {"message": "Logged out successfully"}