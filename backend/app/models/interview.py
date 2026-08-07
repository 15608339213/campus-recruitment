from __future__ import annotations
from typing import Optional, List, Dict
"""面试技巧与题库数据模型。

包含：InterviewTip、QuestionBank。
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InterviewTip(Base):
    """按岗位类别缓存的面试技巧。"""

    __tablename__ = "interview_tips"
    __table_args__ = (
        # 同一岗位类别仅保留一份技巧缓存
        {"comment": "面试技巧缓存表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_category: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False, comment="岗位类别"
    )
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False, comment="技巧内容 Markdown")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<InterviewTip(id={self.id}, job_category={self.job_category})>"


class QuestionBank(Base):
    """笔试/面试题库。"""

    __tablename__ = "question_bank"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_category: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="岗位类别")
    question: Mapped[str] = mapped_column(Text, nullable=False, comment="题目")
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="参考答案")
    question_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True, comment="笔试/面试/HR面")
    difficulty: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="easy/medium/hard")
    source: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="来源")
    company: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True, comment="公司名称")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<QuestionBank(id={self.id}, job_category={self.job_category})>"


class QuestionSource(Base):
    """自定义题库源（管理员可添加外部题库 URL 自动同步）。"""

    __tablename__ = "question_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="题库源名称")
    url: Mapped[str] = mapped_column(String(512), nullable=False, comment="题库源 URL")
    format: Mapped[str] = mapped_column(String(32), default="json", comment="数据格式：json/markdown/csv")
    sync_interval_hours: Mapped[int] = mapped_column(Integer, default=24, comment="同步间隔（小时）")
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否启用")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<QuestionSource(id={self.id}, name={self.name})>"
