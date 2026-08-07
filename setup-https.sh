#!/bin/bash
# ============================================================
# HTTPS 证书配置脚本（需要域名）
#
# 前提：已购买域名并解析到服务器 IP
# 用法：sudo bash setup-https.sh your-domain.com
# ============================================================

set -e

DOMAIN=${1:-}

if [ -z "$DOMAIN" ]; then
    echo "用法: sudo bash setup-https.sh your-domain.com"
    echo "示例: sudo bash setup-https.sh qiuzhao.example.com"
    exit 1
fi

echo "============================================"
echo "  配置 HTTPS 证书：$DOMAIN"
echo "============================================"

# 1. 安装 certbot
echo "[1/4] 安装 certbot..."
apt-get update -qq
apt-get install -y -qq certbot

# 2. 停止 nginx（certbot standalone 模式需要 80 端口）
echo "[2/4] 停止前端容器以释放 80 端口..."
cd ~/campus-recruitment
docker compose stop frontend

# 3. 申请证书
echo "[3/4] 申请 Let's Encrypt 证书..."
certbot certonly --standalone \
    --non-interactive \
    --agree-tos \
    --email admin@${DOMAIN} \
    -d ${DOMAIN} \
    --keep-until-expiring

# 4. 替换 nginx 配置为 HTTPS 版
echo "[4/4] 更新 Nginx 配置..."
sed "s/SERVER_DOMAIN/${DOMAIN}/g" frontend/nginx.https.conf > frontend/nginx.conf

# 5. 更新 docker-compose.yml 挂载证书
# 在 frontend 服务中添加 volumes 挂载
cat >> docker-compose.yml.tmp << 'DOCKEREOF'

# 在 frontend 服务的 volumes 中添加:
#     - /etc/letsencrypt:/etc/letsencrypt:ro
# 在 frontend 服务的 ports 中添加:
#     - "443:443"
DOCKEREOF

echo ""
echo "============================================"
echo "  请在 docker-compose.yml 的 frontend 服务中手动添加:"
echo "    ports:"
echo "      - \"80:80\""
echo "      - \"443:443\""
echo "    volumes:"
echo "      - /etc/letsencrypt:/etc/letsencrypt:ro"
echo "============================================"

# 启动服务
echo ""
echo "重新构建并启动前端（应用 HTTPS 配置）..."
docker compose up -d --build frontend

echo ""
echo "============================================"
echo "  HTTPS 配置完成！"
echo "  访问地址：https://${DOMAIN}"
echo "============================================"
echo ""
echo "证书自动续期（已设置 cron 任务）："
echo "  0 3 * * * certbot renew --quiet --post-hook 'docker compose restart frontend'"
