#!/bin/bash

echo "=== 诊断远程API连接问题 ==="
echo ""

SERVER="165.154.162.11"
PORT="12002"
API_URL="http://$SERVER:$PORT"

echo "1. 测试网络连通性（ping）："
ping -c 3 $SERVER
echo ""

echo "2. 测试端口连通性（telnet）："
echo "尝试连接 $SERVER:$PORT ..."
(echo -e "GET /lsp/health HTTP/1.0\r\n\r\n"; sleep 2) | telnet $SERVER $PORT 2>&1 | head -20
echo ""

echo "3. 使用curl测试（带超时设置）："
echo "3.1 健康检查接口（10秒超时）："
curl -v --connect-timeout 10 --max-time 10 "$API_URL/lsp/health" 2>&1
echo ""

echo "3.2 测试valid接口（10秒超时）："
curl -v --connect-timeout 10 --max-time 10 "$API_URL/lsp/api/v1/scores/valid?user_id=550e8400-e29b-41d4-a716-446655440001" 2>&1
echo ""

echo "4. 使用wget测试（如果curl失败）："
wget -O - --timeout=10 "$API_URL/lsp/health" 2>&1
echo ""

echo "5. 使用nc（netcat）测试端口："
echo "测试TCP连接..."
nc -zv $SERVER $PORT 2>&1
echo ""

echo "6. 测试不同的请求方式："
echo "6.1 只获取HTTP头信息："
curl -I --connect-timeout 5 "$API_URL/lsp/health"
echo ""

echo "6.2 使用HTTP/1.0："
curl --http1.0 --connect-timeout 5 "$API_URL/lsp/health"
echo ""

echo "7. 可能的问题原因："
echo "- 服务器未启动或崩溃"
echo "- 防火墙阻止了连接"
echo "- 服务器响应极慢（数据库查询问题）"
echo "- 网络连接问题"
echo "- 服务器配置错误"