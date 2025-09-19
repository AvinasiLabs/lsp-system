# LSP积分系统 - API接口文档

## 项目概述

LSP (Longevity Score Points) 系统是基于iOS HealthKit数据的健康积分计算系统，用于分析用户健康行为并计算长寿积分。

**服务地址**: http://localhost:12001
**API文档**: http://localhost:12001/lsp/docs
**ReDoc文档**: http://localhost:12001/lsp/redoc

## 项目结构

```
lsp-system/
├── src/                    # 源代码目录
│   ├── api/               # API接口层
│   ├── core/              # 核心业务逻辑
│   ├── services/          # 服务层
│   ├── models/            # 数据模型
│   ├── db/                # 数据库配置
│   └── utils/             # 工具类
├── scripts/               # 数据库脚本
├── data/                  # 数据文件
├── venv/                  # Python虚拟环境
├── requirements.txt       # 依赖包
├── start_server.py        # 服务启动脚本
├── .env                   # 环境配置
└── CLAUDE.md              # 项目说明
```

## 认证系统

当前认证系统 **已禁用**，可直接使用API。所有接口通过 `user_id` 参数指定用户。

如需启用认证，设置 `AUTH_ENABLED=true` 并使用JWT令牌认证。

---

## API接口清单

### 1. 系统接口

#### 1.1 根路径
- **路径**: `GET /lsp`
- **描述**: 获取系统基本信息
- **参数**: 无
- **响应**:
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
- **路径**: `GET /lsp/health`
- **描述**: 检查API和数据库连接状态
- **参数**: 无
- **响应**:
```json
{
  "status": "healthy",
  "services": {
    "api": "healthy",
    "database": "healthy"
  }
}
```

---

### 2. 认证接口 (`/lsp/api/v1/auth`)

#### 2.1 认证状态
- **路径**: `GET /lsp/api/v1/auth/status`
- **描述**: 获取认证系统状态
- **参数**: 无
- **响应**:
```json
{
  "auth_enabled": false,
  "message": "认证系统已禁用，可直接使用API，通过user_id参数指定用户"
}
```

#### 2.2 用户登录
- **路径**: `POST /lsp/api/v1/auth/login`
- **描述**: 用户登录获取访问令牌（仅在认证启用时）
- **请求体**:
```json
{
  "user_id": "string",
  "password": "string"
}
```
- **响应**:
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_id": "string"
}
```

#### 2.3 创建演示令牌
- **路径**: `POST /lsp/api/v1/auth/demo-token/{user_id}`
- **描述**: 创建演示用访问令牌（测试用）
- **参数**:
  - `user_id` (path): 用户ID
- **响应**: 同登录接口

---

### 3. 健康数据接口 (`/lsp/api/v1`)

#### 3.1 获取每日健康数据汇总
- **路径**: `GET /lsp/api/v1/health/daily-summary`
- **描述**: 获取指定日期的健康数据汇总
- **参数**:
  - `date` (query, 可选): 查询日期，默认今天，格式：YYYY-MM-DD
  - `user_id` (query): 用户ID（认证禁用时）
- **响应**:
```json
{
  "date": "2025-09-18",
  "sleep_hours": 7.5,
  "steps": 8000,
  "active_energy": 450.0,
  "exercise_minutes": 30,
  "stand_hours": 8,
  "avg_heart_rate": 75.0,
  "resting_heart_rate": 65.0,
  "hrv": 45.0,
  "water_ml": 2000.0
}
```

#### 3.2 计算每日积分
- **路径**: `GET /lsp/api/v1/score/daily`
- **描述**: 计算指定日期的健康积分
- **参数**:
  - `date` (query, 可选): 计算日期，默认今天
  - `user_id` (query): 用户ID
- **响应**:
```json
{
  "user_id": "user_001",
  "date": "2025-09-18",
  "health_summary": {
    "sleep_hours": 7.5,
    "steps": 8000,
    "active_energy": 450.0
  },
  "dimension_scores": {
    "sleep": {
      "easy": 10,
      "medium": 15,
      "hard": 20,
      "total": 45
    },
    "exercise": {
      "easy": 8,
      "medium": 12,
      "total": 20
    }
  },
  "total_score": 65,
  "user_level": "BRONZE",
  "timestamp": "2025-09-18T00:15:30Z"
}
```

#### 3.3 计算日期范围积分
- **路径**: `GET /lsp/api/v1/score/range`
- **描述**: 计算指定日期范围内的积分
- **参数**:
  - `start_date` (query, 必填): 开始日期
  - `end_date` (query, 必填): 结束日期
  - `user_id` (query): 用户ID
- **限制**: 查询范围不超过90天
- **响应**: 积分响应数组

#### 3.4 获取可用积分维度
- **路径**: `GET /lsp/api/v1/score/available-dimensions`
- **描述**: 获取基于当前用户HealthKit数据的可用积分维度
- **参数**:
  - `user_id` (query): 用户ID
- **响应**:
```json
{
  "dimensions": ["sleep", "exercise", "diet", "mental"],
  "message": "基于当前HealthKit数据的可用维度"
}
```

---

### 4. 积分查询接口 (`/lsp/api/v1/scores`)

#### 4.1 获取有效积分
- **路径**: `GET /lsp/api/v1/scores/valid`
- **描述**: 获取用户当前有效积分总额
- **参数**:
  - `as_of_date` (query, 可选): 计算日期，默认今天
  - `user_id` (query): 用户ID
- **响应**:
```json
{
  "user_id": "user_001",
  "total_valid_score": 1250,
  "dimension_scores": {
    "sleep": 500,
    "exercise": 400,
    "diet": 200,
    "mental": 150
  },
  "dimension_percentages": {
    "sleep": {
      "easy": 75.0,
      "medium": 60.0,
      "hard": 45.0,
      "total": 62.5
    }
  },
  "as_of_date": "2025-09-18",
  "record_count": 45
}
```

#### 4.2 获取积分历史
- **路径**: `GET /lsp/api/v1/scores/history`
- **描述**: 获取用户积分历史记录
- **参数**:
  - `start_date` (query, 必填): 开始日期
  - `end_date` (query, 必填): 结束日期
  - `include_expired` (query, 可选): 是否包含过期积分，默认false
  - `user_id` (query): 用户ID
- **限制**: 查询范围不超过365天
- **响应**:
```json
[
  {
    "id": 123,
    "date": "2025-09-18",
    "dimension": "sleep",
    "sub_category": "duration",
    "difficulty": "medium",
    "score": 15,
    "expire_date": "2026-03-18",
    "is_expired": false,
    "tier_level": "BRONZE",
    "details": {
      "sleep_hours": 7.5,
      "sleep_quality": "good"
    },
    "created_at": "2025-09-18T00:15:30Z"
  }
]
```

#### 4.3 获取即将过期积分
- **路径**: `GET /lsp/api/v1/scores/expiring`
- **描述**: 获取未来N天内将要过期的积分
- **参数**:
  - `days_ahead` (query, 可选): 查询天数，默认30，范围1-180
  - `user_id` (query): 用户ID
- **响应**:
```json
{
  "user_id": "user_001",
  "days_ahead": 30,
  "total_expiring_score": 200,
  "expiring_by_date": [
    {
      "expire_date": "2025-10-18",
      "score": 50,
      "count": 3
    },
    {
      "expire_date": "2025-10-25",
      "score": 150,
      "count": 8
    }
  ]
}
```

#### 4.4 获取等级统计
- **路径**: `GET /lsp/api/v1/scores/tier-stats`
- **描述**: 获取用户等级相关统计信息
- **参数**:
  - `user_id` (query): 用户ID
- **响应**:
```json
{
  "user_id": "user_001",
  "current_tier": "BRONZE",
  "total_earned_score": 2500,
  "total_valid_score": 1250,
  "expiration_months": 6
}
```

#### 4.5 检查过期积分
- **路径**: `POST /lsp/api/v1/scores/check-expiration`
- **描述**: 检查并标记过期的积分（管理员功能）
- **参数**: 无
- **响应**:
```json
{
  "checked_count": 1000,
  "expired_count": 25,
  "message": "检查了1000条记录，标记了25条为过期"
}
```

#### 4.6 获取月度汇总
- **路径**: `GET /lsp/api/v1/scores/summary/{year}/{month}`
- **描述**: 获取指定月份的积分汇总统计
- **参数**:
  - `year` (path): 年份，范围2020-2030
  - `month` (path): 月份，范围1-12
  - `user_id` (query): 用户ID
- **响应**:
```json
{
  "user_id": "user_001",
  "year": 2025,
  "month": 9,
  "total_score": 650,
  "active_days": 28,
  "dimension_summary": {
    "sleep": {
      "total": 280,
      "by_difficulty": {
        "easy": 100,
        "medium": 120,
        "hard": 60,
        "super_hard": 0
      }
    },
    "exercise": {
      "total": 200,
      "by_difficulty": {
        "easy": 80,
        "medium": 90,
        "hard": 30,
        "super_hard": 0
      }
    }
  },
  "dimension_percentages": {
    "sleep": {
      "total": 70.0,
      "by_difficulty": {
        "easy": 100.0,
        "medium": 80.0,
        "hard": 40.0,
        "super_hard": 0.0
      }
    }
  }
}
```

---

## 错误响应

所有接口在发生错误时返回统一格式：

```json
{
  "detail": "错误描述信息"
}
```

常见HTTP状态码：
- `200`: 成功（注意：部分错误也返回200，通过detail判断）
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

---

## 数据模型

### 积分维度 (Dimensions)
- `sleep`: 睡眠维度
- `exercise`: 运动维度
- `diet`: 饮食维度
- `mental`: 心理健康维度

### 难度等级 (Difficulty)
- `easy`: 简单
- `medium`: 中等
- `hard`: 困难
- `super_hard`: 超难

### 用户等级 (Tier Levels)
- `BRONZE`: 青铜
- `SILVER`: 白银
- `GOLD`: 黄金
- `PLATINUM`: 铂金
- `DIAMOND`: 钻石
- `AMBASSADOR`: 大使

---

## 使用示例

### 获取今日积分
```bash
curl "http://localhost:12001/lsp/api/v1/score/daily?user_id=default_user"
```

### 获取健康数据汇总
```bash
curl "http://localhost:12001/lsp/api/v1/health/daily-summary?date=2025-09-18&user_id=default_user"
```

### 获取有效积分
```bash
curl "http://localhost:12001/lsp/api/v1/scores/valid?user_id=default_user"
```

### 获取积分历史
```bash
curl "http://localhost:12001/lsp/api/v1/scores/history?start_date=2025-09-01&end_date=2025-09-18&user_id=default_user"
```

---

## 部署信息

- **Python版本**: 3.11+
- **数据库**: PostgreSQL 14+
- **框架**: FastAPI + Uvicorn
- **端口**: 12001
- **环境**: 开发环境（认证已禁用）

---

## 注意事项

1. 当前为开发环境，认证系统已禁用
2. 所有接口需要指定 `user_id` 参数
3. 积分会在6个月后过期
4. 系统支持多用户数据隔离
5. 建议使用Swagger文档进行API测试：http://localhost:12001/lsp/docs