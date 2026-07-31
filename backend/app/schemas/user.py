from __future__ import annotations
"""用户与认证相关的 Pydantic Schema。"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ===== 基础响应 =====
class UserBase(BaseModel):
    """用户基础字段。"""

    email: EmailStr
    nickname: str = Field(..., min_length=1, max_length=64)


class UserCreate(UserBase):
    """注册请求。"""

    password: str = Field(..., min_length=6, max_length=128, description="密码至少 6 位")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("密码长度至少 6 位")
        return v


class UserLogin(BaseModel):
    """登录请求。"""

    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    """更新用户档案。所有字段可选。"""

    nickname: Optional[str] = Field(None, min_length=1, max_length=64)
    edu_email: Optional[EmailStr] = None
    school: Optional[str] = Field(None, max_length=128)
    major: Optional[str] = Field(None, max_length=128)
    graduation_year: Optional[int] = Field(None, ge=1980, le=2100)
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = None
    avatar_url: Optional[str] = Field(None, max_length=512)
    skills: List[str] | None = Field(None, description="技能列表")
    experience_json: Optional[Any] = Field(None, description="工作/实习经历，任意 JSON")
    projects_json: Optional[Any] = Field(None, description="项目经历，任意 JSON")


class UserProfileResponse(BaseModel):
    """用户档案响应。"""

    model_config = ConfigDict(from_attributes=True)

    edu_email: Optional[str] = None
    edu_verified: bool = False
    school: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[int] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience_json: Optional[Any] = None
    projects_json: Optional[Any] = None
    updated_at: Optional[datetime] = None


class UserResponse(BaseModel):
    """用户信息响应（不含密码）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    nickname: str
    role: str
    is_active: bool
    is_verified: bool
    oauth_provider: Optional[str] = None
    created_at: datetime
    profile: Optional[UserProfileResponse] = None


# ===== JWT Token =====
class Token(BaseModel):
    """Token 响应（同时通过 cookie 下发）。"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="access token 有效期（秒）")
    user: UserResponse


class TokenData(BaseModel):
    """JWT payload 解析结果。"""

    user_id: Optional[int] = None
    role: Optional[str] = None
    token_type: Optional[str] = None


class RefreshResponse(BaseModel):
    """刷新 token 响应。"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class VerifyEmailRequest(BaseModel):
    """邮箱验证请求。"""

    email: EmailStr
    code: str = Field(..., min_length=4, max_length=10, description="验证码")


class EduVerifyCodeRequest(BaseModel):
    """发送教育邮箱验证码请求。"""

    edu_email: EmailStr = Field(..., description="教育邮箱（.edu.cn）")


class VerifyEduEmailRequest(BaseModel):
    """验证教育邮箱请求。"""

    edu_email: EmailStr = Field(..., description="教育邮箱（.edu.cn）")
    code: str = Field(..., min_length=4, max_length=10, description="验证码")


class VerifyEduEmailResponse(BaseModel):
    """验证教育邮箱响应。"""

    verified: bool
    message: str


class MessageResponse(BaseModel):
    """通用消息响应。"""

    message: str
    detail: Optional[str] = None
