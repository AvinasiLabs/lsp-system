#!/bin/bash
# 构建Docker镜像

echo "Building LSP System Docker image..."

# 构建镜像
docker build -t lsp-system:latest .

# 打标签（如果需要推送到仓库）
# docker tag lsp-system:latest your-registry/lsp-system:latest

echo "Build completed!"