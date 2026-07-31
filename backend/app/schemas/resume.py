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
