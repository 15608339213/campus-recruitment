from __future__ import annotations
from typing import Optional, List, Dict
"""反馈与访问日志数据模型。

包含：Feedback、VisitLog。
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Feedback(Base):
    """用户反馈。"""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # 反馈类别：bug / feature / complaint / other
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="反馈内容")
    # 状态：pending / processing / resolved / closed
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False, index=True)
    admin_reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="管理员回复")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # 关系
    user: Mapped[Optional["User"]] = relationship(back_populates="feedbacks")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, category={self.category}, status={self.status})>"


class VisitLog(Base):
    """访问日志记录。"""

    __tablename__ = "visit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    path: Mapped[str] = mapped_column(String(512), nullable=False, comment="访问路径")
    ip_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="IP 哈希值，不存原始 IP")
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<VisitLog(id={self.id}, path={self.path})>"
