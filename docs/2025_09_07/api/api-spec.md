# LSP系统API规格文档

**版本**: v2.0  
**最后更新**: 2025-09-07  
**基础URL**: `https://api.lsp-system.com/lsp/api/v1`  
**认证方式**: JWT (可选)

## API概览

LSP积分系统提供完整的RESTful API接口，支持健康数据查询、积分计算、用户管理等功能。API设计遵循OpenAPI 3.0规范。

### 新功能特性 (v2.0)
- ✅ **积分百分比计算** - 各维度积分占最高分的百分比
- ✅ **睡眠阶段分析** - 深度睡眠、REM睡眠详细数据
- ✅ **数据源优先级管理** - 智能选择最优数据源
- ✅ **月度积分汇总** - 包含百分比统计的月度报告

## 认证

### JWT认证 (可选)
```http
Authorization: Bearer <jwt_token>
```

### 无认证模式
当环境变量 `AUTH_ENABLED=false` 时，API可在无认证模式下运行，适用于开发和测试环境。

## 核心接口

### 1. 健康数据接口

#### 1.1 获取每日健康数据汇总
```yaml
GET /health/daily-summary
```

**参数**:
| 参数名 | 类型 | 必需 | 描述 | 默认值 |
|--------|------|------|------|--------|
| date | string(date) | 否 | 查询日期 YYYY-MM-DD | 今天 |
| user_id | string | 否* | 用户ID | 从认证获取 |

**响应**:
```json
{
  "user_id": "user123",
  "date": "2025-09-07",
  "data": {
    "sleep_hours": 7.5,
    "sleep_stages": {
      "deep_sleep_hours": 1.8,
      "rem_sleep_hours": 1.5,
      "light_sleep_hours": 4.2,
      "awake_hours": 0.0
    },
    "steps": 8532,
    "stand_hours": 10,
    "exercise_minutes": 45,
    "water_intake_liters": 2.1,
    "heart_rate_variability": 35.2
  },
  "data_sources": {
    "sleep": "Apple Watch",
    "steps": "iPhone",
    "exercise": "Apple Watch"
  }
}
```

#### 1.2 获取健康数据类型列表
```yaml
GET /health/data-types
```

**响应**:
```json
{
  "available_types": [
    {
      "type": "HKQuantityTypeIdentifierStepCount",
      "display_name": "步数",
      "unit": "count",
      "category": "activity"
    },
    {
      "type": "HKCategoryTypeIdentifierSleepAnalysis", 
      "display_name": "睡眠分析",
      "unit": "hours",
      "category": "sleep"
    }
  ],
  "total_count": 24
}
```

### 2. 积分计算接口

#### 2.1 计算每日积分
```yaml
GET /score/daily
```

**参数**:
| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| date | string(date) | 否 | 计算日期 |
| user_id | string | 否* | 用户ID |

**响应** (v2.0新增百分比字段):
```json
{
  "user_id": "user123",
  "date": "2025-09-07",
  "dimension_scores": {
    "sleep": {
      "total": 3000,
      "details": {
        "easy": 1000,
        "medium": 2000,
        "hard": 0,
        "super_hard": 0
      }
    },
    "exercise": {
      "total": 2400,
      "details": {
        "easy": 2400,
        "medium": 0,
        "hard": 0,
        "super_hard": 0
      }
    }
  },
  "dimension_percentages": {
    "sleep": {
      "total": 17.65,
      "details": {
        "easy": 100.0,
        "medium": 100.0,
        "hard": 0.0,
        "super_hard": 0.0
      }
    },
    "exercise": {
      "total": 11.17,
      "details": {
        "easy": 86.33,
        "medium": 0.0,
        "hard": 0.0,
        "super_hard": 0.0
      }
    }
  },
  "total_score": 5400,
  "tier_multiplier": 1.0,
  "tier_level": "Bronze"
}
```

### 3. 积分查询接口

#### 3.1 获取有效积分
```yaml
GET /scores/valid
```

**参数**:
| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| as_of_date | string(date) | 否 | 计算截止日期 |

**响应** (v2.0新增百分比统计):
```json
{
  "user_id": "user123",
  "total_valid_score": 125400,
  "dimension_scores": {
    "sleep": 45000,
    "exercise": 38200,
    "diet": 2500,
    "mental": 15600
  },
  "dimension_percentages": {
    "sleep": 15.2,
    "exercise": 12.8,
    "diet": 8.3,
    "mental": 11.7
  },
  "as_of_date": "2025-09-07T00:00:00",
  "record_count": 156
}
```

#### 3.2 获取积分历史
```yaml
GET /scores/history
```

**参数**:
| 参数名 | 类型 | 必需 | 描述 | 限制 |
|--------|------|------|------|------|
| start_date | string(date) | 是 | 开始日期 | - |
| end_date | string(date) | 是 | 结束日期 | 不能早于开始日期 |
| include_expired | boolean | 否 | 包含过期积分 | false |

**响应**:
```json
[
  {
    "id": 1234,
    "date": "2025-09-07",
    "dimension": "sleep", 
    "sub_category": "duration",
    "difficulty": "easy",
    "score": 1000,
    "expire_date": "2026-03-07",
    "is_expired": false,
    "tier_level": "Bronze",
    "details": {
      "sleep_hours": 7.5,
      "target_hours": 7.5,
      "data_source": "Apple Watch"
    },
    "created_at": "2025-09-07T06:30:00Z"
  }
]
```

#### 3.3 获取即将过期积分
```yaml
GET /scores/expiring
```

**参数**:
| 参数名 | 类型 | 必需 | 描述 | 范围 |
|--------|------|------|------|------|
| days_ahead | integer | 否 | 查询天数 | 1-180天 |

**响应**:
```json
{
  "user_id": "user123",
  "days_ahead": 30,
  "total_expiring_score": 15600,
  "expiring_by_date": [
    {
      "expire_date": "2025-10-01",
      "score": 8400,
      "record_count": 12
    },
    {
      "expire_date": "2025-10-05", 
      "score": 7200,
      "record_count": 8
    }
  ]
}
```

#### 3.4 获取月度积分汇总 (v2.0新增)
```yaml
GET /scores/summary/{year}/{month}
```

**参数**:
| 参数名 | 类型 | 必需 | 描述 | 范围 |
|--------|------|------|------|------|
| year | integer | 是 | 年份 | 2020-2030 |
| month | integer | 是 | 月份 | 1-12 |

**响应** (包含百分比统计):
```json
{
  "user_id": "user123",
  "year": 2025,
  "month": 9,
  "total_score": 162800,
  "active_days": 28,
  "dimension_summary": {
    "sleep": {
      "total": 84000,
      "by_difficulty": {
        "easy": 28000,
        "medium": 56000,
        "hard": 0,
        "super_hard": 0
      }
    },
    "exercise": {
      "total": 67200,
      "by_difficulty": {
        "easy": 67200,
        "medium": 0,
        "hard": 0,
        "super_hard": 0
      }
    }
  },
  "dimension_percentages": {
    "sleep": {
      "total": 16.4,
      "by_difficulty": {
        "easy": 93.3,
        "medium": 93.3,
        "hard": 0.0,
        "super_hard": 0.0
      }
    },
    "exercise": {
      "total": 10.4,
      "by_difficulty": {
        "easy": 80.2,
        "medium": 0.0,
        "hard": 0.0,
        "super_hard": 0.0
      }
    }
  }
}
```

### 4. 用户管理接口

#### 4.1 获取等级统计
```yaml
GET /scores/tier-stats
```

**响应**:
```json
{
  "user_id": "user123",
  "current_tier": "Bronze",
  "total_earned_score": 1250000,
  "total_valid_score": 125400,
  "expiration_months": 6
}
```

#### 4.2 检查积分过期 (管理员)
```yaml
POST /scores/check-expiration
```

**响应**:
```json
{
  "checked_count": 15420,
  "expired_count": 238,
  "message": "检查了15420条记录，标记了238条为过期"
}
```

### 5. 系统监控接口

#### 5.1 健康检查
```yaml
GET /health
```

**响应**:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-07T10:30:00Z",
  "version": "2.0.0",
  "database": {
    "status": "connected",
    "total_records": 84552
  },
  "services": {
    "score_engine": "running",
    "persistence_service": "running"
  }
}
```

## 错误处理

### 标准错误响应格式
```json
{
  "detail": "错误描述信息",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-09-07T10:30:00Z"
}
```

### 常见错误码

| HTTP状态码 | 错误码 | 描述 | 解决方案 |
|------------|--------|------|----------|
| 400 | INVALID_PARAMETERS | 请求参数无效 | 检查参数格式和范围 |
| 400 | INVALID_DATE_RANGE | 日期范围无效 | 确保结束日期不早于开始日期 |
| 400 | QUERY_RANGE_TOO_LARGE | 查询范围过大 | 限制查询范围在365天内 |
| 401 | UNAUTHORIZED | 认证失败 | 提供有效的JWT token |
| 404 | USER_NOT_FOUND | 用户不存在 | 确认用户ID正确 |
| 404 | NO_DATA_FOUND | 未找到数据 | 确认日期范围内有数据 |
| 500 | DATABASE_ERROR | 数据库错误 | 检查数据库连接状态 |
| 500 | CALCULATION_ERROR | 计算引擎错误 | 查看服务器日志详情 |

### 错误处理最佳实践

1. **参数验证**
   ```bash
   # 错误示例
   curl "http://localhost:8000/lsp/api/v1/scores/history?start_date=2025-10-01&end_date=2025-09-01"
   
   # 响应
   {
     "detail": "结束日期不能早于开始日期",
     "error_code": "INVALID_DATE_RANGE"
   }
   ```

2. **数据不存在**
   ```bash
   curl "http://localhost:8000/lsp/api/v1/health/daily-summary?date=2020-01-01"
   
   # 响应  
   {
     "user_id": "user123",
     "date": "2020-01-01",
     "data": {},
     "message": "该日期无健康数据记录"
   }
   ```

## 数据模型

### 积分计算配置 (v2.0)
```yaml
# score_config.py 配置结构
DIMENSION_MAX_SCORES:
  sleep:
    easy: 1000      # 睡够7.5小时
    medium: 2000    # 深度睡眠 + REM睡眠
    hard: 4000      # 作息时间限制
    super_hard: 10000  # 连续记录奖励
    total: 17000    # 维度最高分
  
  exercise:
    easy: 2780      # 步数 + 站立时间
    medium: 3200    # 运动时长
    hard: 3500      # 运动类型组合
    super_hard: 12000  # 连续运动奖励
    total: 21480
```

### 百分比计算公式
```python
百分比 = (实际得分 / 最高分数) × 100

# 示例
sleep_percentage = (3000 / 17000) × 100 = 17.65%
```

### 数据源优先级
```yaml
睡眠数据优先级:
  1. Apple Watch (最高精度)
  2. Oura Ring
  3. WHOOP
  4. OffScreen App
  
运动数据优先级:
  1. Apple Watch
  2. iPhone (步数)
  3. 第三方fitness tracker
```

## API使用示例

### 1. Python客户端示例
```python
import requests
from datetime import date, timedelta

# 配置
BASE_URL = "http://localhost:8000/lsp/api/v1"
headers = {"Authorization": "Bearer your_jwt_token"}  # 可选

# 获取今日积分 (包含百分比)
def get_daily_score():
    response = requests.get(
        f"{BASE_URL}/score/daily",
        params={"date": date.today().isoformat()},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"今日总分: {data['total_score']}")
        print("各维度百分比:")
        for dim, pct in data['dimension_percentages'].items():
            print(f"  {dim}: {pct['total']}%")
    else:
        print(f"错误: {response.json()}")

# 获取月度汇总
def get_monthly_summary(year, month):
    response = requests.get(
        f"{BASE_URL}/scores/summary/{year}/{month}",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"{year}年{month}月汇总:")
        print(f"总分: {data['total_score']}")
        print(f"活跃天数: {data['active_days']}")
        
        # 打印各维度百分比
        for dim, stats in data['dimension_percentages'].items():
            print(f"{dim}: {stats['total']:.1f}%")
```

### 2. cURL示例
```bash
# 获取有效积分 (含百分比)
curl -X GET "http://localhost:8000/lsp/api/v1/scores/valid" \
     -H "Content-Type: application/json"

# 获取月度汇总
curl -X GET "http://localhost:8000/lsp/api/v1/scores/summary/2025/9" \
     -H "Authorization: Bearer your_jwt_token"

# 获取健康数据 (睡眠阶段详情)
curl -X GET "http://localhost:8000/lsp/api/v1/health/daily-summary?date=2025-09-07"
```

### 3. JavaScript/Fetch示例
```javascript
// 获取积分历史并显示百分比
async function fetchScoreHistory() {
  const startDate = '2025-09-01';
  const endDate = '2025-09-07';
  
  try {
    const response = await fetch(
      `/lsp/api/v1/scores/history?start_date=${startDate}&end_date=${endDate}`,
      {
        headers: {
          'Authorization': 'Bearer your_jwt_token',
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (response.ok) {
      const history = await response.json();
      console.log('积分历史:', history);
      
      // 按维度分组统计
      const dimensionStats = {};
      history.forEach(record => {
        if (!dimensionStats[record.dimension]) {
          dimensionStats[record.dimension] = 0;
        }
        dimensionStats[record.dimension] += record.score;
      });
      
      console.log('维度统计:', dimensionStats);
    } else {
      const error = await response.json();
      console.error('获取失败:', error.detail);
    }
  } catch (err) {
    console.error('请求错误:', err);
  }
}
```

## 性能和限制

### API限制
- **查询日期范围**: 单次查询不超过365天
- **即将过期查询**: 最多查询180天内过期积分
- **并发请求**: 建议不超过100 QPS
- **数据延迟**: HealthKit数据同步可能有1-2小时延迟

### 缓存策略
- **健康数据**: 缓存1小时
- **积分计算**: 缓存30分钟  
- **用户统计**: 缓存6小时

### 数据源同步
- **Apple HealthKit**: 实时同步
- **第三方设备**: 15分钟同步间隔
- **手动输入**: 实时生效

## 版本更新记录

### v2.0 (2025-09-07)
- ✅ 新增积分百分比计算功能
- ✅ 新增月度积分汇总接口  
- ✅ 增强睡眠数据分析 (深度睡眠、REM睡眠)
- ✅ 实现数据源优先级管理
- ✅ 优化错误处理和响应格式
- ✅ 更新所有响应模型包含百分比字段

### v1.0 (2025-07-22)  
- ✅ 基础API接口实现
- ✅ 积分计算和持久化
- ✅ 用户管理和认证
- ✅ Docker部署支持

## 技术规格

### 技术栈
- **框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 15+
- **认证**: JWT (PyJWT)
- **文档**: OpenAPI 3.0 / Swagger UI
- **部署**: Docker + docker-compose

### 环境配置
```bash
# 必需环境变量
DATABASE_URL=postgresql://user:pass@localhost:5432/lsp_db
JWT_SECRET_KEY=your-secret-key

# 可选配置
AUTH_ENABLED=true          # 启用认证 (默认: true)
LOG_LEVEL=INFO            # 日志级别 (默认: INFO)  
API_PREFIX=/lsp/api/v1    # API前缀 (默认: /lsp/api/v1)
```

### OpenAPI文档
- **Swagger UI**: `http://localhost:8000/lsp/docs`
- **ReDoc**: `http://localhost:8000/lsp/redoc`
- **OpenAPI JSON**: `http://localhost:8000/lsp/openapi.json`

---

**文档版本**: v2.0  
**创建日期**: 2025-09-07  
**负责人**: 系统架构师  
**审核状态**: Draft

**修改历史**:
- v2.0 (2025-09-07): 新增积分百分比功能、睡眠阶段分析、月度汇总等新功能的完整API规格
- v1.0 (2025-07-22): 初始API规格文档