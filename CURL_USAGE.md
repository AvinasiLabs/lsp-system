# 正确使用 curl 调用 API

## 问题说明

当使用 curl 调用带查询参数的 URL 时，必须用引号包裹整个 URL，否则 shell 会错误解释特殊字符。

## 错误示例 ❌
```bash
curl http://165.154.162.11:12002/lsp/api/v1/scores/valid?user_id=550e8400-e29b-41d4-a716-446655440001
```
问题：`?` 和 `&` 等字符会被 shell 特殊处理，导致请求失败。

## 正确示例 ✅

### 方法1：使用双引号
```bash
curl "http://165.154.162.11:12002/lsp/api/v1/scores/valid?user_id=550e8400-e29b-41d4-a716-446655440001"
```

### 方法2：使用单引号
```bash
curl 'http://165.154.162.11:12002/lsp/api/v1/scores/valid?user_id=550e8400-e29b-41d4-a716-446655440001'
```

### 方法3：使用 -G 和 --data-urlencode
```bash
curl -G http://165.154.162.11:12002/lsp/api/v1/scores/valid \
     --data-urlencode "user_id=550e8400-e29b-41d4-a716-446655440001"
```

## 实用示例

### 查询有效积分
```bash
curl -s "http://165.154.162.11:12002/lsp/api/v1/scores/valid?user_id=550e8400-e29b-41d4-a716-446655440001" | python -m json.tool
```

### 获取健康数据
```bash
curl -s "http://165.154.162.11:12002/lsp/api/v1/health/daily-summary?user_id=550e8400-e29b-41d4-a716-446655440001&date=2025-07-22" | python -m json.tool
```

### 计算每日积分
```bash
curl -s "http://165.154.162.11:12002/lsp/api/v1/score/daily?user_id=550e8400-e29b-41d4-a716-446655440001&date=2025-07-22" | python -m json.tool
```

### 调试模式（显示请求详情）
```bash
curl -v "http://165.154.162.11:12002/lsp/api/v1/scores/valid?user_id=550e8400-e29b-41d4-a716-446655440001"
```

## 注意事项

1. **始终使用引号**：当 URL 包含 `?`、`&`、`=` 等特殊字符时
2. **使用 -s 参数**：静默模式，不显示进度条
3. **使用管道格式化**：`| python -m json.tool` 可以美化 JSON 输出
4. **使用 -v 调试**：查看请求和响应的详细信息