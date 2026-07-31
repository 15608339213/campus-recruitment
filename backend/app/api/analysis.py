from __future__ import annotations
from typing import Optional, List, Dict, Any
"""行业分析相关 API 路由。

接口：
- GET  /analysis/stats      行业统计（行业/地区/企业类型/薪资分布 + 趋势 + 排行）
- GET  /analysis/recommend  个人专业→行业推荐（调用 DeepSeek）
- GET  /analysis/salary     薪资分布详情
"""

import json
from datetime import date, timedelta
from typing_extensions import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, DBSession
from app.models.job import Job
from app.models.user import User
from app.services.ai.deepseek import DeepSeekError, get_deepseek_client

router = APIRouter(prefix="/analysis", tags=["行业分析"])


def _parse_range(range_str: str) -> Optional[date]:
    """将范围字符串转为起始日期。"""
    today = date.today()
    if range_str == "7D":
        return today - timedelta(days=7)
    elif range_str == "30D":
        return today - timedelta(days=30)
    elif range_str == "MTD":
        return today.replace(day=1)
    elif range_str == "QTD":
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        return today.replace(month=quarter_start_month, day=1)
    elif range_str == "YTD":
        return today.replace(month=1, day=1)
    elif range_str == "ALL":
        return None
    return None


# ===== 行业统计 =====
@router.get("/stats")
async def get_stats(
    db: DBSession,
    range: Optional[str] = Query("30D", description="时间范围：7D/30D/MTD/QTD/YTD/ALL"),
    job_type: Optional[str] = Query(None, description="岗位类型筛选：校招/实习/社招"),
) -> Dict[str, Any]:
    """获取岗位统计数据：行业分布、地区分布、企业类型分布、薪资分布、趋势、排行榜。

    返回结构匹配前端 AnalysisStats 接口：
    {
        "total_jobs": 105,
        "avg_salary": 18738,
        "daily_avg_jobs": 3,
        "active_industries": 8,
        "trend_data": [{"date": "2026-07-01", "jobs": 5}, ...],
        "industry_distribution": [{"name": "技术", "value": 16}, ...],
        "company_type_distribution": [{"name": "民企", "value": 54}, ...],
        "region_distribution": [{"name": "北京", "value": 7}, ...],
        "salary_by_industry": [{"industry": "技术", "avg_salary": 25000, "min_salary": 15000, "max_salary": 50000}, ...],
        "top_companies": [{"company": "字节跳动", "industry": "技术", "company_type": "民企", "jobs": 5, "salary_avg": 30000}, ...]
    }
    """
    start_date = _parse_range(range or "30D")

    # 基础筛选条件
    base_filter = [Job.is_active == True]  # noqa: E712
    if job_type:
        base_filter.append(Job.job_type == job_type)
    if start_date:
        base_filter.append(Job.created_at >= start_date)

    # 总数
    total_result = await db.execute(
        select(func.count(Job.id)).where(*base_filter)
    )
    total_jobs = total_result.scalar_one()

    # 平均薪资
    avg_result = await db.execute(
        select(func.avg((Job.salary_min + Job.salary_max) / 2))
        .where(*base_filter, Job.salary_min.isnot(None), Job.salary_max.isnot(None))
    )
    avg_salary = avg_result.scalar_one()
    avg_salary = round(float(avg_salary), 2) if avg_salary else 0

    # 日均发布
    if start_date:
        days = (date.today() - start_date).days or 1
    else:
        days = 30  # 默认按30天计算
    daily_avg_jobs = round(total_jobs / days, 1) if days > 0 else 0

    # 活跃行业数
    industries_result = await db.execute(
        select(func.count(func.distinct(Job.job_category)))
        .where(*base_filter, Job.job_category.isnot(None))
    )
    active_industries = industries_result.scalar_one()

    # 按岗位类别统计 -> industry_distribution
    category_result = await db.execute(
        select(Job.job_category, func.count(Job.id))
        .where(*base_filter)
        .group_by(Job.job_category)
        .order_by(func.count(Job.id).desc())
    )
    industry_distribution = [
        {"name": cat or "未分类", "value": cnt}
        for cat, cnt in category_result.all()
    ]

    # 按企业类型统计 -> company_type_distribution
    company_type_result = await db.execute(
        select(Job.company_type, func.count(Job.id))
        .where(*base_filter, Job.company_type.isnot(None))
        .group_by(Job.company_type)
        .order_by(func.count(Job.id).desc())
    )
    company_type_distribution = [
        {"name": ct, "value": cnt}
        for ct, cnt in company_type_result.all()
    ]

    # 按地区统计 -> region_distribution
    location_result = await db.execute(
        select(Job.location, func.count(Job.id))
        .where(*base_filter, Job.location.isnot(None))
        .group_by(Job.location)
        .order_by(func.count(Job.id).desc())
        .limit(20)
    )
    region_distribution = [
        {"name": loc, "value": cnt}
        for loc, cnt in location_result.all()
    ]

    # 按行业统计薪资 -> salary_by_industry
    salary_by_industry_result = await db.execute(
        select(
            Job.job_category,
            func.avg((Job.salary_min + Job.salary_max) / 2).label("avg_salary"),
            func.min(Job.salary_min).label("min_salary"),
            func.max(Job.salary_max).label("max_salary"),
        )
        .where(*base_filter, Job.job_category.isnot(None), Job.salary_min.isnot(None))
        .group_by(Job.job_category)
        .order_by(func.avg((Job.salary_min + Job.salary_max) / 2).desc())
    )
    salary_by_industry = [
        {
            "industry": cat,
            "avg_salary": round(float(avg_sal), 2) if avg_sal else 0,
            "min_salary": int(min_sal) if min_sal else 0,
            "max_salary": int(max_sal) if max_sal else 0,
        }
        for cat, avg_sal, min_sal, max_sal in salary_by_industry_result.all()
    ]

    # 趋势数据 -> trend_data (按日期分组统计)
    trend_result = await db.execute(
        select(
            func.date(Job.created_at).label("job_date"),
            func.count(Job.id).label("job_count"),
        )
        .where(*base_filter)
        .group_by(func.date(Job.created_at))
        .order_by(func.date(Job.created_at))
    )
    trend_data = [
        {"date": str(jd), "jobs": cnt}
        for jd, cnt in trend_result.all()
    ]

    # 头部企业排行榜 -> top_companies
    top_companies_result = await db.execute(
        select(
            Job.company,
            Job.job_category,
            Job.company_type,
            func.count(Job.id).label("job_count"),
            func.avg((Job.salary_min + Job.salary_max) / 2).label("avg_sal"),
        )
        .where(*base_filter)
        .group_by(Job.company, Job.job_category, Job.company_type)
        .order_by(func.count(Job.id).desc())
        .limit(15)
    )
    top_companies = [
        {
            "company": comp,
            "industry": cat or "未分类",
            "company_type": ct or "未知",
            "jobs": cnt,
            "salary_avg": round(float(avg_sal), 2) if avg_sal else 0,
        }
        for comp, cat, ct, cnt, avg_sal in top_companies_result.all()
    ]

    return {
        "total_jobs": total_jobs,
        "avg_salary": avg_salary,
        "daily_avg_jobs": daily_avg_jobs,
        "active_industries": active_industries,
        "trend_data": trend_data,
        "industry_distribution": industry_distribution,
        "company_type_distribution": company_type_distribution,
        "region_distribution": region_distribution,
        "salary_by_industry": salary_by_industry,
        "top_companies": top_companies,
    }


# ===== 个人专业→行业推荐 =====
@router.get("/recommend")
async def get_recommendation(
    current_user: CurrentUser,
    db: DBSession,
) -> Dict[str, Any]:
    """根据用户专业和当前岗位市场数据，AI 生成职业规划推荐。

    需要用户已填写专业信息。
    """
    # 检查用户是否填写了专业
    profile = current_user.profile
    if profile is None or not profile.major:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先在个人中心填写专业信息",
        )

    # 获取行业统计数据
    stats_result = await db.execute(
        select(Job.job_category, func.count(Job.id), func.avg(Job.salary_max))
        .where(Job.is_active == True, Job.job_category.isnot(None))  # noqa: E712
        .group_by(Job.job_category)
        .order_by(func.count(Job.id).desc())
        .limit(15)
    )
    industry_stats = {
        "industries": [
            {
                "category": cat,
                "job_count": cnt,
                "avg_salary_max": round(avg_sal, 2) if avg_sal else 0,
            }
            for cat, cnt, avg_sal in stats_result.all()
        ]
    }

    # 获取用户技能
    skills: List[str] = []
    if profile.skills:
        skills = [s.strip() for s in profile.skills.split(",") if s.strip()]

    # 调用 AI 生成推荐
    try:
        client = get_deepseek_client()
        recommendation = await client.analyze_industry_recommendation(
            major=profile.major,
            industry_stats=industry_stats,
            user_skills=skills,
        )
    except DeepSeekError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI 分析失败：{e}",
        )

    return {
        "major": profile.major,
        "industry_stats": industry_stats,
        "recommendation": recommendation,
    }


# ===== 薪资分布详情 =====
@router.get("/salary")
async def get_salary_distribution(
    db: DBSession,
    job_category: Optional[str] = Query(None, description="按岗位类别筛选"),
    location: Optional[str] = Query(None, description="按地区筛选"),
) -> Dict[str, Any]:
    """获取薪资分布详情，支持按岗位类别和地区筛选。"""
    conditions = [Job.is_active == True, Job.salary_min.isnot(None)]  # noqa: E712
    if job_category:
        conditions.append(Job.job_category == job_category)
    if location:
        conditions.append(Job.location.ilike(f"%{location}%"))

    # 聚合统计
    result = await db.execute(
        select(
            func.count(Job.id),
            func.avg(Job.salary_min),
            func.avg(Job.salary_max),
            func.min(Job.salary_min),
            func.max(Job.salary_max),
        ).where(*conditions)
    )
    count, avg_min, avg_max, min_sal, max_sal = result.one()

    # 按类别分组薪资
    category_salary = await db.execute(
        select(
            Job.job_category,
            func.avg(Job.salary_min),
            func.avg(Job.salary_max),
            func.count(Job.id),
        )
        .where(*conditions, Job.job_category.isnot(None))
        .group_by(Job.job_category)
        .order_by(func.avg(Job.salary_max).desc())
    )
    by_category = [
        {
            "category": cat,
            "avg_min": round(avg_mn, 2) if avg_mn else 0,
            "avg_max": round(avg_mx, 2) if avg_mx else 0,
            "count": cnt,
        }
        for cat, avg_mn, avg_mx, cnt in category_salary.all()
    ]

    return {
        "total": count,
        "avg_min": round(avg_min, 2) if avg_min else 0,
        "avg_max": round(avg_max, 2) if avg_max else 0,
        "min": min_sal or 0,
        "max": max_sal or 0,
        "by_category": by_category,
    }
