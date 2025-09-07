# 睡眠阶段积分计算功能文档

## 功能概述

LSP积分系统新增了**睡眠阶段分析功能**，实现了睡眠维度的中级别和难级别积分计算：
- **中级别**：深度睡眠和REM睡眠检测（2000分）
- **难级别**：入睡和起床时间限制（4000分）

## 实现详情

### 1. 数据源

系统使用HealthKit数据中的睡眠阶段信息：
- **主要数据源**：Oura（提供完整的睡眠阶段数据）
- **备选数据源**：WHOOP、OffScreen等
- **数据类型**：`HKCategoryTypeIdentifierSleepAnalysis`

### 2. 睡眠阶段分类

```python
睡眠阶段映射 = {
    'HKCategoryValueSleepAnalysisAwake': 'awake',        # 清醒
    'HKCategoryValueSleepAnalysisAsleepCore': 'core',    # 核心睡眠
    'HKCategoryValueSleepAnalysisAsleepDeep': 'deep',    # 深度睡眠
    'HKCategoryValueSleepAnalysisAsleepREM': 'rem',      # REM睡眠
    'HKCategoryValueSleepAnalysisInBed': 'in_bed',       # 在床
    'HKCategoryValueSleepAnalysisAsleepUnspecified': 'unspecified'  # 未指定
}
```

### 3. 积分规则

#### 3.1 中级别：深度睡眠 + REM睡眠（2000分）

**要求**：
- 深度睡眠 ≥ 1.5小时
- REM睡眠 ≥ 1.5小时

**积分计算**：
- 两项都达标：2000分
- 仅一项达标：1000分
- 都未达标：0分

#### 3.2 难级别：时间限制（4000分）

**要求**：
- 入睡时间：23:30前
- 起床时间：7:30前
- 前提条件：易级别和中级别都获得积分

**积分计算**：
- 两项都达标：4000分
- 仅一项达标：2000分
- 都未达标：0分

## 核心组件

### 1. 睡眠分析服务（SleepAnalysisService）

**文件位置**：`src/services/sleep_analysis_service.py`

**主要功能**：
- `get_sleep_stages_data()`: 从数据库获取睡眠阶段数据
- `analyze_sleep_stages()`: 分析一晚的睡眠阶段，统计各阶段时长
- `get_sleep_time_details()`: 获取入睡和起床时间，判断是否满足时间要求
- `get_monthly_sleep_analysis()`: 获取整月的睡眠分析

**使用示例**：
```python
from src.services.sleep_analysis_service import SleepAnalysisService

service = SleepAnalysisService()

# 分析某一天的睡眠
analysis = service.analyze_sleep_stages(
    user_id="user001",
    date=datetime(2025, 6, 11),
    source_filter='Oura'  # 可选，指定数据源
)

# 返回结果
{
    'date': '2025-06-11',
    'has_data': True,
    'stages_duration_hours': {
        'deep': 1.8,   # 深度睡眠时长
        'rem': 1.6,    # REM睡眠时长
        'core': 3.2,   # 核心睡眠时长
        'awake': 0.5   # 清醒时长
    },
    'sleep_time': '2025-06-10T23:15:00',  # 入睡时间
    'wake_time': '2025-06-11T07:15:00',   # 起床时间
    'total_sleep_hours': 6.6
}
```

### 2. 更新的睡眠计算器（SleepCalculator）

**文件位置**：`src/core/calculators/sleep_calculator.py`

**新增方法**：
- `_calculate_medium_with_stages()`: 计算深度睡眠和REM睡眠积分
- `_calculate_hard_with_time_limits()`: 计算时间限制积分

**调用方式**：
```python
from src.core.calculators.sleep_calculator import SleepCalculator

calculator = SleepCalculator()

# 需要传递user_id和date参数
scores = calculator.calculate(
    health_data,
    user_id="user001",
    date=datetime(2025, 6, 11)
)

# 返回结果
{
    'easy': 1000,    # 睡眠时长积分
    'medium': 2000,  # 深度+REM睡眠积分
    'hard': 4000,    # 时间限制积分
    'super_hard': 0,
    'total': 7000
}
```

### 3. 积分引擎更新

**文件位置**：`src/core/score_engine.py`

**更新内容**：
- 为睡眠计算器传递`user_id`和`date`参数
- 保持其他计算器的兼容性

## 数据库查询

睡眠阶段数据存储在`health_metric`表中：

```sql
-- 查询某天的睡眠阶段数据
SELECT start_date, end_date, value, source_name
FROM health_metric
WHERE type = 'HKCategoryTypeIdentifierSleepAnalysis'
  AND user_id = 'user001'
  AND start_date >= '2025-06-10 18:00:00'
  AND end_date <= '2025-06-11 12:00:00'
  AND source_name = 'Oura'
ORDER BY start_date;
```

## 测试验证

### 运行测试脚本

```bash
# 测试睡眠阶段分析功能
python scripts/test_sleep_stages.py
```

### 测试内容

1. **睡眠阶段分析服务测试**
   - 验证数据获取
   - 验证阶段时长统计
   - 验证时间判断逻辑

2. **积分计算测试**
   - 验证中级别积分计算
   - 验证难级别积分计算
   - 验证前提条件判断

3. **多天数据测试**
   - 验证连续多天的分析
   - 验证积分累计

## 注意事项

1. **数据源依赖**：功能依赖于有睡眠阶段数据的设备（如Oura、WHOOP）
2. **时间判断**：凌晨入睡的情况会正确处理（如凌晨1点入睡仍算前一天）
3. **兼容性**：保留了旧方法，无数据时自动回退
4. **数据质量**：不同数据源的睡眠阶段分类可能不同，Oura数据最完整

## 后续优化建议

1. **支持Apple Watch原生数据**：等待Apple Watch提供睡眠阶段数据
2. **智能数据源选择**：自动选择质量最好的数据源
3. **睡眠质量评分**：基于多维度计算综合睡眠质量分数
4. **超难级别实现**：连续15天达到易中难标准（需要历史数据支持）
5. **可视化报告**：生成睡眠趋势图表

## 版本记录

- **版本**: v1.1
- **日期**: 2025-09-06
- **作者**: LSP系统开发团队
- **更新内容**: 实现睡眠中级别和难级别积分计算功能