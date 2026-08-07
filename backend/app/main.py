"""FastAPI 应用入口。

- 创建 FastAPI 应用实例
- 配置 CORS 中间件
- 注册所有 API 路由
- 配置生命周期事件（启动/关闭）
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.ai_provider import router as ai_provider_router
from app.api.analysis import router as analysis_router
from app.api.auth import router as auth_router
from app.api.feedback import router as feedback_router
from app.api.interview import router as interview_router
from app.api.jobs import router as jobs_router
from app.api.resume import router as resume_router
from app.api.admin import router as admin_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理。

    启动时：初始化数据库（开发环境自动建表）
    关闭时：关闭数据库连接池
    """
    # ===== 启动 =====
    # 开发环境自动创建表（生产环境使用 Alembic 迁移）
    if settings.is_development:
        from app.core.database import init_db

        await init_db()
        print(f"[{settings.APP_NAME}] 开发环境：数据库表已自动创建")  # noqa: T201

    print(f"[{settings.APP_NAME}] 服务已启动")  # noqa: T201

    yield

    # ===== 关闭 =====
    from app.core.database import close_db

    await close_db()
    print(f"[{settings.APP_NAME}] 服务已关闭")  # noqa: T201


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例。"""
    app = FastAPI(
        title=settings.APP_NAME,
        description="秋招助手网站后端 API - 岗位聚合、AI 简历生成、行业分析、面试题库",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        lifespan=lifespan,
    )

    # ===== CORS 中间件 =====
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,  # 允许携带 cookie
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ===== 注册路由 =====
    api_prefix = settings.API_V1_PREFIX
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(jobs_router, prefix=api_prefix)
    app.include_router(resume_router, prefix=api_prefix)
    app.include_router(ai_provider_router, prefix=api_prefix)
    app.include_router(feedback_router, prefix=api_prefix)
    app.include_router(analysis_router, prefix=api_prefix)
    app.include_router(interview_router, prefix=api_prefix)
    app.include_router(admin_router, prefix=api_prefix)

    # ===== 静态文件（上传目录）=====
    import os
    os.makedirs("uploads/avatars", exist_ok=True)
    os.makedirs("uploads/resumes", exist_ok=True)
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    # ===== 健康检查 =====
    @app.get(f"{api_prefix}/health", tags=["系统"])
    async def health_check() -> dict:
        """健康检查接口。"""
        return {
            "status": "ok",
            "app": settings.APP_NAME,
            "env": settings.APP_ENV,
            "version": "1.0.0",
        }

    # ===== 全局异常处理 =====
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """全局未捕获异常处理。"""
        import traceback

        error_detail = str(exc) if settings.DEBUG else "服务器内部错误"
        if settings.DEBUG:
            traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "detail": error_detail,
                "path": str(request.url.path),
            },
        )

    return app


# 创建应用实例（uvicorn 通过 app.main:app 引用）
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
