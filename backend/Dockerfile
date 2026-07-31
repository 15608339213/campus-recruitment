# ============================================================
# 秋招助手后端 Dockerfile
# 适用于 Fly.io / Render / 任意支持 Docker 的云平台
# ============================================================

# ===== 构建阶段 =====
FROM python:3.11-slim AS builder

# 设置环境变量，避免 Python 生成 .pyc 文件、启用无缓冲输出
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 安装系统依赖（编译 asyncpg / bcrypt 等需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用 Docker 缓存层
COPY requirements.txt .

# 注释掉 playwright 行（部署时不需要浏览器自动化，减小镜像体积约 500MB）
RUN sed -i 's/^playwright/# playwright/' requirements.txt

RUN pip install --user --no-cache-dir -r requirements.txt

# ===== 运行阶段 =====
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH

WORKDIR /app

# 仅安装运行时必要的系统库
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 阶段复制已安装的 Python 包
COPY --from=builder /root/.local /root/.local

# 复制项目代码
COPY . .

# 暴露端口（Fly.io / Render 等平台通过 PORT 环境变量指定）
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# 启动命令，支持通过 PORT 环境变量覆盖端口
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2
