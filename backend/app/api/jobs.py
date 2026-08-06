from __future__ import annotations
from typing import Optional, List, Dict, Any
"""岗位相关 API 路由。

接口：
- GET    /jobs                 岗位列表（筛选/分页/排序）
- GET    /jobs/tags/all        获取所有岗位标签
- GET    /jobs/favorites/me    我的收藏列表
- GET    /jobs/{id}            岗位详情
- POST   /jobs/{id}/favorite   收藏岗位
- DELETE /jobs/{id}/favorite   取消收藏

注意：固定路径路由必须定义在 /{job_id} 参数路由之前，否则会被拦截。
"""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DBSession, OptionalUser
from app.models.job import Favorite, Job, JobTag
from app.schemas.job import (
    FavoriteListResponse,
    FavoriteResponse,
    JobListResponse,
    JobResponse,
    JobTagResponse,
)

router = APIRouter(prefix="/jobs", tags=["岗位"])


# ===== 工具函数 =====
def _build_job_response(job: Job, is_favorited: bool = False) -> JobResponse:
    """构建岗位响应。"""
    return JobResponse(
        id=job.id,
        title=job.title,
        company=job.company,
        company_type=job.company_type,
        location=job.location,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_unit=job.salary_unit,
        start_date=job.start_date,
        end_date=job.end_date,
        job_category=job.job_category,
        job_type=job.job_type,
        degree_required=job.degree_required,
        description_html=job.description_html,
        source_url=job.source_url,
        source_repo=job.source_repo,
        is_active=job.is_active,
        created_at=job.created_at,
        updated_at=job.updated_at,
        tags=[JobTagResponse(id=t.id, tag=t.tag) for t in job.tags],
        is_favorited=is_favorited,
    )


async def _get_favorited_job_ids(db: AsyncSession, user_id: int) -> set[int]:
    """获取用户已收藏的岗位 ID 集合。"""
    result = await db.execute(
        select(Favorite.job_id).where(Favorite.user_id == user_id)
    )
    return {row[0] for row in result.all()}


# ===== 岗位列表 =====
@router.get("", response_model=JobListResponse)
async def list_jobs(
    db: DBSession,
    current_user: OptionalUser,
    keyword: Optional[str] = Query(None, description="搜索关键词（标题/公司）"),
    company_type: Optional[str] = Query(None, description="企业类型"),
    location: Optional[str] = Query(None, description="工作地点"),
    job_category: Optional[str] = Query(None, description="岗位类别"),
    job_type: Optional[str] = Query(None, description="岗位类型：校招/实习/社招"),
    degree_required: Optional[str] = Query(None, description="学历要求"),
    salary_min: Optional[int] = Query(None, ge=0, description="薪资下限"),
    salary_max: Optional[int] = Query(None, ge=0, description="薪资上限"),
    tag: Optional[str] = Query(None, description="标签筛选"),
    is_active: Optional[bool] = Query(True, description="是否仅看有效岗位"),
    sort_by: str = Query("latest", description="排序：latest/salary_desc/deadline"),
    skip: int = Query(0, ge=0, description="分页偏移量"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
) -> JobListResponse:
    """获取岗位列表，支持多条件筛选、分页和排序。"""
    # 构建查询条件
    conditions = []
    if keyword:
        conditions.append(
            or_(
                Job.title.ilike(f"%{keyword}%"),
                Job.company.ilike(f"%{keyword}%"),
            )
        )
    if company_type:
        conditions.append(Job.company_type == company_type)
    if location:
        conditions.append(Job.location.ilike(f"%{location}%"))
    if job_category:
        conditions.append(Job.job_category == job_category)
    if job_type:
        conditions.append(Job.job_type == job_type)
    if degree_required:
        conditions.append(Job.degree_required == degree_required)
    if salary_min is not None:
        conditions.append(Job.salary_max >= salary_min)
    if salary_max is not None:
        conditions.append(Job.salary_min <= salary_max)
    if is_active is not None:
        conditions.append(Job.is_active == is_active)

    # 标签筛选：需要子查询
    if tag:
        tag_subquery = select(JobTag.job_id).where(JobTag.tag == tag).subquery()
        conditions.append(Job.id.in_(select(tag_subquery)))

    # 构建排序
    order_by_map = {
        "latest": Job.created_at.desc(),
        "salary_desc": Job.salary_max.desc().nullslast(),
        "deadline": Job.end_date.asc().nullslast(),
        "end_date_asc": Job.end_date.asc().nullslast(),
    }
    order_clause = order_by_map.get(sort_by, Job.created_at.desc())

    # 查询总数
    count_query = select(func.count(Job.id))
    for cond in conditions:
        count_query = count_query.where(cond)
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # 查询岗位列表
    query = select(Job)
    for cond in conditions:
        query = query.where(cond)
    query = query.order_by(order_clause).offset(skip).limit(limit)

    result = await db.execute(query)
    jobs = result.scalars().all()

    # 获取当前用户收藏状态
    favorited_ids: set[int] = set()
    if current_user:
        favorited_ids = await _get_favorited_job_ids(db, current_user.id)

    items = [_build_job_response(job, job.id in favorited_ids) for job in jobs]
    return JobListResponse(items=items, total=total, skip=skip, limit=limit)


# ===== 获取所有标签（固定路径，必须在 /{job_id} 之前）=====
@router.get("/tags/all", response_model=List[JobTagResponse])
async def list_all_tags(db: DBSession) -> List[JobTagResponse]:
    """获取所有岗位标签（去重）。"""
    result = await db.execute(select(JobTag.tag).distinct())
    tags = result.scalars().all()
    return [JobTagResponse(id=0, tag=t) for t in tags]


# ===== 我的收藏列表（固定路径，必须在 /{job_id} 之前）=====
@router.get("/favorites/me", response_model=FavoriteListResponse)
async def list_my_favorites(
    current_user: CurrentUser,
    db: DBSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> FavoriteListResponse:
    """获取当前用户的收藏列表。"""
    # 总数
    count_result = await db.execute(
        select(func.count(Favorite.id)).where(Favorite.user_id == current_user.id)
    )
    total = count_result.scalar_one()

    # 列表（selectinload 预加载 job 关联，避免异步懒加载报错）
    result = await db.execute(
        select(Favorite)
        .options(selectinload(Favorite.job))
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    favorites = result.scalars().all()

    items = []
    for fav in favorites:
        # 手动加载 job（避免 lazy load 在异步中报错）
        job_resp = None
        if fav.job is not None:
            job_resp = _build_job_response(fav.job, True)
        items.append(
            FavoriteResponse(
                id=fav.id,
                job_id=fav.job_id,
                note=fav.note,
                created_at=fav.created_at,
                job=job_resp,
            )
        )
    return FavoriteListResponse(items=items, total=total, skip=skip, limit=limit)


# ===== 筛选选项（固定路径，必须在 /{job_id} 之前）=====
@router.get("/meta")
async def get_job_meta(db: DBSession) -> Dict[str, Any]:
    """获取岗位筛选选项（行业、企业类型、地点、学历）。"""
    # 行业类别
    cat_result = await db.execute(
        select(Job.job_category)
        .where(Job.is_active == True, Job.job_category.isnot(None))  # noqa: E712
        .distinct()
    )
    industries = sorted([c for c in cat_result.scalars().all() if c])

    # 企业类型
    ct_result = await db.execute(
        select(Job.company_type)
        .where(Job.is_active == True, Job.company_type.isnot(None))  # noqa: E712
        .distinct()
    )
    company_types = sorted([c for c in ct_result.scalars().all() if c])

    # 工作地点
    loc_result = await db.execute(
        select(Job.location)
        .where(Job.is_active == True, Job.location.isnot(None))  # noqa: E712
        .distinct()
        .limit(50)
    )
    locations = sorted([l for l in loc_result.scalars().all() if l])

    # 学历要求
    deg_result = await db.execute(
        select(Job.degree_required)
        .where(Job.is_active == True, Job.degree_required.isnot(None))  # noqa: E712
        .distinct()
    )
    degrees = sorted([d for d in deg_result.scalars().all() if d])

    return {
        "industries": industries,
        "company_types": company_types,
        "locations": locations,
        "degrees": degrees,
    }


# ===== 岗位详情（参数路由）=====
@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: DBSession,
    current_user: OptionalUser,
) -> JobResponse:
    """获取岗位详情。"""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="岗位不存在",
        )

    is_favorited = False
    if current_user:
        favorited_ids = await _get_favorited_job_ids(db, current_user.id)
        is_favorited = job_id in favorited_ids

    return _build_job_response(job, is_favorited)


# ===== 收藏岗位 =====
@router.post("/{job_id}/favorite", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    job_id: int,
    current_user: CurrentUser,
    db: DBSession,
    note: Optional[str] = Query(None, description="收藏备注"),
) -> FavoriteResponse:
    """收藏岗位。"""
    # 检查岗位是否存在
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="岗位不存在",
        )

    # 检查是否已收藏
    existing = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.job_id == job_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="已收藏过该岗位",
        )

    favorite = Favorite(user_id=current_user.id, job_id=job_id, note=note)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)

    return FavoriteResponse(
        id=favorite.id,
        job_id=favorite.job_id,
        note=favorite.note,
        created_at=favorite.created_at,
        job=_build_job_response(job, True),
    )


# ===== 取消收藏 =====
@router.delete("/{job_id}/favorite", status_code=status.HTTP_200_OK)
async def remove_favorite(
    job_id: int,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """取消收藏岗位。"""
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.job_id == job_id,
        )
    )
    favorite = result.scalar_one_or_none()
    if favorite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未收藏该岗位",
        )
    await db.delete(favorite)
    await db.commit()
    return {"message": "已取消收藏"}
