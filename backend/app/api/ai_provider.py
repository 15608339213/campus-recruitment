"""AI 提供商配置 API。

用户可以：
1. 查看内置支持的 AI 提供商列表
2. 添加自己的 AI 提供商配置（API Key、Base URL、模型）
3. 选择当前激活的提供商
4. 测试连接是否正常
5. 在简历生成时使用选中的提供商
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, DBSession
from app.models.ai_provider import AIProviderConfig
from app.schemas.ai_provider import (
    AIProviderConfigCreate,
    AIProviderConfigResponse,
    AIProviderConfigUpdate,
    AIProviderInfo,
    AIProviderListResponse,
    TestConnectionRequest,
    TestConnectionResponse,
)
from app.services.ai.provider import BUILTIN_PROVIDERS, AIProviderClient, AIProviderError

router = APIRouter(prefix="/ai-providers", tags=["AI 提供商"])


def _mask_api_key(key: str) -> str:
    """脱敏 API Key，只显示前4位和后4位。"""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


def _to_response(config: AIProviderConfig) -> AIProviderConfigResponse:
    """将 ORM 对象转为响应。"""
    return AIProviderConfigResponse(
        id=config.id,
        provider_id=config.provider_id,
        display_name=config.display_name,
        api_key_masked=_mask_api_key(config.api_key),
        base_url=config.base_url,
        model=config.model,
        is_active=config.is_active,
        last_tested=config.last_tested,
        last_test_ok=config.last_test_ok,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


# ===== 内置提供商列表 =====
@router.get("/builtin", response_model=List[AIProviderInfo])
async def list_builtin_providers() -> List[AIProviderInfo]:
    """获取内置支持的 AI 提供商列表。"""
    return [
        AIProviderInfo(
            id=pid,
            name=info["name"],
            base_url=info["base_url"],
            models=info["models"],
            default_model=info["default_model"],
            website=info["website"],
            description=info["description"],
        )
        for pid, info in BUILTIN_PROVIDERS.items()
    ]


# ===== 用户的提供商配置列表 =====
@router.get("", response_model=AIProviderListResponse)
async def list_my_providers(
    current_user: CurrentUser,
    db: DBSession,
) -> AIProviderListResponse:
    """获取当前用户的所有 AI 提供商配置。"""
    result = await db.execute(
        select(AIProviderConfig)
        .where(AIProviderConfig.user_id == current_user.id)
        .order_by(AIProviderConfig.created_at.desc())
    )
    configs = result.scalars().all()
    return AIProviderListResponse(
        items=[_to_response(c) for c in configs],
        total=len(configs),
    )


# ===== 创建提供商配置 =====
@router.post("", response_model=AIProviderConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_provider_config(
    payload: AIProviderConfigCreate,
    current_user: CurrentUser,
    db: DBSession,
) -> AIProviderConfigResponse:
    """添加新的 AI 提供商配置。"""
    config = AIProviderConfig(
        user_id=current_user.id,
        provider_id=payload.provider_id,
        display_name=payload.display_name,
        api_key=payload.api_key,
        base_url=payload.base_url,
        model=payload.model,
        is_active=payload.is_active,
    )

    # 如果设为激活，先取消其他激活配置
    if payload.is_active:
        await db.execute(
            update(AIProviderConfig)
            .where(AIProviderConfig.user_id == current_user.id)
            .values(is_active=False)
        )

    db.add(config)
    await db.commit()
    await db.refresh(config)
    return _to_response(config)


# ===== 更新提供商配置 =====
@router.put("/{config_id}", response_model=AIProviderConfigResponse)
async def update_provider_config(
    config_id: int,
    payload: AIProviderConfigUpdate,
    current_user: CurrentUser,
    db: DBSession,
) -> AIProviderConfigResponse:
    """更新 AI 提供商配置。"""
    result = await db.execute(
        select(AIProviderConfig).where(
            AIProviderConfig.id == config_id,
            AIProviderConfig.user_id == current_user.id,
        )
    )
    config = result.scalar_one_or_none()
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置不存在")

    # 更新字段
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)

    # 如果设为激活，取消其他激活配置
    if payload.is_active:
        await db.execute(
            update(AIProviderConfig)
            .where(
                AIProviderConfig.user_id == current_user.id,
                AIProviderConfig.id != config_id,
            )
            .values(is_active=False)
        )

    await db.commit()
    await db.refresh(config)
    return _to_response(config)


# ===== 删除提供商配置 =====
@router.delete("/{config_id}", status_code=status.HTTP_200_OK)
async def delete_provider_config(
    config_id: int,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """删除 AI 提供商配置。"""
    result = await db.execute(
        select(AIProviderConfig).where(
            AIProviderConfig.id == config_id,
            AIProviderConfig.user_id == current_user.id,
        )
    )
    config = result.scalar_one_or_none()
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置不存在")

    await db.delete(config)
    await db.commit()
    return {"message": "删除成功"}


# ===== 测试连接 =====
@router.post("/test", response_model=TestConnectionResponse)
async def test_connection(
    payload: TestConnectionRequest,
    current_user: CurrentUser,
) -> TestConnectionResponse:
    """测试 AI 提供商连接是否正常。"""
    try:
        client = AIProviderClient(
            api_key=payload.api_key,
            base_url=payload.base_url,
            model=payload.model,
        )
        result = await client.test_connection()
        await client.close()
        return TestConnectionResponse(**result)
    except AIProviderError as e:
        return TestConnectionResponse(success=False, message=str(e))


# ===== 获取当前激活的提供商配置（内部使用） =====
async def get_active_provider_client(
    user_id: int,
    db: AsyncSession,
) -> AIProviderClient:
    """获取用户当前激活的 AI 提供商客户端。

    优先使用用户自己配置的提供商；如果未配置则回退到系统默认的 DeepSeek。
    """
    result = await db.execute(
        select(AIProviderConfig).where(
            AIProviderConfig.user_id == user_id,
            AIProviderConfig.is_active == True,  # noqa: E712
        )
    )
    config = result.scalar_one_or_none()

    if config:
        return AIProviderClient(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
            provider_id=config.provider_id,
        )

    # 回退到系统默认 DeepSeek 配置
    from app.core.config import settings

    if settings.DEEPSEEK_API_KEY:
        return AIProviderClient(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            model=settings.DEEPSEEK_MODEL,
            provider_id="deepseek",
        )

    raise AIProviderError(
        "尚未配置 AI 提供商。请在「AI 设置」页面添加您的 API Key，"
        "或在系统 .env 中配置 DEEPSEEK_API_KEY。"
    )
