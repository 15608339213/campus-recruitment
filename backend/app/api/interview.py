from __future__ import annotations
from typing import Optional, List, Dict, Any
"""面试技巧与题库相关 API 路由。

接口：
- GET    /interview/tips              获取所有面试技巧
- GET    /interview/tips/{category}   按岗位类别获取面试技巧
- GET    /interview/questions         获取题库列表（筛选/分页）
- GET    /interview/questions/{id}    获取题目详情
- GET    /interview/categories        获取所有有数据的岗位类别
- POST   /interview/tips              创建/更新面试技巧（管理员）
- POST   /interview/questions         创建题目（管理员）
"""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import AdminUser, DBSession
from app.models.interview import InterviewTip, QuestionBank
from app.schemas.interview import (
    InterviewTipCreate,
    InterviewTipListResponse,
    InterviewTipResponse,
    QuestionBankCreate,
    QuestionBankListResponse,
    QuestionBankResponse,
)

router = APIRouter(prefix="/interview", tags=["面试技巧与题库"])


# ===== 获取所有面试技巧 =====
@router.get("/tips", response_model=InterviewTipListResponse)
async def list_tips(db: DBSession) -> InterviewTipListResponse:
    """获取所有岗位类别的面试技巧。"""
    result = await db.execute(
        select(InterviewTip).order_by(InterviewTip.job_category)
    )
    tips = result.scalars().all()
    items = [InterviewTipResponse.model_validate(t) for t in tips]
    return InterviewTipListResponse(items=items, total=len(items))


# ===== 按岗位类别获取面试技巧 =====
@router.get("/tips/{category}", response_model=InterviewTipResponse)
async def get_tip_by_category(
    category: str,
    db: DBSession,
) -> InterviewTipResponse:
    """按岗位类别获取面试技巧。"""
    result = await db.execute(
        select(InterviewTip).where(InterviewTip.job_category == category)
    )
    tip = result.scalar_one_or_none()
    if tip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"暂无 [{category}] 类别的面试技巧",
        )
    return InterviewTipResponse.model_validate(tip)


# ===== 获取题库列表 =====
@router.get("/questions", response_model=QuestionBankListResponse)
async def list_questions(
    db: DBSession,
    job_category: Optional[str] = Query(None, description="按岗位类别筛选"),
    question_type: Optional[str] = Query(None, description="按题型筛选：笔试/面试/HR面"),
    difficulty: Optional[str] = Query(None, description="按难度筛选：easy/medium/hard"),
    company: Optional[str] = Query(None, description="按公司筛选"),
    skip: int = Query(0, ge=0, description="分页偏移量"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
) -> QuestionBankListResponse:
    """获取题库列表，支持按类别、题型、难度、公司筛选和分页。"""
    conditions = []
    if job_category:
        conditions.append(QuestionBank.job_category == job_category)
    if question_type:
        conditions.append(QuestionBank.question_type == question_type)
    if difficulty:
        conditions.append(QuestionBank.difficulty == difficulty)
    if company:
        conditions.append(QuestionBank.company == company)

    # 总数
    count_query = select(func.count(QuestionBank.id))
    for cond in conditions:
        count_query = count_query.where(cond)
    total = (await db.execute(count_query)).scalar_one()

    # 列表
    query = select(QuestionBank)
    for cond in conditions:
        query = query.where(cond)
    query = query.order_by(QuestionBank.id.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    items = [QuestionBankResponse.model_validate(q) for q in result.scalars().all()]

    return QuestionBankListResponse(items=items, total=total, skip=skip, limit=limit)


# ===== 获取题目详情 =====
@router.get("/questions/{question_id}", response_model=QuestionBankResponse)
async def get_question(
    question_id: int,
    db: DBSession,
) -> QuestionBankResponse:
    """获取题目详情。"""
    result = await db.execute(
        select(QuestionBank).where(QuestionBank.id == question_id)
    )
    question = result.scalar_one_or_none()
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在",
        )
    return QuestionBankResponse.model_validate(question)


# ===== 获取所有有数据的岗位类别 =====
@router.get("/categories")
async def list_categories(db: DBSession) -> Dict[str, Any]:
    """获取所有有面试技巧或题库数据的岗位类别。"""
    # 技巧中的类别
    tips_result = await db.execute(
        select(InterviewTip.job_category).distinct()
    )
    tips_cats = {c for c in tips_result.scalars().all() if c}

    # 题库中的类别
    ques_result = await db.execute(
        select(QuestionBank.job_category).distinct()
    )
    ques_cats = {c for c in ques_result.scalars().all() if c}

    all_cats = sorted(tips_cats | ques_cats)

    # 每个类别的题目数
    cat_counts = {}
    for cat in all_cats:
        cnt_result = await db.execute(
            select(func.count(QuestionBank.id)).where(QuestionBank.job_category == cat)
        )
        cat_counts[cat] = cnt_result.scalar_one()

    return {
        "categories": all_cats,
        "counts": cat_counts,
    }


# ===== 创建/更新面试技巧（管理员） =====
@router.post("/tips", response_model=InterviewTipResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_tip(
    payload: InterviewTipCreate,
    admin: AdminUser,
    db: DBSession,
) -> InterviewTipResponse:
    """创建或更新面试技巧（仅管理员）。"""
    # 检查是否已存在
    result = await db.execute(
        select(InterviewTip).where(InterviewTip.job_category == payload.job_category)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.content_markdown = payload.content_markdown
        await db.commit()
        await db.refresh(existing)
        return InterviewTipResponse.model_validate(existing)

    tip = InterviewTip(
        job_category=payload.job_category,
        content_markdown=payload.content_markdown,
    )
    db.add(tip)
    await db.commit()
    await db.refresh(tip)
    return InterviewTipResponse.model_validate(tip)


# ===== 创建题目（管理员） =====
@router.post("/questions", response_model=QuestionBankResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    payload: QuestionBankCreate,
    admin: AdminUser,
    db: DBSession,
) -> QuestionBankResponse:
    """创建题目（仅管理员）。"""
    question = QuestionBank(
        job_category=payload.job_category,
        question=payload.question,
        answer=payload.answer,
        question_type=payload.question_type,
        difficulty=payload.difficulty,
        source=payload.source,
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return QuestionBankResponse.model_validate(question)
