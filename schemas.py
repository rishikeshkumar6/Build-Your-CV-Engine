from pydantic import BaseModel, EmailStr, validator, field_validator
import re
from typing import Optional, Any


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: Optional[str] = None
    auth_provider: Optional[str] = None  # e.g., 'google', 'facebook'

    # @field_validator("name")
    # def validate_name(cls, v):
    #     print("Validating name:", v)
    #     if not re.fullmatch(r"[A-Za-z ]+", v):
    #         raise ValueError("Name can only contain letters and spaces")
    #     return v

    # @field_validator("phonenumber")
    # def validate_phonenumber(cls, v):
    #     if not re.fullmatch(r"\d{10}", v):
    #         raise ValueError("Phone number must be exactly 10 digits")
    #     return v


class UserResponse(UserCreate):
    id: int


class UserRegsiterResponse(BaseModel):
    message: str
    statusCode: int


class UserLoginResponse(BaseModel):
    token: str
    statusCode: int


class UserUpdate(BaseModel):
    id: int
    email: Optional[EmailStr] = None


class GetUserResponse(BaseModel):
    statusCode: int
    message: str = None
    data: Any = {}
    status: Optional[bool] = False

    class Config:
        orm_mode = True
