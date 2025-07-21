#!/bin/bash
# 测试Docker设置脚本

echo "=== Docker部署测试脚本 ==="
echo

# 检查Docker是否安装
echo "1. 检查Docker安装..."
if command -v docker &> /dev/null; then
    echo "✅ Docker已安装"
    docker --version
else
    echo "❌ Docker未安装"
    echo "请先安装Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo

# 检查Docker Compose
echo "2. 检查Docker Compose..."
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose已安装"
    docker-compose --version
else
    echo "⚠️  使用docker compose (内置版本)"
fi

echo

# 检查Docker守护进程
echo "3. 检查Docker守护进程..."
if docker info &> /dev/null; then
    echo "✅ Docker守护进程正在运行"
else
    echo "❌ Docker守护进程未运行"
    echo "请启动Docker Desktop应用程序"
    exit 1
fi

echo

# 显示项目文件
echo "4. Docker相关文件:"
echo "✅ Dockerfile" && ls -la Dockerfile
echo "✅ docker-compose.yml" && ls -la docker-compose.yml
echo "✅ .dockerignore" && ls -la .dockerignore

echo
echo "=== 环境准备完成 ==="
echo
echo "下一步操作："
echo "1. 复制环境变量文件: cp .env.example .env"
echo "2. 编辑.env文件，配置数据库连接"
echo "3. 构建镜像: docker-compose build"
echo "4. 启动服务: docker-compose up -d"