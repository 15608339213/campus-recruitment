from __future__ import annotations
from typing import Optional, List, Dict
"""简历相关数据模型。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Resume(Base):
    """AI 生成的定制化简历。"""

    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_job_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # AI 生成的定制内容（基本信息/教育/项目/技能/自我评价等 JSON）
    customized_content_json: Mapped[str] = mapped_column(Text, nullable=False, comment="AI 生成的简历内容 JSON")
    pdf_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="PDF 文件 URL")
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False, comment="版本号")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="resumes")  # noqa: F821
    target_job: Mapped[Optional["Job"]] = relationship(back_populates="resumes")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, user_id={self.user_id}, version={self.version})>"
