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


class ResumeUpload(Base):
    """用户上传的简历文件记录。"""

    __tablename__ = "resume_uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="原始文件名")
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="存储路径")
    file_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="文件类型：pdf/word/image")
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, comment="文件大小（bytes）")
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="提取的文本内容")
    parsed_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="AI解析后的JSON数据")
    is_imported: Mapped[bool] = mapped_column(Integer, default=0, nullable=False, comment="是否已导入资料")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ResumeUpload(id={self.id}, file_name={self.file_name})>"
