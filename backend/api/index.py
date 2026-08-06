"""Vercel Serverless 入口（Python WSGI）。

Vercel Python Functions 使用 WSGI 协议，FastAPI 是 ASGI 应用，
通过 a2wsgi 将 FastAPI 包装为 WSGI 应用供 Vercel 调用。
"""

import os
import sys
from pathlib import Path

# 将 backend 目录加入 sys.path，确保可以导入 app 包
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from a2wsgi import ASGIMiddleware  # noqa: E402

from app.main import app as fastapi_app  # noqa: E402

# Vercel 期望的 WSGI 应用入口
app = ASGIMiddleware(fastapi_app)
