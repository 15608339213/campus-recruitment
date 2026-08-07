from __future__ import annotations
from typing import Optional, List, Dict, Any
"""简历相关 API 路由。

接口：
- POST   /resume/generate   生成定制简历（调用 DeepSeek）
- GET    /resume            获取当前用户的简历列表
- GET    /resume/{id}       获取简历详情
- GET    /resume/{id}/pdf   下载简历 PDF
"""

import json
from typing_extensions import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, DBSession
from app.models.job import Job
from app.models.resume import Resume
from app.models.resume_template import ResumeAnalysis, ResumeTemplate
from app.models.user import User
from app.schemas.resume import (
    ResumeAnalysisRequest,
    ResumeAnalysisResponse,
    ResumeContent,
    ResumeGenerate,
    ResumeListResponse,
    ResumeResponse,
    ResumeTemplateListResponse,
    ResumeTemplateResponse,
)
from app.api.ai_provider import get_active_provider_client
from app.services.ai.provider import AIProviderError

router = APIRouter(prefix="/resume", tags=["简历"])


def _parse_resume_content(json_str: str) -> Optional[ResumeContent]:
    """解析简历内容 JSON。"""
    try:
        data = json.loads(json_str)
        return ResumeContent(**data)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def _build_resume_response(resume: Resume) -> ResumeResponse:
    """构建简历响应。"""
    return ResumeResponse(
        id=resume.id,
        user_id=resume.user_id,
        target_job_id=resume.target_job_id,
        customized_content=_parse_resume_content(resume.customized_content_json),
        pdf_url=resume.pdf_url,
        version=resume.version,
        created_at=resume.created_at,
    )


def _build_profile_dict(user: User) -> dict:
    """从用户档案构建 AI 输入数据。"""
    profile = user.profile
    if profile is None:
        return {"nickname": user.nickname, "email": user.email}

    skills = []
    if profile.skills:
        skills = [s.strip() for s in profile.skills.split(",") if s.strip()]

    return {
        "nickname": user.nickname,
        "email": user.email,
        "school": profile.school,
        "major": profile.major,
        "graduation_year": profile.graduation_year,
        "phone": profile.phone,
        "bio": profile.bio,
        "skills": skills,
        "experience": _safe_json_parse(profile.experience_json),
        "projects": _safe_json_parse(profile.projects_json),
    }


def _safe_json_parse(value: Optional[str]):
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


# ===== 生成简历 =====
@router.post("/generate", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def generate_resume(
    payload: ResumeGenerate,
    current_user: CurrentUser,
    db: DBSession,
) -> ResumeResponse:
    """根据目标岗位和用户档案生成定制化简历。

    调用 DeepSeek API，根据用户经历、技能和岗位描述生成匹配的简历内容。
    """
    # 1. 获取目标岗位
    job_result = await db.execute(select(Job).where(Job.id == payload.target_job_id))
    job = job_result.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标岗位不存在",
        )

    # 2. 构建用户档案数据
    profile_dict = _build_profile_dict(current_user)

    # 3. 调用 AI 生成简历
    extra_info = {}
    if payload.extra_experience:
        extra_info["extra_experience"] = payload.extra_experience
    if payload.extra_skills:
        extra_info["extra_skills"] = payload.extra_skills
    if payload.custom_requirements:
        extra_info["custom_requirements"] = payload.custom_requirements

    job_description = (
        f"岗位名称：{job.title}\n"
        f"公司：{job.company}\n"
        f"地点：{job.location or '未指定'}\n"
        f"类别：{job.job_category or '未指定'}\n"
        f"学历要求：{job.degree_required or '未指定'}\n"
        f"岗位描述：\n{job.description_html or '无'}"
    )

    try:
        client = await get_active_provider_client(current_user.id, db)
        resume_content = await client.generate_resume(
            user_profile=profile_dict,
            job_description=job_description,
            extra_info=extra_info if extra_info else None,
        )
        await client.close()
    except AIProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI 简历生成失败：{e}",
        )

    # 4. 计算版本号
    version_result = await db.execute(
        select(Resume)
        .where(Resume.user_id == current_user.id, Resume.target_job_id == payload.target_job_id)
        .order_by(Resume.version.desc())
        .limit(1)
    )
    latest = version_result.scalar_one_or_none()
    new_version = (latest.version + 1) if latest else 1

    # 5. 保存简历
    resume = Resume(
        user_id=current_user.id,
        target_job_id=payload.target_job_id,
        customized_content_json=json.dumps(resume_content, ensure_ascii=False),
        version=new_version,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    return _build_resume_response(resume)


# ===== 简历列表 =====
@router.get("", response_model=ResumeListResponse)
async def list_resumes(
    current_user: CurrentUser,
    db: DBSession,
) -> ResumeListResponse:
    """获取当前用户的所有简历。"""
    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
    )
    resumes = result.scalars().all()
    items = [_build_resume_response(r) for r in resumes]
    return ResumeListResponse(items=items, total=len(items))


# ===== 简历详情 =====
@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    current_user: CurrentUser,
    db: DBSession,
) -> ResumeResponse:
    """获取简历详情。"""
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id)
    )
    resume = result.scalar_one_or_none()
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历不存在",
        )
    return _build_resume_response(resume)


# ===== 下载简历 PDF =====
@router.get("/{resume_id}/pdf")
async def download_resume_pdf(
    resume_id: int,
    current_user: CurrentUser,
    db: DBSession,
) -> StreamingResponse:
    """下载简历 PDF。

    MVP 阶段：将简历内容渲染为简易 HTML 并以文件流返回（text/html）。
    生产环境应使用 wkhtmltopdf / weasyprint 转为真正的 PDF。
    """
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id)
    )
    resume = result.scalar_one_or_none()
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历不存在",
        )

    content = _parse_resume_content(resume.customized_content_json)
    html = _render_resume_html(content, current_user.nickname)

    # 返回 HTML 流（模拟 PDF 下载）
    # 生产环境替换为真正的 PDF 生成逻辑
    return StreamingResponse(
        iter([html.encode("utf-8")]),
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="resume_{resume_id}.html"'
        },
    )


def _render_resume_html(content: Optional[ResumeContent], nickname: str) -> str:
    """将简历内容渲染为简易 HTML（用于 PDF 导出）。"""
    if content is None:
        return f"<html><body><h1>{nickname} 的简历</h1><p>简历内容为空</p></body></html>"

    # 如果有原始 Markdown，优先使用
    if content.raw_markdown:
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>{nickname} - 简历</title>
<style>
body {{ font-family: 'Microsoft YaHei', sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; line-height: 1.6; }}
h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
h2 {{ color: #34495e; border-left: 4px solid #3498db; padding-left: 10px; }}
</style></head>
<body><pre style="white-space: pre-wrap;">{content.raw_markdown}</pre></body>
</html>"""

    # 否则按结构渲染
    sections = [f"<h1>{nickname}</h1>"]

    if content.skills:
        sections.append(f"<h2>技能</h2><p>{'、'.join(content.skills)}</p>")

    if content.experience:
        sections.append("<h2>工作/实习经历</h2>")
        for exp in content.experience:
            sections.append(
                f"<h3>{exp.get('company', '')} - {exp.get('role', '')}</h3>"
                f"<p>{exp.get('period', '')}</p>"
                f"<p>{exp.get('description', '')}</p>"
            )

    if content.projects:
        sections.append("<h2>项目经历</h2>")
        for proj in content.projects:
            sections.append(
                f"<h3>{proj.get('name', '')} - {proj.get('role', '')}</h3>"
                f"<p>{proj.get('description', '')}</p>"
                f"<p><em>技术栈：{proj.get('tech_stack', '')}</em></p>"
            )

    if content.self_evaluation:
        sections.append(f"<h2>自我评价</h2><p>{content.self_evaluation}</p>")

    body = "\n".join(sections)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>{nickname} - 简历</title>
<style>
body {{ font-family: 'Microsoft YaHei', sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; line-height: 1.6; }}
h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
h2 {{ color: #34495e; border-left: 4px solid #3498db; padding-left: 10px; }}
</style></head>
<body>{body}</body>
</html>"""


# ===== 简历模板 =====

@router.get("/templates", response_model=ResumeTemplateListResponse)
async def list_templates(db: DBSession) -> ResumeTemplateListResponse:
    """获取所有可用简历模板。"""
    result = await db.execute(
        select(ResumeTemplate)
        .where(ResumeTemplate.is_public == True)
        .order_by(ResumeTemplate.is_builtin.desc(), ResumeTemplate.downloads.desc())
    )
    templates = result.scalars().all()
    return ResumeTemplateListResponse(
        items=[ResumeTemplateResponse.model_validate(t) for t in templates],
        total=len(templates),
    )


@router.get("/templates/{template_id}", response_model=ResumeTemplateResponse)
async def get_template(template_id: int, db: DBSession) -> ResumeTemplateResponse:
    """获取单个模板详情。"""
    result = await db.execute(
        select(ResumeTemplate).where(ResumeTemplate.id == template_id)
    )
    tpl = result.scalar_one_or_none()
    if tpl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模板不存在")
    return ResumeTemplateResponse.model_validate(tpl)


# ===== 简历分析 =====

@router.post("/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume(
    payload: ResumeAnalysisRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> ResumeAnalysisResponse:
    """上传简历文本，AI 分析并给出优化建议。"""
    try:
        client = await get_active_provider_client(current_user.id, db)
    except AIProviderError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    system_prompt = (
        "你是一位资深 HR 和简历优化专家。请分析用户上传的简历文本，"
        "从以下维度给出评估和建议。必须返回合法 JSON。\n"
        '{"ats_score": 85, "skills_matched": ["技能1","技能2"], '
        '"missing_keywords": ["缺失关键词1"], '
        '"suggestions": [{"title": "问题", "detail": "建议"}]}'
    )

    user_msg = f"## 简历内容\n{payload.resume_text}"
    if payload.target_job_category:
        user_msg += f"\n\n## 目标岗位类别\n{payload.target_job_category}"

    try:
        result = await client.chat_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=2048,
        )
        await client.close()
    except AIProviderError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    import json as _json

    analysis = ResumeAnalysis(
        user_id=current_user.id,
        original_text=payload.resume_text[:5000],
        ats_score=result.get("ats_score"),
        skills_matched=_json.dumps(result.get("skills_matched", []), ensure_ascii=False),
        missing_keywords=_json.dumps(result.get("missing_keywords", []), ensure_ascii=False),
        suggestions=_json.dumps(result.get("suggestions", []), ensure_ascii=False),
        raw_ai_response=_json.dumps(result, ensure_ascii=False),
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    return ResumeAnalysisResponse(
        id=analysis.id,
        ats_score=analysis.ats_score,
        skills_matched=_json.loads(analysis.skills_matched) if analysis.skills_matched else None,
        missing_keywords=_json.loads(analysis.missing_keywords) if analysis.missing_keywords else None,
        suggestions=_json.loads(analysis.suggestions) if analysis.suggestions else None,
        created_at=analysis.created_at,
    )
