# Issue #1: 实现积分持久化存储和过期机制

Issue Link: https://github.com/AvinasiLabs/lsp-system/issues/1

## 问题分析

### 当前状态
1. 积分计算已经实现，但只在内存中计算，未持久化
2. user_scores表已存在，但结构需要扩展
3. 现有字段：id, user_id, score_date, dimension, difficulty, score, details, created_at
4. 缺少过期相关字段和tier等级字段

### 需要实现
1. 扩展user_scores表结构
2. 创建积分持久化服务
3. 更新ScoreEngine自动保存积分
4. 实现积分查询API
5. 实现过期检查机制

## 实现计划

### Phase 1: 数据库迁移 (Step 1)
- 创建迁移脚本 `scripts/add_score_expiration_fields.py`
- 添加字段：expire_date, is_expired, tier_level, sub_category
- 注意：已有difficulty字段，不需要difficulty_level

### Phase 2: 积分持久化服务 (Step 2-3)
- 创建 `src/services/score_persistence_service.py`
  - save_daily_scores() - 保存每日积分
  - save_dimension_score() - 保存维度积分明细
  - calculate_expire_date() - 计算过期时间（默认6个月）
  - get_user_valid_scores() - 获取有效积分
  - get_user_score_history() - 获取积分历史
  - mark_expired_scores() - 标记过期积分

### Phase 3: 更新ScoreEngine (Step 4)
- 在calculate_daily_score()后自动调用持久化服务
- 保存总分和各维度详细积分

### Phase 4: 积分查询API (Step 5-6)
- 创建新的API端点在 `src/api/score_api.py`
  - GET /api/v1/scores/history - 积分历史
  - GET /api/v1/scores/valid - 当前有效积分
  - GET /api/v1/scores/expiring - 即将过期积分
  - POST /api/v1/scores/check-expiration - 手动触发过期检查

### Phase 5: 测试和文档 (Step 7-8)
- 创建测试脚本 `scripts/test_score_persistence.py`
- 更新API文档
- 更新实现进度文档

## 技术细节

### 过期时间计算
```python
def calculate_expire_date(score_date: datetime, tier_level: str = "Bronze") -> datetime:
    """根据tier等级计算过期时间"""
    expiration_months = {
        "Bronze": 6,      # 6个月
        "Silver": 8,      # 8个月  
        "Gold": 12,       # 12个月
        "Platinum": None, # 永不过期
        "Diamond": None,  # 永不过期
        "Ambassador": None # 永不过期
    }
    
    months = expiration_months.get(tier_level, 6)
    if months is None:
        return None  # 永不过期
    
    return score_date + timedelta(days=months * 30)
```

### 数据结构设计
```python
# 积分记录
{
    "user_id": "user_001",
    "score_date": "2025-07-18",
    "dimension": "sleep",
    "sub_category": "duration",  # 新增
    "difficulty": "easy",
    "score": 1000,
    "expire_date": "2026-01-18",  # 新增
    "is_expired": false,  # 新增
    "tier_level": "Bronze",  # 新增
    "details": {
        "sleep_hours": 7.8,
        "rule": "睡够7.5小时"
    }
}
```

## 预计工作量
- 总预计时间：4-5小时
- Phase 1: 30分钟
- Phase 2: 1.5小时
- Phase 3: 30分钟
- Phase 4: 1.5小时
- Phase 5: 1小时

## 注意事项
1. 保持向后兼容性
2. 所有时间使用UTC时区
3. 为未来Tier系统预留扩展性
4. 考虑大量数据的查询性能