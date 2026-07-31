# 秋招助手 24 小时在线部署指南

> 目标：把项目部署到免费云平台，实现 24 小时随时访问，任何人都能通过网址访问。

## 架构总览

```
用户浏览器
    ↓
Vercel（前端网页，自带 CDN + HTTPS）
    ↓ 调用 API
Fly.io（后端 API 服务，永不休眠）
    ↓ 读写数据
Supabase（PostgreSQL 数据库，免费 500MB）
```

**最终效果**：
- 前端网址：`https://campus-recruitment.vercel.app`（示例）
- 后端 API：`https://campus-recruitment-backend.fly.dev/docs`
- 24 小时在线，任何人可访问

**预计耗时**：30-60 分钟
**费用**：完全免费（各平台免费额度内）

---

## 第一步：推送代码到 GitHub

### 1.1 在 GitHub 创建空仓库

1. 打开 https://github.com/new
2. Repository name 填：`campus-recruitment`
3. 选择 **Public**（开源项目）
4. **不要**勾选 "Add a README file"（项目已有）
5. 点击 **Create repository**

### 1.2 本地初始化并推送

在项目根目录 `d:\trae\秋招网站` 打开终端，依次执行：

```bash
# 初始化 git 仓库
git init
git branch -M main

# 添加所有文件（.gitignore 会自动排除敏感文件和 node_modules）
git add .

# 首次提交
git commit -m "feat: 秋招助手开源网站初始版本"

# 关联远程仓库（把 your-username 换成你的 GitHub 用户名）
git remote add origin https://github.com/your-username/campus-recruitment.git

# 推送
git push -u origin main
```

> 推送后刷新 GitHub 页面，确认代码已上传。

---

## 第二步：创建 Supabase 数据库

### 2.1 注册并创建项目

1. 打开 https://supabase.com，点击 **Start your project**，用 GitHub 登录
2. 点击 **New Project**
3. 填写：
   - Name：`campus-recruitment`
   - Database Password：**生成一个强密码并保存好**（后面要用）
   - Region：`Southeast Asia (Singapore)` 或 `East Asia`
4. 点击 **Create new project**，等待约 2 分钟初始化

### 2.2 获取数据库连接串

1. 进入项目后，左侧菜单点击 **Project Settings**（齿轮图标）
2. 点击 **Database**
3. 找到 **Connection string** 区域，选择 **URI** 格式
4. 复制连接串，格式类似：
   ```
   postgresql://postgres.[你的项目ID]:[你的密码]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
   ```

### 2.3 转为 asyncpg 格式

把连接串中的 `postgresql://` 改为 `postgresql+asyncpg://`：

```
postgresql+asyncpg://postgres.[项目ID]:[密码]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
```

> **保存这个连接串**，下一步要用。

### 2.4 初始化数据库表

在 Supabase 的 SQL Editor 中执行以下 SQL（创建所有表）：

1. 左侧菜单点击 **SQL Editor**
2. 点击 **New query**
3. 复制粘贴项目 `scripts/init_db.py` 生成的 SQL，或直接在本地运行：

```bash
# 本地临时设置数据库连接，运行初始化脚本
cd d:\trae\秋招网站\backend
set DATABASE_URL=postgresql+asyncpg://postgres.[项目ID]:[密码]@aws-0-xxx.supabase.com:5432/postgres
python ..\scripts\init_db.py
```

> 也可以先跳过这步，后端首次启动时开发模式会自动建表（但生产模式需手动）。

---

## 第三步：部署后端到 Fly.io

### 3.1 安装 flyctl CLI

```powershell
# PowerShell 管理员模式运行
iwr https://fly.io/install.ps1 -useb | iex
```

安装后重启终端，验证：

```bash
fly version
```

### 3.2 登录 Fly.io

```bash
fly auth login
```

浏览器会打开 Fly.io 登录页，用 GitHub 登录（首次需注册账号）。

### 3.3 部署后端

```bash
cd d:\trae\秋招网站\backend

# 首次初始化（会读取已有的 fly.toml 配置）
fly launch --no-deploy

# 提示选择时：
# - Copy configuration to the new app? 选 Yes
# - App name: campus-recruitment-backend（或自定义）
# - Choose region: Tokyo (nrt) - 离中国最近
```

### 3.4 设置环境变量

```bash
# 数据库连接（替换为你的 Supabase 连接串）
fly secrets set DATABASE_URL="postgresql+asyncpg://postgres.xxx:密码@xxx.supabase.com:5432/postgres"

# JWT 密钥（生成一个随机密钥）
fly secrets set SECRET_KEY="请用 openssl rand -hex 32 生成一个替换这里"

# CORS 允许的前端域名（部署前端后填入 Vercel 地址，先用通配）
fly secrets set BACKEND_CORS_ORIGINS='["https://campus-recruitment.vercel.app","http://localhost:5173"]'

# AI 配置（可选，用户也可在前端自行配置）
fly secrets set DEEPSEEK_API_KEY="你的 DeepSeek API Key"
```

### 3.5 正式部署

```bash
fly deploy
```

部署完成后会显示后端地址：`https://campus-recruitment-backend.fly.dev`

验证：
```bash
# 浏览器打开
https://campus-recruitment-backend.fly.dev/api/v1/health
# 应返回 {"status":"ok","app":"秋招助手后端"}

# API 文档
https://campus-recruitment-backend.fly.dev/docs
```

> **保存后端地址**，下一步前端要用。

---

## 第四步：部署前端到 Vercel

### 4.1 导入项目

1. 打开 https://vercel.com，点击 **Sign Up** / **Log In**，用 GitHub 登录
2. 点击 **Add New Project**
3. 在 Import Git Repository 中找到 `campus-recruitment` 仓库
4. 点击 **Import**

### 4.2 配置构建

在 Configure Project 页面：

| 配置项 | 值 |
|--------|-----|
| Framework Preset | Vue.js |
| Root Directory | `frontend` |
| Build Command | `npm run build`（自动识别） |
| Output Directory | `dist`（自动识别） |

### 4.3 设置环境变量

在 **Environment Variables** 区域添加：

| 变量名 | 值 |
|--------|-----|
| `VITE_API_BASE_URL` | `https://campus-recruitment-backend.fly.dev/api/v1`（替换为你的后端地址） |

### 4.4 部署

点击 **Deploy**，等待 1-2 分钟构建完成。

部署成功后获得前端地址：`https://campus-recruitment.vercel.app`

---

## 第五步：更新后端 CORS 配置

部署前端后，把 Vercel 域名加入后端 CORS 白名单：

```bash
cd d:\trae\秋招网站\backend

# 替换为你的实际 Vercel 域名
fly secrets set BACKEND_CORS_ORIGINS='["https://campus-recruitment.vercel.app","http://localhost:5173"]'

# 不需要重新部署，secrets 更新后自动重启
```

---

## 第六步：验证

1. 打开前端网址 `https://你的域名.vercel.app`
2. 注册账号并登录
3. 浏览岗位列表（应有 300+ 条数据）
4. 进入「AI 设置」页面，添加你的 AI API Key
5. 测试生成简历
6. 在手机上打开同一网址，确认可访问

---

## 初始化数据库数据（可选）

如果 Supabase 数据库是空的，需要插入种子数据：

### 方法一：本地运行脚本

```bash
cd d:\trae\秋招网站\backend

# 设置临时环境变量指向 Supabase
$env:DATABASE_URL="postgresql+asyncpg://postgres.xxx:密码@xxx.supabase.com:5432/postgres"

# 运行种子数据脚本
python ..\scripts\seed_data.py
```

### 方法二：Fly.io 容器内执行

```bash
fly ssh console

# 进入容器后执行
python /app/../scripts/seed_data.py
```

---

## 常见问题

### Q: Fly.io 部署失败，提示内存不足？

Fly.io 免费额度可能有限制。尝试调整 `fly.toml` 中的内存：
```toml
[[vm]]
  memory = "256mb"  # 降到最小规格
```

### Q: 后端访问报 502/503？

检查日志：
```bash
fly logs
```
通常是数据库连接失败，确认 `DATABASE_URL` 格式正确（`postgresql+asyncpg://`）。

### Q: 前端访问报 CORS 错误？

确认后端环境变量 `BACKEND_CORS_ORIGINS` 包含了你的 Vercel 域名。

### Q: Fly.io 免费额度用完？

Fly.io 免费额度为 3 个 shared-cpu-1x 256MB 实例。如果超限：
- 改用 Render 免费版（会休眠，但可接受）
- 或购买付费计划（$1.95/月起）

### Q: 如何绑定自定义域名？

- Vercel：Project Settings → Domains → 添加域名
- Fly.io：`fly certs add your-domain.com`

---

## 后续更新

代码推送到 GitHub 后：
- **Vercel** 会自动重新构建部署前端
- **Fly.io** 需手动执行 `fly deploy` 更新后端

---

## 各平台管理入口

| 平台 | 管理地址 | 用途 |
|------|---------|------|
| GitHub | https://github.com/your-username/campus-recruitment | 代码仓库 |
| Supabase | https://supabase.com/dashboard | 数据库管理 |
| Fly.io | https://fly.io/dashboard | 后端服务 |
| Vercel | https://vercel.com/dashboard | 前端部署 |
