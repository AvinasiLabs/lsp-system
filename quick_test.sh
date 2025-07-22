#!/bin/bash

echo "=== 快速诊断API问题 ==="
echo ""

# 测试服务器
SERVER="165.154.162.11:12002"

echo "1. 测试基础连接（5秒超时）："
curl -v --connect-timeout 5 --max-time 5 "http://$SERVER/lsp/health" 2>&1 | grep -E "Connected|HTTP|timeout|Failed"
echo ""

echo "2. 测试您的查询（10秒超时）："
curl -v --connect-timeout 10 --max-time 10 \
  "http://$SERVER/lsp/api/v1/scores/valid?user_id=550e8400-e29b-41d4-a716-446655440001" 2>&1
echo ""

echo "3. 简单的端口扫描："
nc -zv 165.154.162.11 12002 2>&1
echo ""

echo "如果以上命令都超时，可能的原因："
echo "1. 服务器未运行"
echo "2. 防火墙阻止了12002端口"
echo "3. 服务器正在处理请求但响应极慢"