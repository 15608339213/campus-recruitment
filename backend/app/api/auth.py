from __future__ import annotations
from typing import Optional, List, Dict, Any
"""认证相关 API 路由。

接口：
- POST   /register          注册
- POST   /login             登录
- POST   /verify-email      验证邮箱
- POST   /refresh           刷新 access token
- GET    /me                获取当前用户信息
- POST   /logout            登出
- GET    /oauth/github      GitHub OAuth 登录跳转
- GET    /oauth/github/callback  GitHub OAuth 回调
"""

from typing_extensions import Annotated

import httpx
from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.deps import CurrentUser, DBSession, RefreshUser
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User
from app.schemas.user import (
    EduVerifyCodeRequest,
    MessageResponse,
    RefreshResponse,
    Token,
    UserCreate,
    UserLogin,
    UserProfileUpdate,
    UserResponse,
    VerifyEduEmailRequest,
    VerifyEduEmailResponse,
    VerifyEmailRequest,
)
from app.services.auth.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["认证"])


# ===== Cookie 工具函数 =====
def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """将 access_token 和 refresh_token 设置到 httpOnly cookie。"""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    """清除认证 cookie。"""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")


def _build_user_response(user: User) -> UserResponse:
    """构建用户响应（处理 profile 中 skills 字段转换）。"""
    user_dict = {
        "id": user.id,
        "email": user.email,
        "nickname": user.nickname,
        "role": user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "oauth_provider": user.oauth_provider,
        "created_at": user.created_at,
        "profile": None,
    }
    if user.profile:
        skills_list = []
        if user.profile.skills:
            skills_list = [s.strip() for s in user.profile.skills.split(",") if s.strip()]
        user_dict["profile"] = {
            "edu_email": user.profile.edu_email,
            "edu_verified": user.profile.edu_verified,
            "school": user.profile.school,
            "major": user.profile.major,
            "graduation_year": user.profile.graduation_year,
            "phone": user.profile.phone,
            "bio": user.profile.bio,
            "avatar_url": user.profile.avatar_url,
            "skills": skills_list,
            "experience_json": _safe_json_parse(user.profile.experience_json),
            "projects_json": _safe_json_parse(user.profile.projects_json),
            "updated_at": user.profile.updated_at,
        }
    return UserResponse(**user_dict)


def _safe_json_parse(value: Optional[str]):
    """安全解析 JSON 字符串，失败返回原值。"""
    if value is None:
        return None
    import json

    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


# ===== 注册 =====
@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: DBSession,
) -> MessageResponse:
    """邮箱注册。注册成功后会发送邮箱验证码。"""
    service = AuthService(db)
    user = await service.register(user_in)
    return MessageResponse(
        message="注册成功",
        detail=f"已向 {user.email} 发送验证码，请查收邮件完成验证",
    )


# ===== 登录速率限制 =====
async def _check_login_rate_limit(ip: str) -> None:
    """检查登录失败次数。超过限制抛出 HTTPException。"""
    import redis.asyncio as aioredis

    try:
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        key = f"login_fail:{ip}"
        attempts = await r.get(key)
        if attempts and int(attempts) >= settings.LOGIN_MAX_ATTEMPTS:
            ttl = await r.ttl(key)
            minutes = max(1, ttl // 60) if ttl > 0 else settings.LOGIN_LOCKOUT_MINUTES
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"登录失败次数过多，请 {minutes} 分钟后重试",
            )
        await r.aclose()
    except aioredis.ConnectionError:
        pass  # Redis 不可用时跳过限流


async def _record_login_failure(ip: str) -> None:
    """记录一次登录失败。"""
    import redis.asyncio as aioredis

    try:
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        key = f"login_fail:{ip}"
        await r.incr(key)
        await r.expire(key, settings.LOGIN_LOCKOUT_MINUTES * 60)
        await r.aclose()
    except aioredis.ConnectionError:
        pass


async def _clear_login_failures(ip: str) -> None:
    """登录成功后清除失败记录。"""
    import redis.asyncio as aioredis

    try:
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.delete(f"login_fail:{ip}")
        await r.aclose()
    except aioredis.ConnectionError:
        pass


# ===== 登录 =====
@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: DBSession,
    request: Request,
    response: Response,
) -> Token:
    """邮箱密码登录，成功后通过 httpOnly cookie 下发 JWT。"""
    client_ip = request.client.host if request.client else "unknown"

    # 1. 检查是否被锁定
    await _check_login_rate_limit(client_ip)

    # 2. 登录
    service = AuthService(db)
    try:
        user, access_token, refresh_token = await service.login(credentials)
    except HTTPException:
        await _record_login_failure(client_ip)
        raise

    # 3. 登录成功，清除失败记录
    await _clear_login_failures(client_ip)

    _set_auth_cookies(response, access_token, refresh_token)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_build_user_response(user),
    )


# ===== 邮箱验证 =====
@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    payload: VerifyEmailRequest,
    db: DBSession,
) -> MessageResponse:
    """验证邮箱验证码。"""
    service = AuthService(db)
    await service.verify_email(payload.email, payload.code)
    return MessageResponse(message="邮箱验证成功")


# ===== 重新发送验证码 =====
@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    email: str,
    db: DBSession,
) -> MessageResponse:
    """重新发送邮箱验证码。"""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该邮箱未注册",
        )
    if user.is_verified:
        return MessageResponse(message="该邮箱已验证，无需重复操作")

    service = AuthService(db)
    await service.generate_verification_code(email)
    return MessageResponse(message="验证码已重新发送，请查收邮件")


# ===== 发送教育邮箱验证码 =====
@router.post("/edu-verify-code", response_model=MessageResponse)
async def send_edu_verify_code(
    payload: EduVerifyCodeRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> MessageResponse:
    """发送教育邮箱验证码（需登录）。

    验证码在开发环境下通过日志输出，生产环境应发送邮件。
    """
    service = AuthService(db)
    code = await service.generate_edu_verification_code(current_user, payload.edu_email)
    return MessageResponse(
        message="验证码已发送至您的教育邮箱",
        detail=f"[DEV] 验证码: {code}" if settings.is_development else None,
    )


# ===== 验证教育邮箱 =====
@router.post("/verify-edu-email", response_model=VerifyEduEmailResponse)
async def verify_edu_email(
    payload: VerifyEduEmailRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> VerifyEduEmailResponse:
    """验证教育邮箱（需登录）。验证成功后升级为认证学生。"""
    service = AuthService(db)
    # 重新加载 current_user 以确保 profile 关联已加载
    result = await db.execute(
        select(User).options(selectinload(User.profile)).where(User.id == current_user.id)
    )
    user = result.scalar_one()
    await service.verify_edu_email(user, payload.edu_email, payload.code)
    return VerifyEduEmailResponse(verified=True, message="教育邮箱验证成功，已升级为认证学生")


# ===== 刷新 Token =====
@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    user: RefreshUser,
    response: Response,
    db: DBSession,
) -> RefreshResponse:
    """使用 refresh token 刷新 access token。"""
    service = AuthService(db)
    new_access_token = await service.refresh_token(user)
    # 更新 access_token cookie
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return RefreshResponse(
        access_token=new_access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ===== 获取当前用户 =====
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    """获取当前登录用户信息。"""
    return _build_user_response(current_user)


# ===== 更新用户档案 =====
@router.put("/me", response_model=UserResponse)
async def update_me(
    profile_in: UserProfileUpdate,
    current_user: CurrentUser,
    db: DBSession,
) -> UserResponse:
    """更新当前用户档案。"""
    service = AuthService(db)
    # 将 profile_in 转为字典，跳过 None 值
    profile_data = profile_in.model_dump(exclude_none=True)
    # 经历和项目转 JSON 字符串存储
    import json

    for field in ("experience_json", "projects_json"):
        if field in profile_data and profile_data[field] is not None:
            profile_data[field] = json.dumps(profile_data[field], ensure_ascii=False)

    user = await service.update_profile(current_user, profile_data)
    return _build_user_response(user)


# ===== 登出 =====
@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response) -> MessageResponse:
    """登出，清除认证 cookie。"""
    _clear_auth_cookies(response)
    return MessageResponse(message="已登出")


# ===== 头像上传 =====
@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(..., description="头像图片（JPEG/PNG/WebP，≤5MB）"),
    current_user: CurrentUser = None,
    db: DBSession = None,
) -> UserResponse:
    """上传用户头像。"""
    import os
    import uuid

    # 校验文件类型
    allowed = settings.ALLOWED_UPLOAD_TYPES[:3]  # 只允许图片
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail=f"仅支持 JPEG/PNG/WebP 格式")
    # 校验大小
    content = await file.read()
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail=f"文件不能超过 {settings.MAX_UPLOAD_SIZE_MB}MB")

    # 保存文件
    upload_dir = "uploads/avatars"
    os.makedirs(upload_dir, exist_ok=True)
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    # 更新数据库
    service = AuthService(db)
    result = await db.execute(
        select(User).options(selectinload(User.profile)).where(User.id == current_user.id)
    )
    user = result.scalar_one()
    avatar_url = f"/uploads/avatars/{filename}"
    await service.update_profile(user, {"avatar_url": avatar_url})
    return _build_user_response(user)


# ===== GitHub OAuth 登录跳转 =====
@router.get("/oauth/github")
async def github_oauth_login() -> dict:
    """跳转到 GitHub OAuth 授权页面。

    前端可直接用 window.location.href 跳转到返回的 url。
    """
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth 未配置，请联系管理员",
        )
    github_auth_url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        "&scope=user:email"
        "&allow_signup=true"
    )
    return {"url": github_auth_url}


# ===== GitHub OAuth 回调 =====
@router.get("/oauth/github/callback", response_model=Token)
async def github_oauth_callback(
    code: str,
    db: DBSession,
    response: Response,
) -> Token:
    """GitHub OAuth 回调处理。

    流程：
    1. 用 code 换 access_token
    2. 用 access_token 获取用户信息
    3. 获取或创建本地用户
    4. 生成 JWT 并设置 cookie
    """
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth 未配置",
        )

    # 1. 用 code 换 access_token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()

    if "access_token" not in token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub 授权失败，未获取到 access_token",
        )

    github_access_token = token_data["access_token"]

    # 2. 获取用户信息
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {github_access_token}"},
        )
        user_resp.raise_for_status()
        github_user = user_resp.json()

        # 获取邮箱（可能需要单独请求）
        emails_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {github_access_token}"},
        )
        emails = emails_resp.json() if emails_resp.status_code == 200 else []

    # 找到主邮箱
    email = None
    if isinstance(emails, list):
        for e in emails:
            if e.get("primary"):
                email = e.get("email")
                break
    if not email:
        email = github_user.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法获取 GitHub 邮箱，请确保已授权邮箱访问权限",
        )

    # 3. 获取或创建用户
    service = AuthService(db)
    user = await service.get_or_create_oauth_user(
        provider="github",
        provider_uid=str(github_user["id"]),
        email=email,
        nickname=github_user.get("name") or github_user.get("login") or "GitHub用户",
        avatar_url=github_user.get("avatar_url"),
    )

    # 4. 生成 JWT
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)
    _set_auth_cookies(response, access_token, refresh_token)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_build_user_response(user),
    )
