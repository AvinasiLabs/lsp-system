# 多数据源管理服务文档

## 功能概述

多数据源管理服务（Data Source Manager）是LSP积分系统中处理多种健康数据来源的核心服务，专门解决数据冲突、重复和优先级选择问题。目前主要应用于睡眠数据的智能选择和管理。

**实现时间**：2025-09-07  
**状态**：✅ 已完成睡眠数据源管理器  
**核心文件**：`src/services/sleep_data_source_manager.py`

## 解决的核心问题

### 1. 数据源冲突
- **Apple Watch vs HealthKit**：同一用户的睡眠数据可能来自多个设备
- **数据重复**：相同时间段的多条睡眠记录
- **数据质量差异**：不同设备的数据精度和完整性不同

### 2. 数据选择策略
- **优先级规则**：根据数据源可靠性确定选择优先级
- **质量评估**：基于数据完整性和一致性选择最佳数据
- **智能合并**：在合适的情况下合并多个数据源

## 核心功能

### 1. 睡眠数据源管理器

#### 支持的数据源类型
```python
# 数据源优先级定义（优先级从高到低）
DATA_SOURCE_PRIORITY = {
    "Apple Watch": 1,           # 最高优先级：Apple Watch直接数据
    "iPhone": 2,                # 中等优先级：iPhone健康应用
    "HealthKit_Auto": 3,        # 较低优先级：HealthKit自动数据
    "HealthKit_Manual": 4,      # 最低优先级：手动输入数据
    "Unknown": 5                # 未知来源
}
```

#### 实现架构
```python
class SleepDataSourceManager:
    """睡眠数据源管理器"""
    
    def __init__(self):
        """初始化管理器"""
        self.priority_rules = DATA_SOURCE_PRIORITY
        
    def select_best_sleep_data(self, user_id: str, date: datetime) -> list:
        """
        选择指定日期的最佳睡眠数据
        
        Args:
            user_id: 用户ID
            date: 目标日期
            
        Returns:
            list: 优选后的睡眠数据记录
        """
        
    def resolve_data_conflicts(self, sleep_records: list) -> list:
        """解决睡眠数据冲突"""
        
    def assess_data_quality(self, record: dict) -> float:
        """评估数据质量分数 (0-100)"""
        
    def merge_overlapping_records(self, records: list) -> list:
        """合并重叠的睡眠记录"""
```

### 2. 数据质量评估算法

#### 评估标准
```python
def assess_data_quality(self, record: dict) -> float:
    """
    数据质量评估算法
    
    评估标准：
    1. 时长合理性 (30分 - 是否在合理的睡眠时长范围内)
    2. 时间连续性 (25分 - 开始和结束时间是否合理)
    3. 数据源可靠性 (25分 - 基于设备类型的可靠性)
    4. 数据完整性 (20分 - 必要字段是否完整)
    
    Returns:
        float: 质量分数 (0-100)
    """
    quality_score = 0
    
    # 1. 时长合理性检查
    duration_hours = self._calculate_duration_hours(record)
    if 0.5 <= duration_hours <= 12:  # 30分钟到12小时合理
        if 6 <= duration_hours <= 10:  # 最理想范围
            quality_score += 30
        elif 4 <= duration_hours <= 12:  # 可接受范围
            quality_score += 20
        else:  # 边缘情况
            quality_score += 10
    
    # 2. 时间连续性检查
    if self._is_time_continuous(record):
        quality_score += 25
    elif self._is_time_reasonable(record):
        quality_score += 15
    
    # 3. 数据源可靠性
    source = record.get('source_name', 'Unknown')
    source_score = 25 - (self.priority_rules.get(source, 5) - 1) * 5
    quality_score += max(0, source_score)
    
    # 4. 数据完整性
    required_fields = ['start_date', 'end_date', 'value']
    completeness = sum(1 for field in required_fields if record.get(field))
    quality_score += (completeness / len(required_fields)) * 20
    
    return min(100, quality_score)
```

### 3. 冲突解决策略

#### 重叠数据处理
```python
def resolve_overlapping_records(self, records: list) -> list:
    """
    解决重叠睡眠记录的冲突
    
    策略：
    1. 按数据源优先级排序
    2. 选择质量评分最高的记录
    3. 对于部分重叠，选择覆盖时间最长的记录
    4. 如果质量相近，优先选择最新记录
    """
    if len(records) <= 1:
        return records
    
    # 按优先级和质量评分排序
    sorted_records = sorted(records, key=lambda x: (
        self.priority_rules.get(x.get('source_name', 'Unknown'), 5),
        -self.assess_data_quality(x),  # 质量分数降序
        -x.get('id', 0)  # ID降序（较新记录）
    ))
    
    # 选择最佳记录，去除重叠
    selected_records = []
    for record in sorted_records:
        if not self._has_significant_overlap(record, selected_records):
            selected_records.append(record)
    
    return selected_records
```

#### 数据合并逻辑
```python
def merge_compatible_records(self, records: list) -> list:
    """
    合并兼容的睡眠记录
    
    合并条件：
    1. 来自同一数据源
    2. 时间间隔小于30分钟
    3. 数据质量评分相近
    """
    if len(records) <= 1:
        return records
    
    merged_records = []
    current_group = [records[0]]
    
    for record in records[1:]:
        if self._can_merge_with_group(record, current_group):
            current_group.append(record)
        else:
            # 合并当前组
            merged_record = self._merge_record_group(current_group)
            merged_records.append(merged_record)
            current_group = [record]
    
    # 处理最后一组
    if current_group:
        merged_record = self._merge_record_group(current_group)
        merged_records.append(merged_record)
    
    return merged_records
```

## 应用场景

### 1. 睡眠积分计算优化

**问题**：用户同时使用Apple Watch和iPhone记录睡眠，导致重复计算
**解决方案**：
```python
from src.services.sleep_data_source_manager import SleepDataSourceManager

# 创建数据源管理器
manager = SleepDataSourceManager()

# 获取优选的睡眠数据
best_sleep_data = manager.select_best_sleep_data(user_id, date)

# 用于睡眠积分计算
sleep_calculator.calculate(best_sleep_data)
```

**效果**：
- 消除数据重复问题
- 选择质量最高的数据源
- 提高积分计算准确性

### 2. 数据质量监控

**场景**：监控和提升系统数据质量
```python
# 批量评估数据质量
quality_report = manager.generate_quality_report(user_id, date_range)

# 识别低质量数据源
low_quality_sources = manager.identify_problematic_sources()

# 优化数据采集策略
manager.optimize_collection_strategy()
```

### 3. Apple Watch专项处理

**问题**：Apple Watch数据在某些情况下可能不如HealthKit准确
**解决方案**：
```python
# 智能选择：Apple Watch数据质量评估
if manager.is_apple_watch_data_reliable(record):
    # 优先使用Apple Watch数据
    selected_data = apple_watch_records
else:
    # 回退到HealthKit数据
    selected_data = healthkit_records
```

## 技术实现细节

### 1. 数据获取和预处理

```python
def get_all_sleep_sources(self, user_id: str, date: datetime) -> dict:
    """获取所有可用的睡眠数据源"""
    sources = {}
    
    # HealthKit睡眠分析数据
    healthkit_data = self._get_healthkit_sleep_data(user_id, date)
    if healthkit_data:
        sources['healthkit'] = healthkit_data
    
    # Apple Watch特定数据
    watch_data = self._get_apple_watch_sleep_data(user_id, date)
    if watch_data:
        sources['apple_watch'] = watch_data
    
    # 手动输入数据
    manual_data = self._get_manual_sleep_data(user_id, date)
    if manual_data:
        sources['manual'] = manual_data
    
    return sources
```

### 2. 性能优化

```python
# 缓存机制
@cached(ttl=300)  # 5分钟缓存
def select_best_sleep_data(self, user_id: str, date: datetime) -> list:
    """缓存优选结果，避免重复计算"""
    
# 批量处理
def select_best_sleep_data_batch(self, requests: list) -> dict:
    """批量处理多个用户/日期的数据选择"""
    
# 异步处理
async def select_best_sleep_data_async(self, user_id: str, date: datetime) -> list:
    """异步版本的数据选择"""
```

### 3. 扩展性设计

```python
class BaseDataSourceManager:
    """数据源管理器基类"""
    
    def select_best_data(self, user_id: str, date: datetime, data_type: str) -> list:
        """通用数据选择接口"""
        
    def register_data_source(self, source_name: str, priority: int):
        """注册新数据源"""
        
class ExerciseDataSourceManager(BaseDataSourceManager):
    """运动数据源管理器（未来扩展）"""
    
class DietDataSourceManager(BaseDataSourceManager):
    """饮食数据源管理器（未来扩展）"""
```

## 测试验证

### 测试覆盖范围

1. **数据源识别测试**
   - ✅ Apple Watch数据识别准确性
   - ✅ HealthKit数据分类正确性
   - ✅ 未知数据源处理

2. **质量评估测试**
   - ✅ 正常睡眠数据质量评分
   - ✅ 异常数据识别和降分
   - ✅ 边界条件处理

3. **冲突解决测试**
   - ✅ 重叠数据去重
   - ✅ 优先级选择准确性
   - ✅ 合并逻辑正确性

4. **性能测试**
   - ✅ 大量数据处理性能
   - ✅ 缓存机制有效性
   - ✅ 内存使用优化

### 测试脚本

- `test_all_sleep_sources.py`：多数据源综合测试
- `test_apple_watch_sleep.py`：Apple Watch数据专项测试  
- `scripts/test_sleep_stages.py`：集成测试包含数据源管理

## 配置和定制

### 1. 优先级配置

```python
# 自定义数据源优先级
CUSTOM_PRIORITY = {
    "Oura_Ring": 1,      # 如果用户使用Oura Ring
    "Apple_Watch": 2,
    "Fitbit": 3,
    "HealthKit": 4
}

manager = SleepDataSourceManager(priority_rules=CUSTOM_PRIORITY)
```

### 2. 质量评估权重调整

```python
# 自定义质量评估权重
QUALITY_WEIGHTS = {
    "duration_reasonableness": 0.4,  # 时长合理性权重40%
    "time_continuity": 0.3,          # 时间连续性权重30%
    "source_reliability": 0.2,       # 数据源可靠性权重20%
    "data_completeness": 0.1         # 数据完整性权重10%
}
```

### 3. 合并策略配置

```python
# 配置数据合并规则
MERGE_CONFIG = {
    "max_gap_minutes": 30,           # 最大间隔30分钟内可合并
    "min_quality_diff": 10,          # 质量分数差异小于10分可合并
    "allow_cross_source_merge": False # 不允许跨数据源合并
}
```

## 性能特征

- **响应时间**：单日数据选择 < 50ms
- **内存使用**：峰值 < 30MB
- **并发支持**：支持多用户同时处理
- **缓存机制**：5分钟智能缓存，减少重复计算
- **批量处理**：支持批量用户数据处理

## 监控和日志

### 日志级别

- **INFO**：数据源选择和处理流程
- **WARNING**：数据质量问题和冲突解决
- **ERROR**：数据获取失败或处理异常
- **DEBUG**：详细的评分和选择过程

### 监控指标

```python
# 关键监控指标
metrics = {
    "data_source_distribution": "各数据源使用分布",
    "quality_score_average": "平均数据质量评分",
    "conflict_resolution_rate": "冲突解决成功率",
    "processing_time_p95": "处理时间95分位数",
    "cache_hit_rate": "缓存命中率"
}
```

## 问题排查

### 常见问题

**Q: 为什么Apple Watch数据没有被优先选择？**  
A: 检查数据质量评分，可能Apple Watch数据存在异常导致质量评分下降

**Q: 数据选择结果不稳定？**  
A: 可能是质量评分接近导致的，可以调整评估权重或增加稳定性因子

**Q: 处理性能较慢？**  
A: 检查缓存是否生效，考虑启用批量处理模式

### 调试工具

```python
# 查看数据源选择详情
debug_info = manager.get_selection_debug_info(user_id, date)
print(json.dumps(debug_info, indent=2))

# 质量评分详细分析
quality_breakdown = manager.get_quality_score_breakdown(record)
print(f"质量评分详情: {quality_breakdown}")

# 性能分析
performance_stats = manager.get_performance_stats()
print(f"性能统计: {performance_stats}")
```

## 未来扩展计划

### 短期计划 (1-2周)
1. **运动数据源管理**：扩展到运动维度数据
2. **配置界面**：提供用户自定义优先级设置
3. **监控看板**：数据质量和处理性能监控

### 中期计划 (1个月)
1. **机器学习优化**：基于历史数据优化选择策略
2. **实时数据源**：支持实时数据流处理
3. **多设备协调**：跨设备数据一致性保证

### 长期计划 (3个月)
1. **全维度支持**：支持8个维度的数据源管理
2. **智能推荐**：推荐最佳数据采集方案
3. **数据质量预警**：自动识别和修复数据质量问题

## 相关文档

- [睡眠分析功能文档](../features/sleep-analysis.md)
- [积分百分比计算文档](../features/score-percentage.md)
- [LSP积分实现进度文档](../../../doc/LSP积分实现进度.md)

---

**版本**：v1.0  
**最后更新**：2025-09-07  
**维护者**：LSP开发团队