from __future__ import annotations
"""应用配置管理。

使用 pydantic-settings 从环境变量 / .env 文件加载配置。
所有配置项均有默认值，方便本地开发。
"""

from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===== 应用配置 =====
    APP_NAME: str = "秋招助手后端"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # CORS 允许的源（JSON 字符串或逗号分隔）
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # ===== 数据库 =====
    DATABASE_URL: str = "sqlite+aiosqlite:///./campus_recruit.db"

    # ===== JWT 配置 =====
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ===== Cookie 配置 =====
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    # ===== DeepSeek AI 配置 =====
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    AI_DAILY_LIMIT: int = 5

    # ===== GitHub OAuth 配置 =====
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/oauth/github/callback"

    # ===== 邮件服务 =====
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@example.com"

    # ===== Redis =====
    REDIS_URL: str = ""

    # ===== 安全配置 =====
    # 登录失败锁定：同一IP 5次失败后锁定30分钟
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 30
    # 注册速率限制：同一IP每小时最多3次
    REGISTER_RATE_PER_HOUR: int = 3
    # 文件上传限制
    MAX_UPLOAD_SIZE_MB: int = 5
    ALLOWED_UPLOAD_TYPES: list[str] = [
        "image/jpeg", "image/png", "image/webp",
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    # 服务器IP（用于 CORS 白名单 + HTTPS 重定向）
    SERVER_IP: str = "120.53.31.101"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _ensure_async_postgres(cls, v: Any) -> Any:
        """自动将 postgresql:// 转为 postgresql+asyncpg:// 供 SQLAlchemy 异步引擎使用。"""
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _assemble_cors_origins(cls, v: Any) -> list[str]:
        """支持 JSON 数组或逗号分隔字符串两种格式。"""
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, (list, str)):
            return v  # pydantic 会自动解析 JSON 字符串
        raise ValueError(v)

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_async_sqlite(self) -> bool:
        return "sqlite" in self.DATABASE_URL


@lru_cache
def get_settings() -> Settings:
    """获取全局配置单例（带缓存，避免重复读取 .env）。"""
    return Settings()


settings = get_settings()
