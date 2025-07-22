# LSP积分系统 API 接口文档

## 概述

LSP积分系统是一个基于健康数据的长寿积分计算系统。系统通过分析用户的健康数据（如睡眠、运动、心率等），计算相应的积分奖励。

### 基础信息
- **基础URL**: `http://localhost:8000/lsp`
- **API版本**: v1
- **认证方式**: 可选的JWT认证（通过环境变量配置）

### API文档访问
- **Swagger UI**: http://localhost:8000/lsp/docs
- **ReDoc**: http://localhost:8000/lsp/redoc
- **OpenAPI JSON**: http://localhost:8000/lsp/openapi.json

## 认证说明

系统支持两种模式：

### 1. 禁用认证（默认）
- 直接通过URL参数 `user_id` 指定用户
- 适合开发和测试环境

### 2. 启用认证
- 需要JWT令牌访问API
- 在请求头中添加：`Authorization: Bearer YOUR_TOKEN`
- 适合生产环境

## API接口列表

### 1. 系统状态接口

#### 1.1 根路径
```
GET /lsp
```
**描述**: 获取系统基本信息  
**响应示例**:
```json
{
  "message": "欢迎使用LSP积分系统",
  "version": "1.0.0",
  "docs": "/lsp/docs",
  "redoc": "/lsp/redoc",
  "auth_enabled": false
}
```

#### 1.2 健康检查
```
GET /lsp/health
```
**描述**: 检查系统和数据库状态  
**响应示例**:
```json
{
  "status": "healthy",
  "services": {
    "api": "healthy",
    "database": "healthy"
  }
}
```

### 2. 认证接口

#### 2.1 认证状态
```
GET /lsp/api/v1/auth/status
```
**描述**: 获取认证系统状态  
**响应示例**:
```json
{
  "auth_enabled": false,
  "message": "认证系统已禁用，可直接使用API，通过user_id参数指定用户"
}
```

#### 2.2 用户登录
```
POST /lsp/api/v1/auth/login
```
**描述**: 用户登录获取访问令牌（认证启用时使用）  
**请求体**:
```json
{
  "user_id": "user_001",
  "password": "password123"
}
```
**响应示例**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_id": "user_001"
}
```

#### 2.3 演示令牌
```
POST /lsp/api/v1/auth/demo-token/{user_id}
```
**描述**: 创建演示用的访问令牌（仅测试环境）  
**路径参数**:
- `user_id`: 用户ID

### 3. 健康数据接口

#### 3.1 获取每日健康数据汇总
```
GET /lsp/api/v1/health/daily-summary
```
**描述**: 获取指定日期的健康数据汇总  
**查询参数**:
- `user_id` (string): 用户ID（认证禁用时必需）
- `date` (string, 可选): 查询日期，格式：YYYY-MM-DD，默认为今天

**响应示例**:
```json
{
  "date": "2025-07-08",
  "sleep_hours": 7.5,
  "steps": 8500,
  "active_energy": 450.5,
  "exercise_minutes": 45,
  "stand_hours": 10,
  "avg_heart_rate": 72.5,
  "resting_heart_rate": 58.0,
  "hrv": 45.2,
  "water_ml": 2000.0
}
```

### 4. 积分计算接口

#### 4.1 计算每日积分
```
GET /lsp/api/v1/score/daily
```
**描述**: 计算指定日期的积分  
**查询参数**:
- `user_id` (string): 用户ID（认证禁用时必需）
- `date` (string, 可选): 计算日期，格式：YYYY-MM-DD，默认为今天

**响应示例**:
```json
{
  "user_id": "user_001",
  "date": "2025-07-08",
  "health_summary": {
    "sleep_hours": 7.5,
    "steps": 8500,
    "active_energy": 450.5
  },
  "dimension_scores": {
    "sleep": {
      "base_score": 6,
      "difficulty_multiplier": 1,
      "difficulty": "easy",
      "details": {
        "sleep_duration": {
          "hours": 7.5,
          "score": 6,
          "optimal_range": "7-9小时"
        }
      }
    },
    "exercise": {
      "base_score": 12,
      "difficulty_multiplier": 2,
      "difficulty": "medium",
      "details": {
        "steps": {
          "count": 8500,
          "score": 8
        },
        "active_energy": {
          "calories": 450.5,
          "score": 4
        }
      }
    }
  },
  "total_score": 18,
  "user_level": "starter",
  "timestamp": "2025-07-22T10:30:00"
}
```

#### 4.2 计算日期范围积分
```
GET /lsp/api/v1/score/range
```
**描述**: 计算日期范围内的积分  
**查询参数**:
- `user_id` (string): 用户ID（认证禁用时必需）
- `start_date` (string, 必需): 开始日期，格式：YYYY-MM-DD
- `end_date` (string, 必需): 结束日期，格式：YYYY-MM-DD

**限制**: 查询范围不能超过90天

#### 4.3 获取可用积分维度
```
GET /lsp/api/v1/score/available-dimensions
```
**描述**: 获取基于当前数据的可用积分维度  
**查询参数**:
- `user_id` (string): 用户ID（认证禁用时必需）

**响应示例**:
```json
{
  "dimensions": ["sleep", "exercise", "mental"],
  "message": "基于当前HealthKit数据的可用维度"
}
```

### 5. 积分查询接口

#### 5.1 查询有效积分
```
GET /lsp/api/v1/scores/valid
```
**描述**: 获取用户当前有效积分总额  
**查询参数**:
- `user_id` (string): 用户ID（认证禁用时必需）
- `as_of_date` (string, 可选): 计算日期，格式：YYYY-MM-DD，默认为今天

**响应示例**:

*当用户有积分时:*
```json
{
  "user_id": "user_001",
  "total_valid_score": 156,
  "dimension_scores": {
    "sleep": 48,
    "exercise": 72,
    "mental": 36
  },
  "as_of_date": "2025-07-22",
  "record_count": 28
}
```

*当用户不存在或没有积分时:*
```json
{
  "user_id": "non_existent_user",
  "total_valid_score": 0,
  "dimension_scores": {},
  "as_of_date": "2025-07-22T18:03:53.278255",
  "record_count": 0
}
```

**特殊行为说明**:
- 当用户不存在时，不会报错，而是返回0积分
- 当user_id为空或未提供时，默认使用 `default_user`
- 支持特殊字符和超长的user_id，但建议使用标准格式（如 `user_001`）

#### 5.2 查询积分历史
```
GET /lsp/api/v1/scores/history
```
**描述**: 获取用户积分历史记录  
**查询参数**:
- `user_id` (string): 用户ID（认证禁用时必需）
- `start_date` (string, 必需): 开始日期，格式：YYYY-MM-DD
- `end_date` (string, 必需): 结束日期，格式：YYYY-MM-DD
- `include_expired` (boolean, 可选): 是否包含过期积分，默认false

**限制**: 查询范围不能超过365天

#### 5.3 查询即将过期积分
```
GET /lsp/api/v1/scores/expiring
```
**描述**: 获取即将过期的积分  
**查询参数**:
- `user_id` (string): 用户ID（认证禁用时必需）
- `days_ahead` (integer, 可选): 查询未来多少天内将过期的积分，默认30天，范围1-180

**响应示例**:
```json
{
  "user_id": "user_001",
  "days_ahead": 30,
  "total_expiring_score": 24,
  "expiring_by_date": [
    {
      "expire_date": "2025-08-15",
      "score": 12,
      "dimension": "sleep"
    },
    {
      "expire_date": "2025-08-20",
      "score": 12,
      "dimension": "exercise"
    }
  ]
}
```

#### 5.4 获取用户等级统计
```
GET /lsp/api/v1/scores/tier-stats
```
**描述**: 获取用户等级相关统计  
**查询参数**:
- `user_id` (string): 用户ID（认证禁用时必需）

**响应示例**:
```json
{
  "user_id": "user_001",
  "current_tier": "starter",
  "total_earned_score": 280,
  "total_valid_score": 156,
  "expiration_months": 6
}
```

#### 5.5 获取月度汇总
```
GET /lsp/api/v1/scores/summary/{year}/{month}
```
**描述**: 获取月度积分汇总  
**路径参数**:
- `year` (integer): 年份（2020-2030）
- `month` (integer): 月份（1-12）

**查询参数**:
- `user_id` (string): 用户ID（认证禁用时必需）

**响应示例**:
```json
{
  "user_id": "user_001",
  "year": 2025,
  "month": 7,
  "total_score": 156,
  "active_days": 22,
  "dimension_summary": {
    "sleep": {
      "total": 48,
      "by_difficulty": {
        "easy": 36,
        "medium": 12,
        "hard": 0,
        "super_hard": 0
      }
    },
    "exercise": {
      "total": 72,
      "by_difficulty": {
        "easy": 24,
        "medium": 36,
        "hard": 12,
        "super_hard": 0
      }
    }
  }
}
```

#### 5.6 检查并标记过期积分
```
POST /lsp/api/v1/scores/check-expiration
```
**描述**: 检查并标记过期的积分（管理员功能）  
**响应示例**:
```json
{
  "checked_count": 1250,
  "expired_count": 48,
  "message": "检查了1250条记录，标记了48条为过期"
}
```

## 调用示例

### 使用 cURL

#### 禁用认证时的调用
```bash
# 获取健康数据汇总
curl "http://localhost:8000/lsp/api/v1/health/daily-summary?user_id=user_001&date=2025-07-08"

# 计算每日积分
curl "http://localhost:8000/lsp/api/v1/score/daily?user_id=user_001&date=2025-07-08"

# 查询有效积分
curl "http://localhost:8000/lsp/api/v1/scores/valid?user_id=user_001"

# 查询积分历史
curl "http://localhost:8000/lsp/api/v1/scores/history?user_id=user_001&start_date=2025-07-01&end_date=2025-07-31"
```

#### 启用认证时的调用
```bash
# 1. 获取访问令牌
TOKEN=$(curl -X POST http://localhost:8000/lsp/api/v1/auth/demo-token/user_001 | jq -r '.access_token')

# 2. 使用令牌调用API
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/lsp/api/v1/score/daily?date=2025-07-08"
```

### 使用 Python

```python
import requests
import json

# 基础URL
BASE_URL = "http://localhost:8000/lsp"

# 禁用认证时的调用
def call_api_without_auth():
    # 获取健康数据
    response = requests.get(
        f"{BASE_URL}/api/v1/health/daily-summary",
        params={"user_id": "user_001", "date": "2025-07-08"}
    )
    print("健康数据:", json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # 计算积分
    response = requests.get(
        f"{BASE_URL}/api/v1/score/daily",
        params={"user_id": "user_001", "date": "2025-07-08"}
    )
    print("积分计算:", json.dumps(response.json(), indent=2, ensure_ascii=False))

# 启用认证时的调用
def call_api_with_auth():
    # 获取令牌
    token_response = requests.post(f"{BASE_URL}/api/v1/auth/demo-token/user_001")
    token = token_response.json()["access_token"]
    
    # 设置请求头
    headers = {"Authorization": f"Bearer {token}"}
    
    # 调用API
    response = requests.get(
        f"{BASE_URL}/api/v1/score/daily",
        params={"date": "2025-07-08"},
        headers=headers
    )
    print("积分计算:", json.dumps(response.json(), indent=2, ensure_ascii=False))

# 执行示例
call_api_without_auth()
```

### 使用 JavaScript (Node.js)

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000/lsp';

// 禁用认证时的调用
async function callApiWithoutAuth() {
    try {
        // 获取健康数据
        const healthResponse = await axios.get(`${BASE_URL}/api/v1/health/daily-summary`, {
            params: {
                user_id: 'user_001',
                date: '2025-07-08'
            }
        });
        console.log('健康数据:', healthResponse.data);
        
        // 计算积分
        const scoreResponse = await axios.get(`${BASE_URL}/api/v1/score/daily`, {
            params: {
                user_id: 'user_001',
                date: '2025-07-08'
            }
        });
        console.log('积分计算:', scoreResponse.data);
    } catch (error) {
        console.error('API调用失败:', error.message);
    }
}

// 启用认证时的调用
async function callApiWithAuth() {
    try {
        // 获取令牌
        const tokenResponse = await axios.post(`${BASE_URL}/api/v1/auth/demo-token/user_001`);
        const token = tokenResponse.data.access_token;
        
        // 调用API
        const scoreResponse = await axios.get(`${BASE_URL}/api/v1/score/daily`, {
            params: { date: '2025-07-08' },
            headers: { 'Authorization': `Bearer ${token}` }
        });
        console.log('积分计算:', scoreResponse.data);
    } catch (error) {
        console.error('API调用失败:', error.message);
    }
}

// 执行示例
callApiWithoutAuth();
```

## 错误处理

API使用标准HTTP状态码：

- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未授权（认证启用时）
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

错误响应格式：
```json
{
  "detail": "错误描述信息"
}
```

## 注意事项

1. **环境配置**: 确保正确配置 `.env` 文件，特别是数据库连接和认证相关配置
2. **数据库准备**: 首次使用前需要运行数据库初始化脚本
3. **认证模式**: 根据环境选择合适的认证模式（开发环境可禁用，生产环境建议启用）
4. **查询限制**: 注意API的查询范围限制，避免请求过大的数据范围
5. **积分过期**: 定期调用过期检查接口，确保积分状态准确

## 扩展说明

### 积分计算规则
- 积分基于健康数据的各个维度计算
- 包含难度系数：easy(1x), medium(2x), hard(3x), super_hard(4x)
- 积分有效期根据用户等级确定（6-24个月）

### 用户等级
- starter: 初始等级
- bronze: 铜牌会员
- silver: 银牌会员
- gold: 金牌会员
- platinum: 铂金会员

### 健康数据维度
- 睡眠(sleep): 睡眠时长、睡眠质量
- 运动(exercise): 步数、活动能量、运动时长
- 心理(mental): 站立时长、心率变异性
- 饮食(diet): 饮水量（如有数据）