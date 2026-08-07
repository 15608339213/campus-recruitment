from __future__ import annotations
"""简历相关的 Pydantic Schema。"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Any

from pydantic import BaseModel, ConfigDict, Field


class ResumeGenerate(BaseModel):
    """生成简历请求。"""

    target_job_id: int = Field(..., description="目标岗位 ID")
    # 可选：覆盖用户档案中的经历信息
    extra_experience: Optional[Any] = Field(None, description="额外补充的经历信息 JSON")
    extra_skills: List[str] | None = Field(None, description="额外技能")
    custom_requirements: Optional[str] = Field(None, max_length=2000, description="自定义要求")


class ResumeContent(BaseModel):
    """AI 生成的简历内容结构。"""

    basic_info: Dict[str, Any] = Field(default_factory=dict, description="基本信息")
    education: List[Dict[str, Any]] = Field(default_factory=list, description="教育背景")
    experience: List[Dict[str, Any]] = Field(default_factory=list, description="工作/实习经历")
    projects: List[Dict[str, Any]] = Field(default_factory=list, description="项目经历")
    skills: List[str] = Field(default_factory=list, description="技能列表")
    self_evaluation: Optional[str] = Field(None, description="自我评价")
    raw_markdown: Optional[str] = Field(None, description="AI 生成的 Markdown 全文")


class ResumeResponse(BaseModel):
    """简历响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    target_job_id: Optional[int] = None
    customized_content: Optional[ResumeContent] = None
    pdf_url: Optional[str] = None
    version: int
    created_at: datetime


class ResumeListResponse(BaseModel):
    """简历列表响应。"""

    items: List[ResumeResponse]
    total: int


# ===== 简历模板 =====

class ResumeTemplateResponse(BaseModel):
    """简历模板响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    description: Optional[str] = None
    html_structure: str
    css_rules: str
    preview_url: Optional[str] = None
    is_builtin: bool
    is_public: bool
    downloads: int
    created_at: datetime


class ResumeTemplateListResponse(BaseModel):
    """模板列表。"""

    items: List[ResumeTemplateResponse]
    total: int


class ResumeGenerateV2(ResumeGenerate):
    """生成简历请求 v2 —— 新增模板选择。"""

    template_id: Optional[int] = Field(None, description="简历模板 ID")


class ResumeAnalysisRequest(BaseModel):
    """简历分析请求。"""

    resume_text: str = Field(..., min_length=50, description="简历文本内容")
    target_job_category: Optional[str] = Field(None, description="目标岗位类别")


class ResumeAnalysisResponse(BaseModel):
    """简历分析结果。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ats_score: Optional[int] = None
    skills_matched: Optional[Any] = None
    missing_keywords: Optional[Any] = None
    suggestions: Optional[Any] = None
    created_at: datetime
