from __future__ import annotations
from typing import Optional, List, Dict
"""岗位相关数据模型。

包含：Job、JobTag、Favorite。
"""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Job(Base):
    """招聘岗位主表。"""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False, index=True, comment="岗位名称")
    company: Mapped[str] = mapped_column(String(256), nullable=False, index=True, comment="公司名称")
    # 企业类型：国企/民企/外企/事业单位
    company_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True, comment="工作地点")
    salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="薪资下限")
    salary_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="薪资上限")
    salary_unit: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="元/月、元/天等")
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="招聘开始日期")
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True, comment="截止日期")
    # 岗位类别：技术/产品/运营/金融/...
    job_category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    # 岗位类型：校招/实习/社招
    job_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    degree_required: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="本科/硕士/博士")
    description_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="岗位描述 HTML")
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="原始链接")
    source_repo: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, comment="来源 GitHub 仓库")
    raw_data_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="原始数据留底")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # 关系
    tags: Mapped[List["JobTag"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", lazy="selectin"
    )
    favorites: Mapped[List["Favorite"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    resumes: Mapped[List["Resume"]] = relationship(  # noqa: F821
        back_populates="target_job"
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title={self.title}, company={self.company})>"


class JobTag(Base):
    """岗位标签（多对多：六险一金/解决户口/弹性工作等）。"""

    __tablename__ = "job_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    job: Mapped["Job"] = relationship(back_populates="tags")

    def __repr__(self) -> str:
        return f"<JobTag(id={self.id}, tag={self.tag})>"


class Favorite(Base):
    """用户收藏的岗位。"""

    __tablename__ = "favorites"
    __table_args__ = (
        # 唯一约束：防止同一用户重复收藏同一岗位
        UniqueConstraint("user_id", "job_id", name="uq_user_job_favorite"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="用户备注")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="favorites")  # noqa: F821
    job: Mapped["Job"] = relationship(back_populates="favorites")

    def __repr__(self) -> str:
        return f"<Favorite(id={self.id}, user_id={self.user_id}, job_id={self.job_id})>"
