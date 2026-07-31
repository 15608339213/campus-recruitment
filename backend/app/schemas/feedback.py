from __future__ import annotations
from typing import Optional, List, Dict, Any
"""反馈相关的 Pydantic Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_CATEGORIES = {"bug", "suggestion", "complaint", "praise", "other"}
VALID_STATUSES = {"pending", "processing", "resolved", "closed"}


class FeedbackCreate(BaseModel):
    """提交反馈请求。"""

    category: str = Field(..., description="反馈类别：bug/suggestion/complaint/praise/other")
    content: str = Field(..., min_length=1, max_length=2000, description="反馈内容")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"category 必须是 {VALID_CATEGORIES} 之一")
        return v


class FeedbackResponse(BaseModel):
    """反馈响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    category: str
    content: str
    status: str
    admin_reply: Optional[str] = None
    created_at: datetime


class FeedbackListResponse(BaseModel):
    """反馈列表分页响应。"""

    items: List[FeedbackResponse]
    total: int
    skip: int
    limit: int


class FeedbackReply(BaseModel):
    """管理员回复反馈。"""

    admin_reply: str = Field(..., min_length=1, max_length=2000)
    status: str = Field("resolved", description="新状态：processing/resolved/closed")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"status 必须是 {VALID_STATUSES} 之一")
        return v
