# LSP 积分系统

基于 iOS HealthKit 数据的长寿积分(LSP)系统实现。

## 项目概述

本项目旨在通过分析用户的健康数据（主要来自 iOS HealthKit），根据LSP积分规则计算用户的健康行为积分，激励用户养成更健康的生活习惯。

## 项目结构

```
lsp_system/
├── src/                    # 源代码目录
│   ├── api/               # API接口层
│   ├── core/              # 核心业务逻辑
│   ├── db/                # 数据库相关
│   │   ├── configs/       # 数据库配置
│   │   └── postgresql.py  # PostgreSQL连接池
│   ├── models/            # 数据模型
│   ├── services/          # 业务服务层
│   └── utils/             # 工具类
├── scripts/               # 脚本文件
│   ├── test_db_connection.py      # 数据库连接测试
│   ├── import_csv_to_db.py        # CSV数据导入
│   └── analyze_healthkit_data.py  # HealthKit数据分析
├── data/                  # 数据文件
│   ├── data_30_20250709.csv      # HealthKit导出数据
│   └── sponge_no_perms.sql       # 数据库备份
├── doc/                   # 文档
│   ├── LSP积分系统规则            # 积分规则说明
│   └── LSP积分系统数据需求整理.md  # 数据需求文档
├── tests/                 # 测试代码
├── .env                   # 环境变量配置
├── .venv/                 # Python虚拟环境
├── requirements.txt       # 项目依赖
└── README.md             # 项目说明
```

## 环境要求

- Python 3.11+
- PostgreSQL 14+
- uv (Python包管理器)

## 快速开始

### 1. 安装依赖

```bash
# 激活虚拟环境
source .venv/bin/activate

# 使用uv安装依赖
uv pip install -r requirements.txt
```

### 2. 配置数据库

编辑 `.env` 文件，设置数据库连接参数：

```
POSTGRES_DBNAME = "sponge"
POSTGRES_USER = "postgres"
POSTGRES_PWD = "your_password"
POSTGRES_HOST = "127.0.0.1"
POSTGRES_PORT = 5432
```

### 3. 导入数据

```bash
# 测试数据库连接
python scripts/test_db_connection.py

# 导入HealthKit数据
python scripts/import_csv_to_db.py
```

### 4. 分析数据

```bash
# 分析HealthKit数据类型
python scripts/analyze_healthkit_data.py
```

## 主要功能模块

### 已实现

- ✅ PostgreSQL数据库连接池
- ✅ HealthKit数据导入
- ✅ 基础数据分析工具

### 待开发

- [ ] LSP积分计算引擎
- [ ] 用户行为分析
- [ ] API接口开发
- [ ] 数据可视化
- [ ] 实时积分计算

## 数据说明

### HealthKit数据类型

系统支持以下HealthKit数据类型的积分计算：

- **睡眠数据**: 睡眠时长、深度睡眠、REM睡眠
- **运动数据**: 步数、站立时间、运动时长、消耗能量
- **生理指标**: 心率、HRV、体温、血压、血氧
- **饮食数据**: 饮水量、营养摄入
- **环境数据**: 噪音暴露、UV暴露

详细的数据需求请参考 [LSP积分系统数据需求整理](doc/LSP积分系统数据需求整理.md)

## 开发指南

### 数据库操作

```python
from src.db.postgresql import POSTGRES_POOL

# 查询数据
data = POSTGRES_POOL.select_data(
    table_name="apple_healthkit",
    conditions="type = %s",
    params=("HKQuantityTypeIdentifierStepCount",)
)

# 插入数据
POSTGRES_POOL.insert_data(
    table_name="apple_healthkit",
    columns=["type", "value", "unit", "start_date"],
    values=("StepCount", "10000", "count", "2025-07-18")
)
```

### 添加新功能

1. 在 `src/core/` 中实现核心业务逻辑
2. 在 `src/models/` 中定义数据模型
3. 在 `src/services/` 中实现服务层
4. 在 `src/api/` 中暴露API接口
5. 在 `tests/` 中编写测试用例

## 贡献指南

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件