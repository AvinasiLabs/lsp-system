# 积分百分比计算功能说明文档

## 功能概述

在LSP积分系统中新增了**积分百分比计算功能**，用户在查询积分时，除了能看到实际获得的积分数值外，还能看到该积分占各维度最高分的百分比。这有助于用户更直观地了解自己在各个健康维度的完成程度。

## 功能特性

### 1. 百分比计算规则

- **计算公式**: `百分比 = (实际得分 / 最高可能得分) × 100%`
- **精度**: 保留小数点后2位
- **适用范围**: 所有维度和难度等级

### 2. 各维度最高分配置

系统中已配置的各维度最高分数：

| 维度 | 易(Easy) | 中(Medium) | 难(Hard) | 超难(Super Hard) | 总计(Total) |
|------|----------|------------|----------|------------------|-------------|
| 睡眠(Sleep) | 1,000 | 2,000 | 4,000 | 10,000 | 17,000 |
| 运动(Exercise) | 2,780 | 3,200 | 3,500 | 12,000 | 21,480 |
| 饮食(Diet) | 1,000 | 0 | 0 | 0 | 1,000 |
| 心理(Mental) | 1,000 | 3,000 | 0 | 0 | 4,000 |
| 环境(Environment) | 待实现 | 待实现 | 待实现 | 待实现 | 0 |
| 社交(Social) | 待实现 | 待实现 | 待实现 | 待实现 | 0 |
| 认知(Cognition) | 待实现 | 待实现 | 待实现 | 待实现 | 0 |
| 预防(Prevention) | 待实现 | 待实现 | 待实现 | 待实现 | 0 |

### 3. API响应更新

#### 3.1 GET /lsp/api/v1/scores/valid

**新增字段**: `dimension_percentages`

**响应示例**:
```json
{
  "user_id": "user001",
  "total_valid_score": 5000,
  "dimension_scores": {
    "sleep": 1500,
    "exercise": 2000,
    "diet": 500,
    "mental": 1000
  },
  "dimension_percentages": {
    "sleep": 8.82,      // 1500/17000 = 8.82%
    "exercise": 9.31,   // 2000/21480 = 9.31%
    "diet": 50.0,       // 500/1000 = 50%
    "mental": 25.0      // 1000/4000 = 25%
  },
  "as_of_date": "2025-09-06T10:00:00",
  "record_count": 15
}
```

#### 3.2 GET /lsp/api/v1/scores/summary/{year}/{month}

**新增字段**: `dimension_percentages`

**响应示例**:
```json
{
  "user_id": "user001",
  "year": 2025,
  "month": 9,
  "total_score": 15000,
  "active_days": 20,
  "dimension_summary": {
    "sleep": {
      "total": 5000,
      "by_difficulty": {
        "easy": 3000,
        "medium": 2000,
        "hard": 0,
        "super_hard": 0
      }
    }
  },
  "dimension_percentages": {
    "sleep": {
      "total": 29.41,  // 5000/17000 = 29.41%
      "by_difficulty": {
        "easy": 30.0,    // 3000/10000 = 30% (假设每月最多10倍单日)
        "medium": 10.0,
        "hard": 0.0,
        "super_hard": 0.0
      }
    }
  }
}
```

### 4. 核心代码更新

#### 4.1 新增配置文件
- **文件**: `src/core/score_config.py`
- **功能**: 定义各维度最高分数配置和百分比计算函数

#### 4.2 更新的文件
- `src/core/score_engine.py`: 积分引擎增加百分比计算
- `src/services/score_persistence_service.py`: 持久化服务增加百分比返回
- `src/api/score_api.py`: API响应模型增加百分比字段

## 使用示例

### 1. 测试百分比计算

```bash
# 运行测试脚本
python scripts/test_score_percentage.py
```

### 2. 通过API查询

```bash
# 启动服务器
python start_server.py

# 查询有效积分（包含百分比）
curl "http://localhost:8000/lsp/api/v1/scores/valid?user_id=test_user"

# 查询月度汇总（包含百分比）
curl "http://localhost:8000/lsp/api/v1/scores/summary/2025/9?user_id=test_user"
```

### 3. 在代码中使用

```python
from src.core.score_config import calculate_percentage

# 计算某个维度的百分比
percentage = calculate_percentage(
    actual_score=1500,  # 实际得分
    dimension="sleep",   # 维度名称
    difficulty="total"   # 难度级别或总计
)
print(f"完成度: {percentage}%")  # 输出: 完成度: 8.82%
```

## 功能优势

1. **直观性**: 百分比比纯数字更容易理解完成程度
2. **可比性**: 不同维度的百分比可以直接比较
3. **激励性**: 用户能清楚看到距离满分还有多少空间
4. **目标导向**: 帮助用户设定合理的健康目标

## 注意事项

1. **动态更新**: 如果未来调整某个维度的最高分配置，需要同步更新`score_config.py`
2. **未实现维度**: 对于尚未实现的维度，百分比将返回0
3. **等级倍数**: 百分比计算基于应用等级倍数后的实际得分

## 后续优化建议

1. **可视化**: 在前端展示时可以用进度条形式展示百分比
2. **历史对比**: 记录用户百分比变化趋势
3. **目标设定**: 允许用户设定各维度的百分比目标
4. **成就系统**: 当某个维度达到特定百分比时触发成就

## 版本记录

- **版本**: v1.0
- **日期**: 2025-09-06
- **作者**: LSP系统开发团队
- **更新内容**: 初始版本，实现基础百分比计算功能