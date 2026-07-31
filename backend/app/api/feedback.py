from __future__ import annotations
from typing import Optional, List, Dict, Any
"""反馈相关 API 路由。

接口：
- POST   /feedback        提交反馈（需登录）
- GET    /feedback        获取反馈列表（管理员）
- GET    /feedback/{id}   获取反馈详情（管理员）
- PUT    /feedback/{id}   回复反馈（管理员）
"""

from typing_extensions import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import AdminUser, CurrentUser, DBSession
from app.models.feedback import Feedback
from app.models.user import User
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackListResponse,
    FeedbackReply,
    FeedbackResponse,
)

router = APIRouter(prefix="/feedback", tags=["反馈"])


# ===== 提交反馈 =====
@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    payload: FeedbackCreate,
    current_user: CurrentUser,
    db: DBSession,
) -> FeedbackResponse:
    """提交反馈。需要登录。"""
    feedback = Feedback(
        user_id=current_user.id,
        category=payload.category,
        content=payload.content,
        status="pending",
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return FeedbackResponse.model_validate(feedback)


# ===== 反馈列表（管理员） =====
@router.get("", response_model=FeedbackListResponse)
async def list_feedback(
    admin: AdminUser,
    db: DBSession,
    category: Optional[str] = Query(None, description="按类别筛选"),
    status_filter: Optional[str] = Query(None, alias="status", description="按状态筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> FeedbackListResponse:
    """获取反馈列表（仅管理员）。"""
    conditions = []
    if category:
        conditions.append(Feedback.category == category)
    if status_filter:
        conditions.append(Feedback.status == status_filter)

    # 总数
    count_query = select(func.count(Feedback.id))
    for cond in conditions:
        count_query = count_query.where(cond)
    total = (await db.execute(count_query)).scalar_one()

    # 列表
    query = select(Feedback)
    for cond in conditions:
        query = query.where(cond)
    query = query.order_by(Feedback.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    items = [FeedbackResponse.model_validate(f) for f in result.scalars().all()]

    return FeedbackListResponse(items=items, total=total, skip=skip, limit=limit)


# ===== 我的反馈列表 =====
@router.get("/me", response_model=FeedbackListResponse)
async def list_my_feedback(
    current_user: CurrentUser,
    db: DBSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> FeedbackListResponse:
    """获取当前用户提交的反馈列表。"""
    count_result = await db.execute(
        select(func.count(Feedback.id)).where(Feedback.user_id == current_user.id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Feedback)
        .where(Feedback.user_id == current_user.id)
        .order_by(Feedback.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    items = [FeedbackResponse.model_validate(f) for f in result.scalars().all()]
    return FeedbackListResponse(items=items, total=total, skip=skip, limit=limit)


# ===== 反馈详情（管理员） =====
@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: int,
    admin: AdminUser,
    db: DBSession,
) -> FeedbackResponse:
    """获取反馈详情（仅管理员）。"""
    result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
    feedback = result.scalar_one_or_none()
    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="反馈不存在",
        )
    return FeedbackResponse.model_validate(feedback)


# ===== 回复反馈（管理员） =====
@router.put("/{feedback_id}", response_model=FeedbackResponse)
async def reply_feedback(
    feedback_id: int,
    payload: FeedbackReply,
    admin: AdminUser,
    db: DBSession,
) -> FeedbackResponse:
    """回复反馈（仅管理员）。"""
    result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
    feedback = result.scalar_one_or_none()
    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="反馈不存在",
        )

    feedback.admin_reply = payload.admin_reply
    feedback.status = payload.status
    await db.commit()
    await db.refresh(feedback)
    return FeedbackResponse.model_validate(feedback)
