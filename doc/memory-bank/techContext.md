# Tech Context: LSP积分系统

## 技术栈

### 后端技术
- **语言**: Python 3.11+
- **框架**: FastAPI (计划使用)
- **数据库**: PostgreSQL 14+
- **缓存**: Redis (计划使用)
- **任务队列**: Celery (计划使用)

### 前端技术 (计划)
- **框架**: React/Next.js
- **状态管理**: Redux Toolkit
- **UI组件**: Ant Design / Material-UI
- **图表**: Chart.js / D3.js

### 开发工具
- **包管理**: uv (超快的Python包管理器)
- **虚拟环境**: .venv
- **版本控制**: Git
- **代码质量**: Black, Flake8, mypy

## 开发环境设置

### 1. Python环境
```bash
# 使用uv创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
uv pip install -r requirements.txt
```

### 2. 数据库设置
```bash
# PostgreSQL配置
POSTGRES_DBNAME = "sponge"
POSTGRES_USER = "postgres"
POSTGRES_PWD = "Sponge_2025"
POSTGRES_HOST = "127.0.0.1"
POSTGRES_PORT = 5432
```

### 3. 环境变量
所有敏感配置通过`.env`文件管理：
- 数据库连接信息
- API密钥
- 第三方服务配置

## 主要依赖

### 核心依赖
```txt
psycopg2-binary==2.9.10    # PostgreSQL驱动
pydantic-settings==2.10.1   # 配置管理
python-dotenv==1.1.1        # 环境变量
pandas==2.3.1               # 数据处理
numpy==2.3.1                # 数值计算
```

### 计划添加的依赖
```txt
fastapi==0.100+             # Web框架
uvicorn==0.20+              # ASGI服务器
sqlalchemy==2.0+            # ORM
alembic==1.10+              # 数据库迁移
redis==4.5+                 # Redis客户端
celery==5.2+                # 异步任务
pytest==7.3+                # 测试框架
```

## 项目结构说明

```
lsp_system/
├── src/
│   ├── api/               # API端点定义
│   │   ├── v1/           # API版本1
│   │   └── middlewares/  # 中间件
│   ├── core/             # 核心业务逻辑
│   │   ├── calculators/  # 积分计算器
│   │   ├── rules/        # 规则引擎
│   │   └── validators/   # 数据验证
│   ├── db/               # 数据库相关
│   │   ├── models/       # SQLAlchemy模型
│   │   ├── repositories/ # 数据访问层
│   │   └── migrations/   # Alembic迁移
│   ├── services/         # 业务服务层
│   │   ├── health_data/  # 健康数据服务
│   │   ├── scoring/      # 积分服务
│   │   └── user/         # 用户服务
│   └── utils/            # 工具函数
├── scripts/              # 独立脚本
├── tests/                # 测试代码
│   ├── unit/            # 单元测试
│   ├── integration/     # 集成测试
│   └── fixtures/        # 测试数据
└── data/                # 数据文件
```

## 技术约束

### 性能要求
- API响应时间 < 200ms (P95)
- 批量数据导入 > 1000条/秒
- 并发用户支持 > 10000

### 安全要求
- 所有API需要认证
- 敏感数据加密存储
- 完整的审计日志
- GDPR/HIPAA合规考虑

### 可扩展性
- 水平扩展能力
- 数据库分片准备
- 微服务架构准备
- 多租户支持

## 开发规范

### 代码风格
```python
# 使用类型注解
def calculate_sleep_score(
    sleep_hours: float, 
    deep_sleep_hours: float,
    rem_sleep_hours: float
) -> int:
    """计算睡眠积分"""
    pass

# 使用数据类
from dataclasses import dataclass
from datetime import datetime

@dataclass
class HealthData:
    user_id: str
    type: str
    value: float
    timestamp: datetime
```

### 错误处理
```python
# 自定义异常
class LSPException(Exception):
    """基础异常类"""
    pass

class DataValidationError(LSPException):
    """数据验证错误"""
    pass

class ScoreCalculationError(LSPException):
    """积分计算错误"""
    pass
```

### 日志规范
```python
import logging

logger = logging.getLogger(__name__)

# 使用结构化日志
logger.info("Score calculated", extra={
    "user_id": user_id,
    "score": score,
    "dimension": "sleep"
})
```

## 部署考虑

### 容器化
```dockerfile
# Dockerfile示例
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0"]
```

### 环境配置
- **开发环境**: 本地PostgreSQL + Redis
- **测试环境**: Docker Compose
- **生产环境**: Kubernetes + 云数据库

### 监控和日志
- **APM**: Datadog / New Relic
- **日志**: ELK Stack
- **指标**: Prometheus + Grafana
- **错误追踪**: Sentry

## 第三方服务集成

### 已集成
- iOS HealthKit (数据源)
- PostgreSQL (数据存储)

### 计划集成
- Redis (缓存)
- SendGrid/SES (邮件)
- Twilio (短信)
- Stripe (支付)
- AWS S3 (文件存储)

## CI/CD流程

### 开发流程
1. 功能分支开发
2. 本地测试通过
3. 代码审查
4. 合并到主分支
5. 自动部署到测试环境

### 自动化测试
```yaml
# GitHub Actions示例
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest
```

## 技术债务和改进计划

### 当前技术债务
1. 缺少完整的测试覆盖
2. 没有API文档
3. 缺少性能基准测试
4. 数据库查询未优化

### 改进计划
1. **Phase 1**: 添加单元测试
2. **Phase 2**: 实现API文档(OpenAPI)
3. **Phase 3**: 性能优化
4. **Phase 4**: 添加缓存层
5. **Phase 5**: 微服务拆分准备