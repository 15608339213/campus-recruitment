#!/bin/bash
# ============================================================
# 秋招助手 - 腾讯云一键部署脚本
#
# 使用方法（在服务器上执行）：
#   chmod +x deploy.sh && ./deploy.sh
#
# 前提条件：
#   - 已安装 Docker 和 Docker Compose
#   - 已 git clone 项目到服务器
# ============================================================

set -e

echo "============================================"
echo "  秋招助手 - 腾讯云部署脚本"
echo "============================================"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "[错误] Docker 未安装，正在安装..."
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
    echo "[完成] Docker 安装成功"
else
    echo "[1/5] Docker 已安装: $(docker --version)"
fi

# 检查 Docker Compose
if ! docker compose version &> /dev/null; then
    echo "[错误] Docker Compose 未安装"
    echo "请手动安装: https://docs.docker.com/compose/install/"
    exit 1
fi
echo "[2/5] Docker Compose: $(docker compose version)"

# 检查项目文件
if [ ! -f "docker-compose.yml" ]; then
    echo "[错误] 未找到 docker-compose.yml，请确保在项目根目录执行"
    exit 1
fi
echo "[3/5] 项目文件检查通过"

# 构建并启动服务
echo "[4/5] 正在构建和启动服务（首次约需 5-10 分钟）..."
docker compose up -d --build

# 等待服务启动
echo "[5/5] 等待服务启动..."
sleep 10

# 检查服务状态
echo ""
echo "============================================"
echo "  服务状态检查"
echo "============================================"
docker compose ps

# 获取服务器 IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ip.sb 2>/dev/null || echo "你的服务器IP")

echo ""
echo "============================================"
echo "  部署完成！"
echo "============================================"
echo ""
echo "  访问地址："
echo "    前端：  http://$SERVER_IP"
echo "    API文档：http://$SERVER_IP/api/v1/docs"
echo "    健康检查：http://$SERVER_IP/api/v1/health"
echo ""
echo "  管理员账号：admin@campus.com"
echo "  管理员密码：admin123"
echo ""
echo "  常用命令："
echo "    查看日志：docker compose logs -f"
echo "    重启服务：docker compose restart"
echo "    停止服务：docker compose down"
echo ""
echo "============================================"

# 健康检查
echo "正在检查后端健康状态..."
sleep 5
if curl -s http://localhost/api/v1/health | grep -q "ok"; then
    echo "[成功] 后端服务正常运行！"
else
    echo "[警告] 后端可能还在启动中，请稍等1分钟后访问"
    echo "       查看日志：docker compose logs -f backend"
fi
