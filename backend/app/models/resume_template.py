"""简历模板数据模型。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ResumeTemplate(Base):
    """简历模板（内置 + 用户自定义）。"""

    __tablename__ = "resume_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="模板名称")
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="通用",
        comment="模板分类：经典/现代/创意/极简/学术/科技"
    )
    description: Mapped[str] = mapped_column(String(500), nullable=True, comment="模板描述")
    html_structure: Mapped[str] = mapped_column(Text, nullable=False, comment="HTML 结构")
    css_rules: Mapped[str] = mapped_column(Text, nullable=False, comment="CSS 样式")
    preview_url: Mapped[str] = mapped_column(String(500), nullable=True, comment="预览图 URL")
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否内置模板")
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否公开")
    uploader_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="上传者 ID（用户自定义模板）"
    )
    downloads: Mapped[int] = mapped_column(Integer, default=0, comment="下载次数")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ResumeTemplate(id={self.id}, name={self.name})>"


class ResumeAnalysis(Base):
    """AI 简历分析结果。"""

    __tablename__ = "resume_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="用户 ID")
    resume_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="关联的简历 ID"
    )
    original_text: Mapped[str] = mapped_column(Text, nullable=True, comment="原始简历文本")
    ats_score: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="ATS 兼容性评分 0-100")
    skills_matched: Mapped[str] = mapped_column(Text, nullable=True, comment="匹配的技能 JSON")
    missing_keywords: Mapped[str] = mapped_column(Text, nullable=True, comment="缺失的关键词 JSON")
    suggestions: Mapped[str] = mapped_column(Text, nullable=True, comment="优化建议 JSON")
    raw_ai_response: Mapped[str] = mapped_column(Text, nullable=True, comment="AI 原始响应")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ResumeAnalysis(id={self.id}, user_id={self.user_id})>"
