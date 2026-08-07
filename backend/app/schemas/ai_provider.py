"""AI 提供商 Schema。"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field


class AIProviderConfigCreate(BaseModel):
    """创建 AI 提供商配置。"""

    provider_id: str = Field(..., description="提供商标识：deepseek/openai/moonshot/zhipu/qwen/custom")
    display_name: str = Field(..., min_length=1, max_length=128, description="显示名称")
    api_key: str = Field(..., min_length=1, description="API 密钥")
    base_url: str = Field(..., description="API 基础地址")
    model: str = Field(..., description="模型名称")
    is_active: bool = Field(False, description="是否设为当前激活的提供商")


class AIProviderConfigUpdate(BaseModel):
    """更新 AI 提供商配置。"""

    display_name: Optional[str] = Field(None, min_length=1, max_length=128)
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    is_active: Optional[bool] = None


class AIProviderConfigResponse(BaseModel):
    """AI 提供商配置响应（不返回完整 api_key）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_id: str
    display_name: str
    api_key_masked: str = Field("", description="脱敏后的 API Key")
    base_url: str
    model: str
    is_active: bool
    last_tested: Optional[datetime] = None
    last_test_ok: Optional[bool] = None
    created_at: datetime
    updated_at: datetime


class AIProviderInfo(BaseModel):
    """内置 AI 提供商信息。"""

    id: str
    name: str
    base_url: str
    models: List[str]
    default_model: str
    website: str
    description: str
    api_style: str = Field("openai", description="API 风格：openai/anthropic/gemini")
    tags: List[str] = Field(default_factory=list, description="模型标签")


class AIProviderListResponse(BaseModel):
    """AI 提供商列表响应。"""

    items: List[AIProviderConfigResponse]
    total: int


class TestConnectionRequest(BaseModel):
    """测试连接请求。"""

    api_key: str = Field(..., description="API 密钥")
    base_url: str = Field(..., description="API 基础地址")
    model: str = Field(..., description="模型名称")


class TestConnectionResponse(BaseModel):
    """测试连接响应。"""

    success: bool
    message: str
    response: Optional[str] = None
