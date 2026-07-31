"""AI 提供商配置模型。

每个用户可以保存自己的 AI 服务商配置（API Key、Base URL、模型名），
在简历生成时选择使用哪个提供商。
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AIProviderConfig(Base):
    """用户自定义 AI 提供商配置。"""

    __tablename__ = "ai_provider_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # 提供商标识：deepseek / openai / moonshot / zhipu / qwen / baichuan / yi / custom
    provider_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="AI 提供商标识")
    # 用户给这个配置起的名字，如"我的 DeepSeek"
    display_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="显示名称")
    # API 配置
    api_key: Mapped[str] = mapped_column(Text, nullable=False, comment="API 密钥（加密存储建议）")
    base_url: Mapped[str] = mapped_column(String(512), nullable=False, comment="API 基础地址")
    model: Mapped[str] = mapped_column(String(128), nullable=False, comment="模型名称")
    # 是否为当前激活的提供商
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否为当前选中的提供商"
    )
    # 连接测试状态
    last_tested: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="上次测试时间"
    )
    last_test_ok: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="上次测试是否成功"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # 关系
    user: Mapped["User"] = relationship(back_populates="ai_provider_configs")  # noqa: F821

    def __repr__(self) -> str:
        return f"<AIProviderConfig(id={self.id}, provider={self.provider_id}, model={self.model})>"
