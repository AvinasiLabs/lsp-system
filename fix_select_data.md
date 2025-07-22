# 修复 "获取有效积分失败" 错误

## 问题描述
`POSTGRES_POOL.select_data()` 返回元组列表，但代码期望字典列表。

## 修复方案

### 方案1：修改 postgresql.py 中的 select_data 方法

在 `src/db/postgresql.py` 中找到 `select_data` 方法，修改为返回字典：

```python
def select_data(self, table_name, conditions=None, params=None):
    """查询数据"""
    conn = self.get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # 使用DictCursor
    # ... 其余代码不变
```

### 方案2：修改 score_persistence_service.py

修改 `get_user_valid_scores` 方法，手动处理元组：

```python
# 在 get_user_valid_scores 方法中
for record in data:
    # 如果是元组，手动解析
    if isinstance(record, tuple):
        # 根据表结构解析
        # (id, user_id, score_date, dimension, difficulty, score, details, created_at, expire_date, is_expired, tier_level, sub_category)
        dimension = record[3]  # dimension是第4个字段
        score = record[5]      # score是第6个字段
    else:
        dimension = record['dimension']
        score = record['score']
```

### 方案3：创建兼容层

创建一个辅助函数来转换元组为字典：

```python
def tuple_to_dict(record, columns):
    """将元组转换为字典"""
    return dict(zip(columns, record))

# 使用时
columns = ['id', 'user_id', 'score_date', 'dimension', 'difficulty', 'score', 
          'details', 'created_at', 'expire_date', 'is_expired', 'tier_level', 'sub_category']
          
for record in data:
    if isinstance(record, tuple):
        record = tuple_to_dict(record, columns)
    # 现在可以安全使用 record['dimension']
```

## 推荐方案

建议使用**方案1**，在 `postgresql.py` 中添加 `psycopg2.extras.DictCursor`，这样所有查询都会返回字典格式，不需要修改其他代码。

## 验证修复

修复后，运行以下命令验证：

```bash
curl "http://your-server:12002/lsp/api/v1/scores/valid?user_id=user_001"
```

应该返回正确的积分数据而不是错误。