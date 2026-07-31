from __future__ import annotations
from typing import Optional, List, Dict, Any
"""FastAPI 依赖注入：获取当前用户、数据库 session、管理员校验等。"""

from typing_extensions import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import verify_access_token, verify_refresh_token
from app.models.user import User

# 类型别名，简化路由函数签名
DBSession = Annotated[AsyncSession, Depends(get_db)]


def _extract_token(request: Request) -> Optional[str]:
    """从 cookie 或 Authorization header 中提取 access token。

    优先从 httpOnly cookie 读取（更安全），其次从 Authorization: Bearer header 读取（SPA 常用）。
    """
    # 1. 从 httpOnly cookie 读取
    token = request.cookies.get("access_token")
    if token:
        return token
    # 2. 从 Authorization header 读取（兼容前端 Bearer token 模式）
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


async def get_current_user(
    request: Request,
    db: DBSession,
) -> User:
    """依赖：从 cookie 的 JWT 获取当前登录用户。

    Raises:
        HTTPException 401: 未登录或 token 无效。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未登录或登录已过期，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = _extract_token(request)
    if not token:
        raise credentials_exception

    payload = verify_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(
        select(User).options(selectinload(User.profile)).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_user_optional(
    request: Request,
    db: DBSession,
) -> Optional[User]:
    """依赖：可选的当前用户（未登录返回 None，不抛异常）。

    用于公开接口，但已登录用户可获得个性化数据。
    """
    token = _extract_token(request)
    if not token:
        return None

    payload = verify_access_token(token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    result = await db.execute(
        select(User).options(selectinload(User.profile)).where(User.id == int(user_id))
    )
    return result.scalar_one_or_none()


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """依赖：确保当前用户是激活状态。"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用，请联系管理员",
        )
    return current_user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """依赖：要求当前用户是管理员。"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限",
        )
    return current_user


async def get_user_from_refresh_token(
    request: Request,
    db: DBSession,
) -> User:
    """依赖：从 refresh token 获取用户（用于刷新 access token）。

    Raises:
        HTTPException 401: refresh token 无效。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="刷新令牌无效，请重新登录",
    )

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise credentials_exception

    payload = verify_refresh_token(refresh_token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user


# 类型别名：直接在路由函数参数中使用
CurrentUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(get_current_admin)]
OptionalUser = Annotated[Optional[User], Depends(get_current_user_optional)]
RefreshUser = Annotated[User, Depends(get_user_from_refresh_token)]
