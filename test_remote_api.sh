#!/bin/bash

echo "=== 测试远程API调用 ==="
echo ""

# 服务器地址
SERVER_URL="http://165.154.162.11:12002"
USER_ID="550e8400-e29b-41d4-a716-446655440001"

echo "1. 错误的方式（不加引号）："
echo "命令: curl $SERVER_URL/lsp/api/v1/scores/valid?user_id=$USER_ID"
echo "问题: URL中的?会被shell解释，导致参数丢失"
echo ""

echo "2. 正确的方式 - 方法一（使用引号）："
echo "命令: curl \"$SERVER_URL/lsp/api/v1/scores/valid?user_id=$USER_ID\""
curl -s "$SERVER_URL/lsp/api/v1/scores/valid?user_id=$USER_ID" | python -m json.tool
echo ""

echo "3. 正确的方式 - 方法二（使用单引号）："
echo "命令: curl '$SERVER_URL/lsp/api/v1/scores/valid?user_id=$USER_ID'"
curl -s "$SERVER_URL/lsp/api/v1/scores/valid?user_id=$USER_ID" | python -m json.tool
echo ""

echo "4. 正确的方式 - 方法三（使用-G和--data-urlencode）："
echo "命令: curl -G $SERVER_URL/lsp/api/v1/scores/valid --data-urlencode \"user_id=$USER_ID\""
curl -s -G "$SERVER_URL/lsp/api/v1/scores/valid" --data-urlencode "user_id=$USER_ID" | python -m json.tool
echo ""

echo "5. 测试其他接口："
echo ""

echo "5.1 健康检查："
curl -s "$SERVER_URL/lsp/health" | python -m json.tool
echo ""

echo "5.2 获取健康数据汇总："
curl -s "$SERVER_URL/lsp/api/v1/health/daily-summary?user_id=$USER_ID&date=2025-07-22" | python -m json.tool
echo ""

echo "5.3 计算每日积分："
curl -s "$SERVER_URL/lsp/api/v1/score/daily?user_id=$USER_ID&date=2025-07-22" | python -m json.tool
echo ""

echo "=== 带详细信息的调用（使用 -v 参数）==="
echo "命令: curl -v \"$SERVER_URL/lsp/api/v1/scores/valid?user_id=$USER_ID\""
curl -v "$SERVER_URL/lsp/api/v1/scores/valid?user_id=$USER_ID" 2>&1 | grep -E "^[<>]|HTTP"