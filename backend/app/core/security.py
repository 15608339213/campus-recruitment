from __future__ import annotations
"""安全工具：JWT 创建/验证、密码哈希/验证。"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# 密码哈希上下文（bcrypt）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ===== 密码哈希 =====
def hash_password(password: str) -> str:
    """对明文密码进行 bcrypt 哈希。"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希值是否匹配。"""
    return pwd_context.verify(plain_password, hashed_password)


# ===== JWT Token =====
def _create_token(
    subject: str | int,
    expires_delta: timedelta,
    token_type: str,
    extra_claims: Dict[str, Any] | None = None,
) -> str:
    """创建 JWT token 的内部方法。

    Args:
        subject: 通常是 user_id
        expires_delta: 过期时长
        token_type: "access" 或 "refresh"
        extra_claims: 额外的声明字段
    """
    now = datetime.now(timezone.utc)
    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(
    user_id: int | str,
    role: str = "user",
    extra_claims: Dict[str, Any] | None = None,
) -> str:
    """创建 access token（默认 30 分钟过期）。"""
    claims = {"role": role}
    if extra_claims:
        claims.update(extra_claims)
    return _create_token(
        subject=user_id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
        extra_claims=claims,
    )


def create_refresh_token(user_id: int | str) -> str:
    """创建 refresh token（默认 7 天过期）。"""
    return _create_token(
        subject=user_id,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
    )


def decode_token(token: str) -> Dict[str, Any]:
    """解码并验证 JWT token。

    Raises:
        JWTError: token 无效、过期或签名错误时抛出。
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def verify_access_token(token: str) -> Dict[str, Any] | None:
    """验证 access token，返回 payload。验证失败返回 None。"""
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str) -> Dict[str, Any] | None:
    """验证 refresh token，返回 payload。验证失败返回 None。"""
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None
