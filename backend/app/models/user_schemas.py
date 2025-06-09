from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from .schemas import Event


# Base User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(default='Croatia', max_length=100)
    bio: Optional[str] = Field(None, max_length=1000)
    preferred_language: Optional[str] = Field(default='hr', pattern=r'^(hr|en)$')


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    email_notifications: Optional[bool] = Field(default=True)
    marketing_emails: Optional[bool] = Field(default=False)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=1000)
    preferred_language: Optional[str] = Field(None, pattern=r'^(hr|en)$')
    email_notifications: Optional[bool] = None
    marketing_emails: Optional[bool] = None


class UserInDB(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    is_superuser: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class User(UserInDB):
    """Public user representation (excludes sensitive fields)."""
    pass


class UserWithProfile(User):
    """User with profile information."""
    user_profile: Optional['UserProfile'] = None


# Profile Schemas
class UserProfileBase(BaseModel):
    website: Optional[str] = Field(None, max_length=500)
    interests: Optional[List[str]] = None
    profile_visibility: Optional[str] = Field(default='public', pattern=r'^(public|friends|private)$')
    show_email: Optional[bool] = Field(default=False)
    show_phone: Optional[bool] = Field(default=False)
    show_location: Optional[bool] = Field(default=True)


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfile(UserProfileBase):
    id: int
    user_id: int
    events_attended: int
    events_favorited: int
    reviews_written: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Authentication Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefresh(BaseModel):
    refresh_token: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(UserCreate):
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class EmailVerification(BaseModel):
    token: str


class ResendEmailVerification(BaseModel):
    email: EmailStr


# Role Schemas
class UserRoleBase(BaseModel):
    name: str = Field(..., max_length=50)
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class UserRoleCreate(UserRoleBase):
    pass


class UserRoleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class UserRole(UserRoleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserRoleAssignmentCreate(BaseModel):
    user_id: int
    role_id: int
    expires_at: Optional[datetime] = None


class UserRoleAssignment(BaseModel):
    id: int
    user_id: int
    role_id: int
    assigned_by: Optional[int] = None
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool
    role: UserRole

    class Config:
        from_attributes = True


# Favorites Schema
class UserFavorite(BaseModel):
    event_id: int
    created_at: datetime


class UserFavoritesList(BaseModel):
    favorites: List[Event]
    total: int


# Response Schemas
class UserResponse(BaseModel):
    user: User
    message: str = "User retrieved successfully"


class UsersListResponse(BaseModel):
    users: List[User]
    total: int
    page: int
    size: int
    pages: int


class AuthResponse(BaseModel):
    user: User
    token: Token
    message: str = "Authentication successful"


# Admin Schemas
class UserAdmin(UserInDB):
    """Admin view of user with all fields."""
    email_verification_token: Optional[str] = None
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None


class UserAdminUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_superuser: Optional[bool] = None


# Search and Filter Schemas
class UserSearchParams(BaseModel):
    q: Optional[str] = None  # Search query
    city: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    created_from: Optional[date] = None
    created_to: Optional[date] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)