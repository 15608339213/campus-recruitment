# 秋招助手 - 腾讯云部署指南

> 基于 Docker Compose 一键部署全栈应用到腾讯云轻量服务器。
> 适合学生和个人开发者，一台服务器搞定前端+后端+数据库。

## 架构总览

```
用户浏览器
    ↓
腾讯云轻量服务器（公网 IP）
    ↓
Nginx（80 端口，前端静态资源 + API 反向代理）
    ↓ /api/ 转发
FastAPI 后端（Docker 容器，8000 端口）
    ↓ 读写数据
PostgreSQL 15（Docker 容器，5432 端口）
Redis 7（Docker 容器，6379 端口）
```

**访问地址**：`http://你的服务器IP`
**管理面板**：`http://你的服务器IP/api/v1/docs`
**管理员账号**：admin@campus.com / admin123

---

## 第一步：购买腾讯云服务器

### 1.1 学生认证（享受学生优惠）

1. 打开 https://cloud.tencent.com/act/campus
2. 点击"学生认证"，用学信网信息完成认证
3. 认证后可享受学生折扣价

### 1.2 购买轻量应用服务器

1. 选择"轻量应用服务器 2核2G"
2. 配置：
   - **地域**：北京/上海/广州（选离你最近的）
   - **镜像**：Ubuntu 22.04 LTS（推荐）
   - **带宽**：4M/每月 300GB 流量（够用）
   - **时长**：1年（学生价约 100 元/年）
3. 购买成功后，记住服务器的**公网 IP**和初始密码

### 1.3 开放防火墙端口

在腾讯云控制台 → 轻量服务器 → 防火墙，添加规则：

| 协议 | 端口 | 说明 |
|------|------|------|
| TCP | 80 | HTTP 前端访问 |
| TCP | 443 | HTTPS（可选，后续配域名时用） |
| TCP | 22 | SSH 连接（默认已开放） |

> 不需要开放 5432/6379/8000，这些端口只在 Docker 内网使用。

---

## 第二步：连接服务器并安装 Docker

### 2.1 SSH 连接服务器

```bash
# 用你的服务器 IP 替换
ssh ubuntu@你的服务器IP
```

输入初始密码登录（首次登录会提示修改密码）。

### 2.2 安装 Docker

```bash
# 一键安装 Docker
curl -fsSL https://get.docker.com | sudo sh

# 启动 Docker 并设置开机自启
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
docker compose version
```

### 2.3 配置 Docker 镜像加速（国内必做）

```bash
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://docker.mirrors.ustc.edu.cn"
  ]
}
EOF
sudo systemctl daemon-reload
sudo systemctl restart docker
```

---

## 第三步：拉取代码并部署

### 3.1 安装 Git 并克隆项目

```bash
# 安装 Git
sudo apt-get update && sudo apt-get install -y git

# 克隆项目
cd ~
git clone https://github.com/15608339213/campus-recruitment.git
cd campus-recruitment
```

### 3.2 一键部署

```bash
# 赋予执行权限
chmod +x deploy.sh

# 执行部署脚本（首次约需 5-10 分钟，会自动构建 Docker 镜像）
./deploy.sh
```

或者手动执行：

```bash
docker compose up -d --build
```

### 3.3 检查部署状态

```bash
# 查看所有容器状态
docker compose ps

# 查看后端日志
docker compose logs -f backend

# 测试健康检查
curl http://localhost/api/v1/health
# 应返回 {"status":"ok","app":"秋招助手后端"}
```

---

## 第四步：访问验证

1. 浏览器打开 `http://你的服务器IP`
2. 应看到秋招助手前端页面
3. 注册账号并登录
4. 浏览岗位列表（应有 300+ 条数据）
5. API 文档：`http://你的服务器IP/api/v1/docs`

管理员账号：`admin@campus.com` / `admin123`

---

## 常用运维命令

```bash
# 查看服务状态
docker compose ps

# 查看实时日志
docker compose logs -f

# 仅查看后端日志
docker compose logs -f backend

# 重启所有服务
docker compose restart

# 重启单个服务
docker compose restart backend

# 停止所有服务
docker compose down

# 停止并删除数据（慎用！会清空数据库）
docker compose down -v

# 重新构建并启动（更新代码后执行）
git pull
docker compose up -d --build
```

---

## 更新代码

```bash
cd ~/campus-recruitment

# 拉取最新代码
git pull origin main

# 重新构建并启动
docker compose up -d --build

# 查看日志确认启动成功
docker compose logs -f backend
```

---

## 可选：绑定域名

### 1. 购买域名

在腾讯云购买域名（约 30-80 元/年），完成备案。

### 2. 添加域名解析

腾讯云控制台 → DNS 解析 DNSPod → 添加记录：
- 主机记录：`@`
- 记录类型：A
- 记录值：你的服务器 IP

### 3. 配置 HTTPS

```bash
# 安装 certbot
sudo apt-get install -y certbot python3-certbot-nginx

# 申请 SSL 证书
sudo certbot --nginx -d 你的域名.com

# 修改 nginx 配置启用 HTTPS
```

---

## 可选：开启 pgAdmin 数据库管理

```bash
# 启动 pgAdmin
docker compose --profile pgadmin up -d pgadmin

# 访问 http://你的服务器IP:5050
# 账号：admin@campus.com / admin123
```

---

## 常见问题

### Q: 部署后访问不了？

1. 检查防火墙是否开放 80 端口
2. 检查容器是否正常运行：`docker compose ps`
3. 查看日志：`docker compose logs`

### Q: 后端启动失败？

```bash
# 查看后端日志
docker compose logs backend

# 常见原因：
# 1. 数据库未就绪 → 等待 30 秒后重试
# 2. 内存不足 → 2G 服务器可能需要添加 swap
```

### Q: 内存不足（OOM）？

2G 内存服务器如果构建时 OOM，添加 swap：

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
# 永久生效
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Q: 如何备份数据库？

```bash
# 备份
docker exec campus-postgres pg_dump -U campus campus_recruitment > backup_$(date +%Y%m%d).sql

# 恢复
docker exec -i campus-postgres psql -U campus campus_recruitment < backup_20260806.sql
```

---

## 费用总结

| 项目 | 费用 |
|------|------|
| 腾讯云轻量服务器 2核2G | 约 99-150 元/年（学生价） |
| 域名（可选） | 约 30-80 元/年 |
| HTTPS 证书 | 免费（Let's Encrypt） |
| 总计 | 约 100-230 元/年 |

---

## 简历加分项

部署完成后，你可以在简历中写：

- 基于 **Docker Compose** 编排全栈应用（FastAPI + Vue3 + PostgreSQL + Redis + Nginx）
- 部署于**腾讯云轻量服务器**，实现 7×24 小时稳定运行
- 使用 **Nginx 反向代理** 实现前后端统一入口，配置 HTTPS 加密传输
- 采用 **Docker 容器化** 部署，支持一键构建、快速扩容
- 应用 **PostgreSQL** 关系型数据库，设计用户/岗位/简历等多表关联模型
