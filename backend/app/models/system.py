"""系统监控与日志数据模型。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CrawlLog(Base):
    """爬虫采集日志。"""

    __tablename__ = "crawl_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(128), nullable=False, index=True, comment="数据源名称")
    status: Mapped[str] = mapped_column(String(32), default="running", comment="running/success/failed")
    items_added: Mapped[int] = mapped_column(Integer, default=0, comment="新增数量")
    items_skipped: Mapped[int] = mapped_column(Integer, default=0, comment="已存在跳过数量")
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<CrawlLog(source={self.source}, status={self.status})>"


class AuditLog(Base):
    """操作审计日志。"""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, comment="操作类型")
    resource: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="操作资源")
    details: Mapped[str | None] = mapped_column(Text, nullable=True, comment="详细信息 JSON")
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<AuditLog(action={self.action}, resource={self.resource})>"


class UserSubscription(Base):
    """用户订阅关键词。"""

    __tablename__ = "user_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    keywords: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="订阅关键词")
    locations: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="关注城市")
    categories: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="关注行业")
    notify_email: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否邮件通知")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<UserSubscription(user_id={self.user_id}, keywords={self.keywords})>"
