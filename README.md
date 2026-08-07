# 秋招助手网站

> 一站式开源校园招聘助手平台 —— 岗位聚合、AI 简历生成、行业数据分析、面试题库，助力应届生高效备战秋招。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Vue](https://img.shields.io/badge/Vue-3.4-brightgreen.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)

## 项目简介

秋招助手是一个**开源**的面向高校应届毕业生的校园招聘信息聚合与辅助平台。项目通过定时爬取多平台校招信息（智联招聘、Boss直聘、国聘、企业官网、GitHub 社区仓库），结合多 AI 提供商能力为用户提供智能简历生成、面试技巧推荐、行业趋势分析等功能，帮助求职者在秋招季快速找到心仪岗位。

### 核心亮点

- **多平台岗位聚合**：自动爬取智联招聘、Boss直聘、国聘等招聘平台及企业官网校招信息，支持多维度筛选与搜索
- **多 AI 提供商简历生成**：用户可自行添加任意 AI 服务商（DeepSeek、OpenAI、通义千问、智谱GLM、Kimi 等），选择喜欢的模型生成定制化简历
- **行业数据分析**：基于 ECharts 的可视化数据看板，洞察行业招聘趋势
- **面试题库**：按岗位类别整理的笔试/面试题目与参考答案
- **完全开源**：MIT 协议，任何人都可以自由部署和使用

## 技术栈

### 前端

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue 3 | ^3.4 | 渐进式 JavaScript 框架 |
| TypeScript | ^5.5 | 类型安全 |
| Vite | ^5.4 | 构建工具与开发服务器 |
| Vue Router | ^4.4 | 官方路由 |
| Pinia | ^2.2 | 状态管理 |
| Naive UI | ^2.39 | 组件库 |
| Tailwind CSS | ^3.4 | 原子化 CSS |
| ECharts | ^5.5 | 数据可视化 |

### 后端

| 技术 | 版本 | 说明 |
|------|------|------|
| FastAPI | ^0.115 | 高性能异步 Web 框架 |
| SQLAlchemy | ^2.0 | ORM（异步模式） |
| asyncpg | ^0.30 | PostgreSQL 异步驱动 |
| Alembic | ^1.14 | 数据库迁移 |
| Pydantic | ^2.10 | 数据校验 |
| python-jose | ^3.3 | JWT 认证 |
| passlib | ^1.7 | 密码哈希（bcrypt） |
| httpx | ^0.28 | 异步 HTTP 客户端 |

### 基础设施

| 技术 | 说明 |
|------|------|
| PostgreSQL 15 | 关系型数据库 |
| Redis 7 | 缓存与限流 |
| Docker Compose | 一键部署全栈服务 |
| GitHub Actions | CI/CD 与定时爬虫 |

## 功能列表

### 用户模块

- 邮箱注册 / 登录
- GitHub OAuth 第三方登录
- JWT Token 认证（Access + Refresh）
- 用户档案管理（教育背景、技能、项目经历）
- 学生身份验证

### 岗位模块

- 岗位列表浏览与分页
- 多维度筛选（城市、企业类型、岗位类别、薪资范围）
- 关键词搜索
- 岗位详情查看
- 岗位收藏与备注
- 招聘截止日期提醒

### AI 简历模块

- **多 AI 提供商支持**：用户可在「AI 设置」页面自行添加任意 AI 服务商
- 支持的内置提供商：
  - DeepSeek（deepseek-chat）
  - OpenAI（GPT-4o / GPT-4o-mini）
  - 通义千问（Qwen-Max / Qwen-Plus）
  - 智谱 GLM（GLM-4 / GLM-3-Turbo）
  - Moonshot Kimi（moonshot-v1-8k / 32k）
  - 百川（Baichuan2）
  - 零一万物（Yi-34B-Chat）
  - 任意兼容 OpenAI 接口的自定义服务商
- 根据目标岗位 AI 生成定制化简历
- 连接测试功能
- 每日 AI 使用次数限制

### 数据采集模块（爬虫）

- **智联招聘**：校招岗位抓取，支持多关键词搜索
- **Boss直聘**：校招岗位抓取，HTML + API 双模式
- **国聘**：国企校招岗位抓取
- **企业官网**：字节跳动、阿里巴巴、腾讯等
- **GitHub 社区仓库**：13+ 个社区维护的校招信息汇总仓库
- 数据清洗、去重、标签增强（可选 LLM 增强）
- 自动写入数据库

### 数据分析模块

- 招聘趋势可视化看板
- 行业分布统计
- 城市分布分析
- 薪资水平对比
- 每日数据快照

### 面试题库模块

- 按岗位类别浏览题目
- 笔试 / 面试 / HR 面分类
- 难度分级（easy / medium / hard）
- 参考答案

### 反馈模块

- 用户反馈提交（功能建议 / Bug 反馈 / 内容投诉 / 表扬鼓励）
- 管理员回复处理
- 访问日志记录

## 快速开始

### 环境要求

- Node.js >= 18（推荐 20 LTS）
- Python >= 3.11
- Docker Desktop（用于一键启动全栈服务）
- Git

### 方式一：Docker Compose 一键启动（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/campus-recruitment.git
cd campus-recruitment

# 2. 复制环境变量配置
cp .env.example .env
# 编辑 .env，至少配置 SECRET_KEY 和 DEEPSEEK_API_KEY

# 3. 一键启动全栈服务（PostgreSQL + Redis + 后端 + 前端）
docker compose --profile full up -d --build

# 4. 查看服务状态
docker compose ps

# 访问地址：
#   前端：  http://localhost:8080
#   后端API：http://localhost:8000/docs
```

### 方式二：本地开发模式

#### 1. 启动基础设施（PostgreSQL + Redis）

```bash
# 仅启动数据库和缓存
docker compose up -d postgres redis

# 查看服务状态
docker compose ps

# 如需数据库可视化管理工具 pgAdmin（可选）
docker compose --profile pgadmin up -d pgadmin
# 然后访问 http://localhost:5050
# 默认账号：admin@campus.com / admin123
```

#### 2. 配置后端环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env，配置数据库连接、API 密钥等
```

关键字段说明：

```bash
# 使用 Docker 启动的 PostgreSQL
DATABASE_URL=postgresql+asyncpg://campus:campus123@localhost:5432/campus_recruitment
# Redis
REDIS_URL=redis://localhost:6379/0
# DeepSeek API 密钥（系统默认 AI 提供商，用户也可在前端自行配置其他 AI）
DEEPSEEK_API_KEY=your-api-key
# GitHub Token（用于爬虫提升 API 速率限制）
GITHUB_TOKEN=ghp-your-token
```

#### 3. 安装后端依赖并启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate    # Linux / macOS
# venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 初始化数据库（建表 + 创建管理员账号）
python ../scripts/init_db.py

# 插入种子数据（300 条示例岗位 + 面试题库）
python ../scripts/seed_data.py

# 启动开发服务器
uvicorn app.main:app --reload --port 8000

# 访问 API 文档
# http://localhost:8000/docs
```

#### 4. 安装前端依赖并启动

```bash
cd frontend

# 安装依赖
npm install

# 复制环境变量
cp .env.example .env
# 编辑 .env，配置 API 地址
# VITE_API_BASE_URL=http://localhost:8000

# 启动开发服务器
npm run dev

# 访问前端
# http://localhost:5173
```

#### 5. 运行爬虫（可选）

```bash
cd crawler

# 设置环境变量
set DATABASE_URL=postgresql+psycopg2://campus:campus123@localhost:5432/campus_recruitment
set GITHUB_TOKEN=ghp-your-token
# Windows PowerShell 使用 $env:DATABASE_URL="..."

# 运行爬虫
python run.py

# 仅抓取 GitHub 仓库数据
python run.py --no-companies

# 仅抓取企业官网数据
python run.py --no-github

# 输出到 JSON 文件（不写入数据库）
python run.py --output result.json
```

## AI 提供商配置

本系统支持用户自行添加任意 AI 服务商来生成简历，无需管理员配置。

### 使用方法

1. 注册并登录秋招助手网站
2. 进入「AI 设置」页面
3. 点击「添加配置」
4. 选择 AI 服务商（或选择「自定义」输入任意兼容 OpenAI 接口的服务）
5. 填入 API Key、API 地址、模型名称
6. 点击「测试连接」验证可用性
7. 设为当前使用并保存

### 支持的 AI 服务商

| 服务商 | 默认模型 | API 地址 | 获取 API Key |
|--------|---------|---------|------------|
| DeepSeek | deepseek-chat | https://api.deepseek.com | https://platform.deepseek.com |
| OpenAI | gpt-4o-mini | https://api.openai.com | https://platform.openai.com |
| 通义千问 | qwen-plus | https://dashscope.aliyuncs.com/compatible-mode | https://dashscope.console.aliyun.com |
| 智谱 GLM | glm-4 | https://open.bigmodel.cn | https://open.bigmodel.cn |
| Moonshot Kimi | moonshot-v1-8k | https://api.moonshot.cn | https://platform.moonshot.cn |
| 百川 | Baichuan2-Turbo | https://api.baichuan-ai.com | https://platform.baichuan-ai.com |
| 零一万物 | yi-large | https://api.lingyiwanwu.com | https://platform.lingyiwanwu.com |
| 自定义 | 用户指定 | 用户指定 | - |

## 数据采集源

### 招聘平台

| 平台 | 数据类型 | 说明 |
|------|---------|------|
| 智联招聘 | 校招岗位 | 多关键词搜索，API + HTML 双模式 |
| Boss直聘 | 校招岗位 | HTML 解析 + API 接口 |
| 国聘 | 国企校招 | API 接口为主 |

### 企业官网

字节跳动、阿里巴巴、腾讯等企业的官方校招页面。

### GitHub 社区仓库

从 13+ 个社区维护的校招信息汇总仓库抓取数据，支持 Markdown 表格和 JSON 格式解析。

## 项目结构

```
campus-recruitment/
├── backend/                      # 后端（FastAPI）
│   ├── alembic/                  # 数据库迁移
│   ├── app/
│   │   ├── api/                  # API 路由层
│   │   │   ├── ai_provider.py   # AI 提供商管理
│   │   │   ├── analysis.py       # 行业分析
│   │   │   ├── auth.py           # 认证
│   │   │   ├── feedback.py       # 用户反馈
│   │   │   ├── interview.py      # 面试题库
│   │   │   ├── jobs.py           # 岗位
│   │   │   └── resume.py         # AI 简历
│   │   ├── core/                 # 核心模块
│   │   ├── models/               # 数据模型（SQLAlchemy ORM）
│   │   ├── schemas/               # Pydantic 数据校验
│   │   ├── services/             # 业务逻辑层
│   │   │   └── ai/               # AI 服务（多提供商抽象层）
│   │   │       ├── provider.py   # 统一 AI 客户端
│   │   │       └── deepseek.py   # DeepSeek 实现
│   │   └── main.py               # 应用入口
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                     # 前端（Vue 3）
│   ├── src/
│   │   ├── views/                # 页面组件
│   │   │   └── settings/
│   │   │       └── AISettings.vue # AI 提供商设置页
│   │   ├── api/                  # API 调用
│   │   ├── router/               # 路由配置
│   │   └── stores/               # Pinia 状态管理
│   ├── Dockerfile
│   ├── nginx.conf                # Nginx 配置
│   └── .env.example
├── crawler/                      # 爬虫模块
│   ├── adapters/                 # 平台适配器
│   │   ├── zhaopin.py            # 智联招聘
│   │   ├── boss.py               # Boss直聘
│   │   ├── iguopin.py            # 国聘
│   │   ├── bytedance.py          # 字节跳动
│   │   ├── alibaba.py            # 阿里巴巴
│   │   └── tencent.py            # 腾讯
│   ├── sources/                  # 数据源
│   │   └── github_repos.py       # GitHub 仓库
│   ├── pipeline.py               # 数据清洗管线
│   ├── requirements.txt
│   └── run.py                    # 爬虫入口
├── scripts/                      # 工具脚本
│   ├── init_db.py                # 数据库初始化
│   └── seed_data.py              # 种子数据生成（300 条岗位）
├── campus-recruitment-dashboard/ # 数据看板（独立）
├── docs/                         # 项目文档
├── .github/workflows/            # CI/CD 配置
│   ├── ci.yml                    # CI 测试
│   └── crawler.yml               # 定时爬虫
├── docker-compose.yml            # 全栈服务编排
├── .env.example                  # 环境变量示例
└── README.md
```

## 开发指南

### 后端开发

#### 数据库迁移（Alembic）

```bash
cd backend

# 生成迁移脚本（修改模型后执行）
alembic revision --autogenerate -m "描述变更内容"

# 执行迁移
alembic upgrade head

# 回滚上一个迁移
alembic downgrade -1
```

#### 新增 API 接口

1. 在 `app/models/` 中定义数据模型
2. 在 `app/schemas/` 中定义请求/响应模型
3. 在 `app/api/` 中编写路由
4. 在 `app/main.py` 中注册路由
5. 生成并执行数据库迁移

### 前端开发

#### 新增页面

1. 在 `src/views/` 中创建页面组件
2. 在 `src/router/` 中配置路由
3. 如需状态管理，在 `src/stores/` 中创建 Pinia store
4. API 调用统一放在 `src/api/` 中

#### 命令

```bash
cd frontend

npm run dev          # 开发服务器
npm run build        # 生产构建
npm run preview      # 预览构建产物
npm run type-check   # TypeScript 类型检查
```

### 爬虫开发

#### 新增招聘平台适配器

1. 在 `crawler/adapters/` 中创建新的适配器类
2. 继承 `BaseCompanyAdapter`
3. 实现 `fetch_jobs()` 方法
4. 在 `crawler/adapters/__init__.py` 中注册

### Git 提交规范

推荐使用 Conventional Commits 格式：

```
<type>(<scope>): <subject>

类型 type：
  feat     新功能
  fix      修复 Bug
  docs     文档变更
  style    代码格式（不影响功能）
  refactor 重构
  test     测试
  chore    构建/工具变更
```

## 部署说明

### 方式一：Docker Compose 全栈部署（推荐）

```bash
# 1. 准备环境变量
cp .env.example .env
# 编辑 .env，配置 SECRET_KEY、DEEPSEEK_API_KEY 等

# 2. 一键构建并启动
docker compose --profile full up -d --build

# 3. 初始化数据库和种子数据（首次部署）
docker exec campus-backend python /app/../scripts/init_db.py
docker exec campus-backend python /app/../scripts/seed_data.py

# 4. 查看日志
docker compose logs -f backend
docker compose logs -f frontend
```

### 方式二：分服务部署

#### 前端部署

1. 构建前端：`cd frontend && npm run build`
2. 将 `dist/` 部署到任意静态文件服务器（Nginx 等）
3. 配置环境变量 `VITE_API_BASE_URL` 指向后端 API 地址

#### 后端部署

```bash
# Docker 部署
cd backend
docker build -t campus-backend .
docker run -d --name campus-backend -p 8000:8000 --env-file .env campus-backend

# 或使用云平台（Render / Railway 等）
# 1. 连接 GitHub 仓库
# 2. 指定 Root Directory 为 backend
# 3. 构建命令：pip install -r requirements.txt
# 4. 启动命令：uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### 数据库部署

- 生产环境使用独立的 PostgreSQL 托管服务（如 Supabase、RDS）
- 配置 `DATABASE_URL` 指向生产数据库
- 使用 Alembic 执行数据库迁移：`alembic upgrade head`
- 初始化管理员账号：`python scripts/init_db.py`

### 环境变量说明

| 变量 | 说明 | 示例 |
|------|------|------|
| `DATABASE_URL` | 数据库连接字符串 | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis 连接地址 | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT 签名密钥 | `openssl rand -hex 32` |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥（系统默认 AI） | `sk-...` |
| `GITHUB_TOKEN` | GitHub Token（爬虫速率限制提升） | `ghp-...` |
| `GITHUB_CLIENT_ID` | GitHub OAuth 客户端 ID | - |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth 密钥 | - |
| `SMTP_HOST` | SMTP 邮件服务器 | `smtp.example.com` |
| `MAIL_FROM` | 发件人邮箱 | `noreply@...` |

> **注意**：AI 提供商配置无需在环境变量中设置。用户可在前端「AI 设置」页面自行添加任意 AI 服务商的 API Key。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'feat: 添加 amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

## 开源协议

本项目基于 [MIT License](LICENSE) 开源协议，任何人都可以自由使用、修改和分发。

Copyright (c) 2026 Campus Recruitment Assistant
