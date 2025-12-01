from datetime import datetime

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field

# MongoDB에 저장되는 "Y" / "N" 값 그대로 사용

YN = Literal["Y", "N"]

class UserBase(BaseModel):

    email: EmailStr = Field(..., description="로그인 이메일")

    google_id: str = Field(..., description="Google OAuth 고유 ID(sub)")

    display_name: str = Field(..., description="화면에 표시될 이름")

    is_use: YN = Field(default="N", description="N이면 서비스 사용 불가")

    is_lock: YN = Field(default="Y", description="Y이면 계정 차단 상태")

    member_level: int = Field(default=1, ge=0, description="0=관리자, 1=일반유저")

    created_at: datetime = Field(default_factory=datetime.utcnow)

    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(UserBase):

    pass

class UserUpdate(BaseModel):

    display_name: Optional[str] = None

    is_use: Optional[YN] = None

    is_lock: Optional[YN] = None

    member_level: Optional[int] = Field(default=None, ge=0)

class UserOut(UserBase):

    id: str

    class Config:

        orm_mode = True

