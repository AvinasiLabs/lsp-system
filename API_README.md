# LSP 积分系统 REST API 文档

## 目录
- [概述](#概述)
- [认证](#认证)
- [错误处理](#错误处理)
- [API 接口](#api-接口)
  - [系统状态](#系统状态)
  - [认证管理](#认证管理)
  - [健康数据](#健康数据)
  - [积分计算](#积分计算)
  - [积分查询](#积分查询)

---

## 概述

### 基础信息
- **基础 URL**: `http://localhost:8000/lsp`
- **API 版本**: v1
- **数据格式**: JSON
- **字符编码**: UTF-8

### 快速开始
```bash
# 健康检查
curl http://localhost:8000/lsp/health

# 查询积分（认证禁用时）
curl "http://localhost:8000/lsp/api/v1/scores/valid?user_id=user_001"
```

---

## 认证

系统支持两种认证模式，通过环境变量 `API_AUTH_ENABLED` 控制。

### 认证禁用模式（默认）
- 通过 URL 参数 `user_id` 指定用户
- 适合开发和测试环境

### 认证启用模式
- 需要在请求头中包含 JWT token
- 格式：`Authorization: Bearer <token>`
- 适合生产环境

---

## 错误处理

### HTTP 状态码
| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（认证失败） |
| 404 | 资源不存在 |
| 422 | 参数验证失败 |
| 500 | 服务器内部错误 |

### 错误响应格式
```json
{
  "detail": "错误描述信息"
}
```

---

## API 接口

## 系统状态

### 1. 系统信息
获取系统基本信息和版本。

**请求**
```http
GET /lsp HTTP/1.1
Host: localhost:8000
```

**响应**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "message": "欢迎使用LSP积分系统",
  "version": "1.0.0",
  "docs": "/lsp/docs",
  "redoc": "/lsp/redoc",
  "auth_enabled": false
}
```

**响应字段说明**
| 字段 | 类型 | 说明 |
|------|------|------|
| message | string | 欢迎信息 |
| version | string | API 版本 |
| docs | string | Swagger 文档路径 |
| redoc | string | ReDoc 文档路径 |
| auth_enabled | boolean | 认证系统是否启用 |

---

### 2. 健康检查
检查系统和数据库状态。

**请求**
```http
GET /lsp/health HTTP/1.1
Host: localhost:8000
```

**响应**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "services": {
    "api": "healthy",
    "database": "healthy"
  }
}
```

**响应字段说明**
| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 总体状态: healthy/degraded |
| services | object | 各服务状态 |
| services.api | string | API 服务状态 |
| services.database | string | 数据库状态 |

---

## 认证管理

### 3. 认证状态
查询认证系统是否启用。

**请求**
```http
GET /lsp/api/v1/auth/status HTTP/1.1
Host: localhost:8000
```

**响应**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "auth_enabled": false,
  "message": "认证系统已禁用，可直接使用API，通过user_id参数指定用户"
}
```

---

### 4. 用户登录
获取访问令牌（仅在认证启用时可用）。

**请求**
```http
POST /lsp/api/v1/auth/login HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "user_id": "user_001",
  "password": "password123"
}
```

**请求参数**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户 ID |
| password | string | 是 | 用户密码 |

**响应（成功）**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_id": "user_001"
}
```

**响应（认证禁用）**
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "detail": "认证系统未启用"
}
```

---

### 5. 演示令牌
快速生成测试用令牌（仅用于开发环境）。

**请求**
```http
POST /lsp/api/v1/auth/demo-token/{user_id} HTTP/1.1
Host: localhost:8000
```

**路径参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户 ID |

**响应**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_id": "user_001"
}
```

---

## 健康数据

### 6. 每日健康数据汇总
获取指定日期的健康数据汇总。

**请求**
```http
GET /lsp/api/v1/health/daily-summary?user_id=user_001&date=2025-07-08 HTTP/1.1
Host: localhost:8000
```

**查询参数**
| 参数 | 类型 | 必需 | 说明 | 默认值 |
|------|------|------|------|--------|
| user_id | string | 是* | 用户 ID | default_user |
| date | string | 否 | 日期 (YYYY-MM-DD) | 今天 |

*注：认证启用时从 token 获取，无需传递

**响应**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "date": "2025-07-08",
  "sleep_hours": 8.0,
  "steps": 10952,
  "active_energy": 781.054,
  "exercise_minutes": 69,
  "stand_hours": 5,
  "avg_heart_rate": 90.6,
  "resting_heart_rate": 51.0,
  "hrv": null,
  "water_ml": 250.0
}
```

**响应字段说明**
| 字段 | 类型 | 说明 | 单位 |
|------|------|------|------|
| date | string | 日期 | - |
| sleep_hours | float/null | 睡眠时长 | 小时 |
| steps | integer/null | 步数 | 步 |
| active_energy | float/null | 活动能量 | 卡路里 |
| exercise_minutes | integer/null | 运动时长 | 分钟 |
| stand_hours | integer/null | 站立小时数 | 小时 |
| avg_heart_rate | float/null | 平均心率 | bpm |
| resting_heart_rate | float/null | 静息心率 | bpm |
| hrv | float/null | 心率变异性 | ms |
| water_ml | float/null | 饮水量 | 毫升 |

---

## 积分计算

### 7. 计算每日积分
计算指定日期的积分。

**请求**
```http
GET /lsp/api/v1/score/daily?user_id=user_001&date=2025-07-08 HTTP/1.1
Host: localhost:8000
```

**查询参数**
| 参数 | 类型 | 必需 | 说明 | 默认值 |
|------|------|------|------|--------|
| user_id | string | 是* | 用户 ID | default_user |
| date | string | 否 | 日期 (YYYY-MM-DD) | 今天 |

**响应**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "user_id": "user_001",
  "date": "2025-07-08T00:00:00",
  "health_summary": {
    "date": "2025-07-08T00:00:00",
    "sleep_hours": 8.0,
    "steps": 10952,
    "active_energy": 781.054,
    "exercise_minutes": 69,
    "stand_hours": 5,
    "avg_heart_rate": 90.6,
    "resting_heart_rate": 51.0,
    "hrv": null,
    "water_ml": 250.0
  },
  "dimension_scores": {
    "sleep": {
      "easy": 1000,
      "medium": 0,
      "hard": 0,
      "super_hard": 0,
      "total": 1000
    },
    "exercise": {
      "easy": 947,
      "medium": 1600,
      "hard": 0,
      "super_hard": 0,
      "total": 2547
    },
    "diet": {
      "easy": 200,
      "medium": 0,
      "hard": 0,
      "super_hard": 0,
      "total": 200
    },
    "mental": {
      "easy": 0,
      "medium": 0,
      "hard": 0,
      "super_hard": 0,
      "total": 0
    }
  },
  "total_score": 3747,
  "user_level": "Bronze",
  "timestamp": "2025-07-22T18:31:06.772554"
}
```

**响应字段说明**
| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户 ID |
| date | string | 计算日期 |
| health_summary | object | 健康数据汇总 |
| dimension_scores | object | 各维度积分明细 |
| total_score | integer | 总积分 |
| user_level | string | 用户等级 |
| timestamp | string | 计算时间戳 |

**维度积分说明**
| 难度 | 倍数 | 说明 |
|------|------|------|
| easy | 1x | 简单任务 |
| medium | 2x | 中等任务 |
| hard | 3x | 困难任务 |
| super_hard | 4x | 超难任务 |

---

### 8. 计算日期范围积分
批量计算指定日期范围内的积分。

**请求**
```http
GET /lsp/api/v1/score/range?user_id=user_001&start_date=2025-07-05&end_date=2025-07-08 HTTP/1.1
Host: localhost:8000
```

**查询参数**
| 参数 | 类型 | 必需 | 说明 | 限制 |
|------|------|------|------|------|
| user_id | string | 是* | 用户 ID | - |
| start_date | string | 是 | 开始日期 (YYYY-MM-DD) | - |
| end_date | string | 是 | 结束日期 (YYYY-MM-DD) | 最多90天 |

**响应**
```http
HTTP/1.1 200 OK
Content-Type: application/json

[
  {
    "user_id": "user_001",
    "date": "2025-07-05T00:00:00",
    "health_summary": {...},
    "dimension_scores": {...},
    "total_score": 3200,
    "user_level": "Bronze",
    "timestamp": "2025-07-22T18:31:06.772554"
  },
  {
    "user_id": "user_001",
    "date": "2025-07-06T00:00:00",
    "health_summary": {...},
    "dimension_scores": {...},
    "total_score": 3500,
    "user_level": "Bronze",
    "timestamp": "2025-07-22T18:31:06.772554"
  }
]
```

**错误响应（范围超限）**
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "detail": "查询范围不能超过90天"
}
```

---

### 9. 获取可用积分维度
查询系统支持的积分维度。

**请求**
```http
GET /lsp/api/v1/score/available-dimensions?user_id=user_001 HTTP/1.1
Host: localhost:8000
```

**响应**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "dimensions": {
    "sleep": true,
    "exercise": true,
    "diet": true,
    "mental": true,
    "environment": false,
    "social": false,
    "cognition": false,
    "prevention": false
  },
  "message": "基于当前HealthKit数据的可用维度"
}
```

---

## 积分查询

### 10. 查询有效积分
获取用户当前有效积分总额。

**请求**
```http
GET /lsp/api/v1/scores/valid?user_id=user_001&as_of_date=2025-07-22 HTTP/1.1
Host: localhost:8000
```

**查询参数**
| 参数 | 类型 | 必需 | 说明 | 默认值 |
|------|------|------|------|--------|
| user_id | string | 是* | 用户 ID | default_user |
| as_of_date | string | 否 | 计算日期 (YYYY-MM-DD) | 今天 |

**响应（有积分）**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "user_id": "user_001",
  "total_valid_score": 32559,
  "dimension_scores": {
    "sleep": 7000,
    "exercise": 16859,
    "diet": 2700,
    "mental": 6000
  },
  "as_of_date": "2025-07-22T18:28:39.468295",
  "record_count": 25
}
```

**响应（无积分）**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "user_id": "new_user",
  "total_valid_score": 0,
  "dimension_scores": {},
  "as_of_date": "2025-07-22T18:28:39.468295",
  "record_count": 0
}
```

---

### 11. 查询积分历史
获取指定日期范围内的积分历史记录。

**请求**
```http
GET /lsp/api/v1/scores/history?user_id=user_001&start_date=2025-07-01&end_date=2025-07-31&include_expired=false HTTP/1.1
Host: localhost:8000
```

**查询参数**
| 参数 | 类型 | 必需 | 说明 | 默认值 |
|------|------|------|------|--------|
| user_id | string | 是* | 用户 ID | default_user |
| start_date | string | 是 | 开始日期 (YYYY-MM-DD) | - |
| end_date | string | 是 | 结束日期 (YYYY-MM-DD) | - |
| include_expired | boolean | 否 | 是否包含过期积分 | false |

**响应**
```http
HTTP/1.1 200 OK
Content-Type: application/json

[
  {
    "id": 123,
    "date": "2025-07-08",
    "dimension": "sleep",
    "sub_category": "duration",
    "difficulty": "easy",
    "score": 1000,
    "expire_date": "2026-01-08",
    "is_expired": false,
    "tier_level": "Bronze",
    "details": {
      "sleep_hours": 8.0
    },
    "created_at": "2025-07-08T12:00:00"
  }
]
```

**响应字段说明**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 记录 ID |
| date | string | 积分日期 |
| dimension | string | 积分维度 |
| sub_category | string/null | 子类别 |
| difficulty | string | 难度等级 |
| score | integer | 积分值 |
| expire_date | string/null | 过期日期 |
| is_expired | boolean | 是否已过期 |
| tier_level | string | 用户等级 |
| details | object | 详细信息 |
| created_at | string | 创建时间 |

---

### 12. 查询即将过期积分
查询未来N天内将要过期的积分。

**请求**
```http
GET /lsp/api/v1/scores/expiring?user_id=user_001&days_ahead=30 HTTP/1.1
Host: localhost:8000
```

**查询参数**
| 参数 | 类型 | 必需 | 说明 | 范围 |
|------|------|------|------|------|
| user_id | string | 是* | 用户 ID | - |
| days_ahead | integer | 否 | 查询天数 | 1-180 |

**响应**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "user_id": "user_001",
  "days_ahead": 30,
  "total_expiring_score": 5000,
  "expiring_by_date": [
    {
      "date": "2025-08-15",
      "scores": [
        {
          "dimension": "sleep",
          "score": 1000,
          "earned_date": "2025-02-15"
        },
        {
          "dimension": "exercise",
          "score": 2000,
          "earned_date": "2025-02-15"
        }
      ]
    }
  ]
}
```

---

### 13. 获取用户等级统计
获取用户等级和积分统计信息。

**请求**
```http
GET /lsp/api/v1/scores/tier-stats?user_id=user_001 HTTP/1.1
Host: localhost:8000
```

**响应**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "user_id": "user_001",
  "current_tier": "Bronze",
  "total_earned_score": 50000,
  "total_valid_score": 32559,
  "expiration_months": 6
}
```

**等级说明**
| 等级 | 过期时间 | 说明 |
|------|----------|------|
| Bronze | 6个月 | 铜牌会员 |
| Silver | 8个月 | 银牌会员 |
| Gold | 12个月 | 金牌会员 |
| Platinum | 永不过期 | 铂金会员 |

---

### 14. 获取月度汇总
按维度统计指定月份的积分情况。

**请求**
```http
GET /lsp/api/v1/scores/summary/2025/7?user_id=user_001 HTTP/1.1
Host: localhost:8000
```

**路径参数**
| 参数 | 类型 | 说明 | 范围 |
|------|------|------|------|
| year | integer | 年份 | 2020-2030 |
| month | integer | 月份 | 1-12 |

**响应**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "user_id": "user_001",
  "year": 2025,
  "month": 7,
  "total_score": 25000,
  "active_days": 22,
  "dimension_summary": {
    "sleep": {
      "total": 7000,
      "by_difficulty": {
        "easy": 5000,
        "medium": 2000,
        "hard": 0,
        "super_hard": 0
      }
    },
    "exercise": {
      "total": 15000,
      "by_difficulty": {
        "easy": 5000,
        "medium": 8000,
        "hard": 2000,
        "super_hard": 0
      }
    }
  }
}
```

---

### 15. 检查并标记过期积分
定期维护任务，检查并标记所有用户的过期积分。

**请求**
```http
POST /lsp/api/v1/scores/check-expiration HTTP/1.1
Host: localhost:8000
```

**响应**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "checked_count": 1250,
  "expired_count": 48,
  "message": "检查了1250条记录，标记了48条为过期"
}
```

**注意**: 此接口应该通过定时任务调用，建议每天执行一次。

---

## 使用示例

### cURL 示例

#### 基础查询
```bash
# 查询有效积分
curl "http://localhost:8000/lsp/api/v1/scores/valid?user_id=user_001"

# 获取健康数据
curl "http://localhost:8000/lsp/api/v1/health/daily-summary?user_id=user_001&date=2025-07-08"

# 计算积分
curl "http://localhost:8000/lsp/api/v1/score/daily?user_id=user_001&date=2025-07-08"
```

#### 认证模式
```bash
# 获取令牌
TOKEN=$(curl -s -X POST http://localhost:8000/lsp/api/v1/auth/demo-token/user_001 | jq -r '.access_token')

# 使用令牌调用
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/lsp/api/v1/scores/valid"
```

### Python 示例

```python
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000/lsp"

# 查询有效积分
def get_valid_scores(user_id):
    response = requests.get(
        f"{BASE_URL}/api/v1/scores/valid",
        params={"user_id": user_id}
    )
    return response.json()

# 计算每日积分
def calculate_daily_score(user_id, date):
    response = requests.get(
        f"{BASE_URL}/api/v1/score/daily",
        params={
            "user_id": user_id,
            "date": date
        }
    )
    return response.json()

# 使用示例
if __name__ == "__main__":
    user_id = "user_001"
    
    # 查询有效积分
    valid_scores = get_valid_scores(user_id)
    print(f"有效积分: {valid_scores['total_valid_score']}")
    
    # 计算今日积分
    today = datetime.now().strftime("%Y-%m-%d")
    daily_score = calculate_daily_score(user_id, today)
    print(f"今日积分: {daily_score.get('total_score', 0)}")
```

### JavaScript 示例

```javascript
const BASE_URL = 'http://localhost:8000/lsp';

// 查询有效积分
async function getValidScores(userId) {
    const response = await fetch(
        `${BASE_URL}/api/v1/scores/valid?user_id=${userId}`
    );
    return response.json();
}

// 计算每日积分
async function calculateDailyScore(userId, date) {
    const params = new URLSearchParams({
        user_id: userId,
        date: date
    });
    
    const response = await fetch(
        `${BASE_URL}/api/v1/score/daily?${params}`
    );
    return response.json();
}

// 使用示例
(async () => {
    const userId = 'user_001';
    
    try {
        // 查询有效积分
        const validScores = await getValidScores(userId);
        console.log(`有效积分: ${validScores.total_valid_score}`);
        
        // 计算今日积分
        const today = new Date().toISOString().split('T')[0];
        const dailyScore = await calculateDailyScore(userId, today);
        console.log(`今日积分: ${dailyScore.total_score || 0}`);
    } catch (error) {
        console.error('API调用失败:', error);
    }
})();
```

---

## 附录

### 数据类型说明

| 类型 | 说明 | 示例 |
|------|------|------|
| string | 字符串 | "user_001" |
| integer | 整数 | 1000 |
| float | 浮点数 | 8.5 |
| boolean | 布尔值 | true/false |
| object | 对象 | {...} |
| array | 数组 | [...] |
| null | 空值 | null |

### 日期格式

- 日期：`YYYY-MM-DD` (例: 2025-07-08)
- 时间戳：ISO 8601 格式 (例: 2025-07-08T12:00:00)

### 分页

目前 API 不支持分页，但以下接口在未来版本可能添加分页支持：
- 积分历史查询
- 月度汇总查询

### 限流

目前无限流策略，建议客户端实现合理的请求频率控制。

### 版本控制

API 版本通过 URL 路径控制：`/api/v1/`

未来版本将保持向后兼容，或提供版本迁移指南。