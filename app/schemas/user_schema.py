from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.core.constants import PermissionEnum, RoleEnum
from app.schemas.common import BaseSchema, validate_password


class UserBase(BaseSchema):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate(cls, value: str) -> str:
        return validate_password(value)


class UserResponse(UserBase):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    avatar_url: str | None = None
    is_active: bool
    role: RoleEnum
    permissions: list[PermissionEnum]
