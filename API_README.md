# LSP积分系统 API 使用指南

## 认证系统配置

LSP积分系统支持可选的认证系统，可以通过配置开关来启用或禁用。

### 配置认证系统

在 `.env` 文件中设置：

```bash
# 认证系统开关
API_AUTH_ENABLED=false  # false: 禁用认证（默认）, true: 启用认证

# JWT配置（仅在认证启用时使用）
API_JWT_SECRET_KEY=your-secret-key-here
API_JWT_ALGORITHM=HS256
API_JWT_EXPIRE_MINUTES=1440  # 24小时
```

### 认证模式差异

#### 禁用认证（默认）
- 所有API端点直接可访问
- 通过 `user_id` 查询参数指定用户
- 适合开发和测试环境

#### 启用认证
- 需要JWT令牌访问API
- 从令牌中自动获取用户身份
- 适合生产环境

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动API服务器

```bash
python start_server.py
```

服务器将在 `http://localhost:8000` 启动

### 3. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API端点

### 健康检查
```bash
GET /health
```

### 健康数据汇总
```bash
GET /api/v1/health/daily-summary?user_id=user_001&date=2025-07-08
```

### 计算每日积分
```bash
GET /api/v1/score/daily?user_id=user_001&date=2025-07-08
```

### 计算日期范围积分
```bash
GET /api/v1/score/range?user_id=user_001&start_date=2025-07-03&end_date=2025-07-09
```

### 获取可用维度
```bash
GET /api/v1/score/available-dimensions?user_id=user_001
```

## 测试API

运行测试脚本验证多用户功能：

```bash
python scripts/test_api_endpoints.py
```

## 环境变量

可以通过环境变量配置服务器：

- `API_HOST`: 服务器主机（默认: 0.0.0.0）
- `API_PORT`: 服务器端口（默认: 8000）
- `API_RELOAD`: 自动重载（默认: true）

例如：
```bash
API_PORT=8080 python start_server.py
```

## 多用户支持

所有API端点都支持 `user_id` 参数，用于隔离不同用户的数据：

- 默认用户ID: `default_user`
- 测试用户: `user_001`, `user_002`, `user_003` 等

## 认证系统使用

### 检查认证状态

```bash
curl http://localhost:8000/api/v1/auth/status
```

### 禁用认证时的请求

```bash
# 直接使用user_id参数
curl "http://localhost:8000/api/v1/score/daily?user_id=user_001&date=2025-07-08"
```

### 启用认证时的请求

1. 获取访问令牌（演示用）：
```bash
curl -X POST http://localhost:8000/api/v1/auth/demo-token/user_001
```

2. 使用令牌访问API：
```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     "http://localhost:8000/api/v1/score/daily?date=2025-07-08"
```

## 示例请求

### 使用 curl

```bash
# 获取用户健康数据
curl "http://localhost:8000/api/v1/health/daily-summary?user_id=user_001&date=2025-07-08"

# 计算用户积分
curl "http://localhost:8000/api/v1/score/daily?user_id=user_001&date=2025-07-08"
```

### 使用 Python

```python
import requests

# 获取健康数据
response = requests.get(
    "http://localhost:8000/api/v1/health/daily-summary",
    params={"user_id": "user_001", "date": "2025-07-08"}
)
print(response.json())

# 计算积分
response = requests.get(
    "http://localhost:8000/api/v1/score/daily",
    params={"user_id": "user_001", "date": "2025-07-08"}
)
print(response.json())
```

## 注意事项

1. 确保PostgreSQL数据库正在运行
2. 确保 `.env` 文件中配置了正确的数据库连接信息
3. 首次使用前需要运行数据库迁移脚本添加用户支持：
   ```bash
   python scripts/add_user_id_migration.py
   ```