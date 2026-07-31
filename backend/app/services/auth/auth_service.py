from __future__ import annotations
"""认证业务服务：注册、登录、JWT 生成、邮箱验证、OAuth。

注意：邮箱验证码发送需要邮件服务，此处使用内存缓存模拟（生产环境应使用 Redis）。
"""

import secrets
import time
from typing import Optional, List, Dict, Any, Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import OAuthAccount, User, UserProfile
from app.schemas.user import UserCreate, UserLogin

# 邮箱验证码缓存：{email: (code, expire_timestamp)}
# 生产环境应使用 Redis，此处用模块级字典模拟
_email_verification_codes: Dict[str, tuple[str, float]] = {}
# 教育邮箱验证码缓存
_edu_verification_codes: Dict[str, tuple[str, float]] = {}
# 验证码有效期 10 分钟
VERIFICATION_CODE_TTL = 600


class AuthService:
    """认证业务逻辑。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ===== 注册 =====
    async def register(self, user_in: UserCreate) -> User:
        """邮箱注册。

        - 检查邮箱是否已注册
        - 哈希密码
        - 创建用户 + 空档案
        - 生成并发送邮箱验证码
        """
        # 检查邮箱是否已存在
        existing = await self.db.execute(select(User).where(User.email == user_in.email))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该邮箱已被注册",
            )

        # 创建用户
        user = User(
            email=user_in.email,
            password_hash=hash_password(user_in.password),
            nickname=user_in.nickname,
            role="user",
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.flush()  # 获取 user.id

        # 创建空档案
        profile = UserProfile(user_id=user.id)
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(user)

        # 生成并发送验证码
        code = await self.generate_verification_code(user.email)
        # TODO: 接入真实邮件服务发送验证码
        # 开发环境下验证码直接返回（通过日志查看）
        _log_verification_code(user.email, code)

        return user

    # ===== 登录 =====
    async def login(self, credentials: UserLogin) -> tuple[User, str, str]:
        """邮箱密码登录。

        Returns:
            (user, access_token, refresh_token)
        """
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.email == credentials.email)
        )
        user = result.scalar_one_or_none()

        if user is None or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误",
            )
        if not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已被禁用，请联系管理员",
            )

        access_token = create_access_token(user.id, user.role)
        refresh_token = create_refresh_token(user.id)
        return user, access_token, refresh_token

    # ===== 刷新 Token =====
    async def refresh_token(self, user: User) -> str:
        """用 refresh token 刷新 access token。"""
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已被禁用",
            )
        return create_access_token(user.id, user.role)

    # ===== 邮箱验证码 =====
    async def generate_verification_code(self, email: str) -> str:
        """生成 6 位数字验证码并缓存。"""
        code = f"{secrets.randbelow(900000) + 100000:06d}"
        _email_verification_codes[email] = (code, time.time() + VERIFICATION_CODE_TTL)
        return code

    async def verify_email(self, email: str, code: str) -> bool:
        """验证邮箱验证码。验证成功后标记用户为已验证。"""
        cached = _email_verification_codes.get(email)
        if cached is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码已过期或未发送，请重新获取",
            )
        cached_code, expire_at = cached
        if time.time() > expire_at:
            _email_verification_codes.pop(email, None)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码已过期，请重新获取",
            )
        if cached_code != code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误",
            )

        # 验证成功，清除验证码
        _email_verification_codes.pop(email, None)

        # 标记用户已验证
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.email == email)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        user.is_verified = True

        # 如果邮箱是教育邮箱，自动升级为 verified_student
        if email.endswith(".edu.cn"):
            user.role = "verified_student"
            if user.profile:
                user.profile.edu_email = email
                user.profile.edu_verified = True

        await self.db.commit()
        return True

    # ===== 教育邮箱验证 =====
    async def generate_edu_verification_code(self, user: User, edu_email: str) -> str:
        """生成教育邮箱验证码并缓存。"""
        # 验证邮箱格式
        if not edu_email.endswith(".edu.cn"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="教育邮箱需以 .edu.cn 结尾",
            )
        # 检查是否已被其他用户使用
        result = await self.db.execute(
            select(UserProfile).where(
                UserProfile.edu_email == edu_email,
                UserProfile.edu_verified == True,  # noqa: E712
            )
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该教育邮箱已被验证使用",
            )

        code = f"{secrets.randbelow(900000) + 100000:06d}"
        _edu_verification_codes[edu_email] = (code, time.time() + VERIFICATION_CODE_TTL)
        _log_verification_code(edu_email, code)
        return code

    async def verify_edu_email(self, user: User, edu_email: str, code: str) -> bool:
        """验证教育邮箱验证码，成功后更新用户档案。"""
        cached = _edu_verification_codes.get(edu_email)
        if cached is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码已过期或未发送，请重新获取",
            )
        cached_code, expire_at = cached
        if time.time() > expire_at:
            _edu_verification_codes.pop(edu_email, None)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码已过期，请重新获取",
            )
        if cached_code != code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误",
            )

        # 验证成功，清除验证码
        _edu_verification_codes.pop(edu_email, None)

        # 更新用户档案
        if user.profile is None:
            user.profile = UserProfile(user_id=user.id)
            self.db.add(user.profile)

        user.profile.edu_email = edu_email
        user.profile.edu_verified = True

        # 升级角色为认证学生
        if user.role == "user":
            user.role = "verified_student"

        await self.db.commit()
        return True

    # ===== GitHub OAuth =====
    async def get_or_create_oauth_user(
        self,
        provider: str,
        provider_uid: str,
        email: str,
        nickname: str,
        avatar_url: Optional[str] = None,
    ) -> User:
        """获取或创建 OAuth 用户。

        - 若已绑定该 OAuth 账号，直接返回用户
        - 若邮箱已注册但未绑定，则绑定后返回
        - 否则创建新用户
        """
        # 1. 查找已绑定的 OAuth 账号
        result = await self.db.execute(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_uid == provider_uid,
            )
        )
        oauth_account = result.scalar_one_or_none()
        if oauth_account is not None:
            user_result = await self.db.execute(
                select(User).where(User.id == oauth_account.user_id)
            )
            return user_result.scalar_one()

        # 2. 查找邮箱是否已注册
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None:
            # 3. 创建新用户
            user = User(
                email=email,
                password_hash=None,
                nickname=nickname,
                role="user",
                oauth_provider=provider,
                oauth_id=provider_uid,
                is_active=True,
                is_verified=True,  # OAuth 用户默认已验证
            )
            self.db.add(user)
            await self.db.flush()

            profile = UserProfile(user_id=user.id, avatar_url=avatar_url)
            self.db.add(profile)
            await self.db.flush()

        # 4. 绑定 OAuth 账号
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_uid=provider_uid,
        )
        self.db.add(oauth_account)
        await self.db.commit()

        # 重新查询以加载完整的关联数据
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user.id)
        )
        return result.scalar_one()

    # ===== 更新档案 =====
    async def update_profile(self, user: User, profile_data: Dict[str, Any]) -> User:
        """更新用户档案。"""
        if user.profile is None:
            user.profile = UserProfile(user_id=user.id)
            self.db.add(user.profile)

        profile = user.profile
        nickname = profile_data.pop("nickname", None)
        if nickname:
            user.nickname = nickname

        for key, value in profile_data.items():
            if key == "skills" and isinstance(value, list):
                value = ",".join(value)
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)

        await self.db.commit()

        # 重新查询以加载完整的关联数据
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user.id)
        )
        return result.scalar_one()


def _log_verification_code(email: str, code: str) -> None:
    """开发环境下打印验证码（生产环境应发送邮件）。"""
    # 使用 print 而非 logging，避免循环导入
    print(f"[DEV] 邮箱验证码 -> {email}: {code}")  # noqa: T201
