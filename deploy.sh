#!/bin/bash
# 部署脚本

# 检查环境变量文件
if [ ! -f .env.prod ]; then
    echo "Error: .env.prod file not found!"
    echo "Please create .env.prod from .env.example"
    exit 1
fi

# 加载环境变量
source .env.prod

echo "Deploying LSP System..."

# 停止旧容器
docker-compose -f docker-compose.prod.yml down

# 构建最新镜像
./build.sh

# 启动新容器
docker-compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo "Waiting for service to start..."
sleep 5

# 检查健康状态
echo "Checking health status..."
curl -f http://localhost:8000/health || echo "Health check failed!"

echo "Deployment completed!"

# 显示容器状态
docker ps | grep lsp_app