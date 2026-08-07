# ============================================================
# 秋招助手后端 Dockerfile
# 适用于 Railway / Fly.io / Render / 任意支持 Docker 的云平台
# ============================================================

# ===== 构建阶段 =====
FROM python:3.11-slim AS builder

# 设置环境变量，避免 Python 生成 .pyc 文件、启用无缓冲输出
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 替换 apt 源为腾讯云镜像（国内加速）
RUN sed -i 's|http://deb.debian.org|http://mirrors.cloud.tencent.com|g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖（编译 asyncpg / bcrypt 等需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用 Docker 缓存层
COPY requirements.txt .

# 注释掉 playwright 行（部署时不需要浏览器自动化，减小镜像体积约 500MB）
RUN sed -i 's/^playwright/# playwright/' requirements.txt

RUN pip install --user --no-cache-dir -i https://mirrors.cloud.tencent.com/pypi/simple -r requirements.txt

# ===== 运行阶段 =====
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH

WORKDIR /app

# 替换 apt 源为腾讯云镜像（国内加速）
RUN sed -i 's|http://deb.debian.org|http://mirrors.cloud.tencent.com|g' /etc/apt/sources.list.d/debian.sources

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

# 启动命令：v2.1 迁移 → 初始化+种子数据 → 30套模板 → 岗位投递信息 → 启动服务
# 所有脚本幂等，每次部署安全重复执行
CMD python scripts/migrate_v2.py && python init_and_seed.py && python scripts/seed_templates.py && python scripts/update_jobs_with_real_data.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2
