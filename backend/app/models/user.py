from __future__ import annotations
from typing import Optional, List, Dict
"""用户与认证相关数据模型。

包含：User、UserProfile、OAuthAccount。
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """用户主表。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="OAuth 用户可能无密码")
    nickname: Mapped[str] = mapped_column(String(64), nullable=False, comment="昵称")
    # 角色：user / verified_student / admin
    role: Mapped[str] = mapped_column(String(32), default="user", nullable=False, index=True)
    # OAuth 主登录方式（可选）：github / qq / email
    oauth_provider: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    oauth_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="邮箱是否已验证")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # 关系
    profile: Mapped[Optional["UserProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    oauth_accounts: Mapped[List["OAuthAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    favorites: Mapped[List["Favorite"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    resumes: Mapped[List["Resume"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    feedbacks: Mapped[List["Feedback"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    ai_provider_configs: Mapped[List["AIProviderConfig"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class UserProfile(Base):
    """用户档案（含简历生成所需的教育、技能、项目经历等）。"""

    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    edu_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    edu_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    school: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    major: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="专业")
    graduation_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="个人简介")
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    # 技能列表存为逗号分隔字符串（PG 可用 ARRAY，此处保持通用）
    skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="技能，逗号分隔")
    # 经历、项目存 JSON 字符串，便于 AI 生成简历
    experience_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="工作/实习经历 JSON")
    projects_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="项目经历 JSON")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="profile")

    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id}, school={self.school})>"


class OAuthAccount(Base):
    """第三方 OAuth 账号关联（一个用户可绑定多个）。"""

    __tablename__ = "oauth_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False, comment="github / qq")
    provider_uid: Mapped[str] = mapped_column(String(128), nullable=False, comment="第三方用户 ID")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="oauth_accounts")

    def __repr__(self) -> str:
        return f"<OAuthAccount(id={self.id}, provider={self.provider})>"
