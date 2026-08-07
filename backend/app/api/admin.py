"""管理员监控看板 API。

接口：
- GET  /admin/stats    全站统计数据
- GET  /admin/health   服务健康（CPU/内存/磁盘）
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.core.deps import AdminUser, DBSession
from app.models.feedback import Feedback
from app.models.job import Job, JobTag
from app.models.resume import Resume
from app.models.resume_template import ResumeAnalysis, ResumeTemplate
from app.models.user import User, UserProfile

router = APIRouter(prefix="/admin", tags=["管理监控"])


@router.get("/stats")
async def get_admin_stats(current_user: AdminUser, db: DBSession) -> Dict[str, Any]:
    """全站监控数据（仅管理员）。"""

    today = date.today()
    week_ago = today - timedelta(days=7)

    # 用户总数
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    # 本周新增
    new_users_week = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_ago)
    )).scalar_one()

    # 岗位
    total_jobs = (await db.execute(
        select(func.count(Job.id)).where(Job.is_active == True)
    )).scalar_one()

    # 简历
    total_resumes = (await db.execute(
        select(func.count(Resume.id))
    )).scalar_one()
    total_analyses = (await db.execute(
        select(func.count(ResumeAnalysis.id))
    )).scalar_one()

    # 反馈
    total_feedback = (await db.execute(
        select(func.count(Feedback.id))
    )).scalar_one()
    pending_feedback = (await db.execute(
        select(func.count(Feedback.id)).where(Feedback.status == "pending")
    )).scalar_one()

    # 岗位按类别统计
    cat_result = await db.execute(
        select(Job.job_category, func.count(Job.id))
        .where(Job.is_active == True)
        .group_by(Job.job_category)
        .order_by(func.count(Job.id).desc())
    )
    job_by_category = [{"name": c or "未知", "value": n} for c, n in cat_result.all()]

    # 近7天注册趋势
    trend_result = await db.execute(
        select(func.date(User.created_at), func.count(User.id))
        .where(User.created_at >= week_ago)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )
    user_trend = [{"date": str(d), "count": n} for d, n in trend_result.all()]

    # 系统资源（容器内）
    import psutil

    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "users": {
            "total": total_users,
            "new_this_week": new_users_week,
            "trend": user_trend,
        },
        "jobs": {
            "total": total_jobs,
            "by_category": job_by_category,
        },
        "content": {
            "resumes": total_resumes,
            "analyses": total_analyses,
            "templates": (await db.execute(select(func.count(ResumeTemplate.id)))).scalar_one(),
        },
        "feedback": {
            "total": total_feedback,
            "pending": pending_feedback,
        },
        "system": {
            "cpu_percent": cpu,
            "memory_used_gb": round(mem.used / (1024**3), 2),
            "memory_total_gb": round(mem.total / (1024**3), 2),
            "memory_percent": mem.percent,
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
        },
        "timestamp": datetime.now().isoformat(),
    }
