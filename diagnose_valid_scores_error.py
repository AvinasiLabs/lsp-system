#!/usr/bin/env python3
"""
诊断"获取有效积分失败"错误
"""
import traceback
from datetime import datetime
from src.db.postgresql import POSTGRES_POOL
from src.services.score_persistence_service import ScorePersistenceService

def diagnose_error():
    print("=== 诊断'获取有效积分失败'错误 ===\n")
    
    # 1. 检查user_scores表是否存在
    print("1. 检查user_scores表:")
    try:
        result = POSTGRES_POOL.select_data(
            table_name='information_schema.tables',
            conditions="table_name = 'user_scores'"
        )
        if result:
            print("   ✓ user_scores表存在")
        else:
            print("   ✗ user_scores表不存在！")
            print("   需要运行: python scripts/init_lsp_tables.py")
            return
    except Exception as e:
        print(f"   错误: {e}")
        return
    
    # 2. 检查表结构
    print("\n2. 检查user_scores表结构:")
    try:
        columns = POSTGRES_POOL.select_data(
            table_name='information_schema.columns',
            conditions="table_name = 'user_scores' ORDER BY ordinal_position"
        )
        print("   列名:")
        required_columns = ['user_id', 'score_date', 'dimension', 'score', 'is_expired', 'expire_date']
        missing_columns = []
        
        column_names = [col['column_name'] for col in columns] if columns else []
        for col in required_columns:
            if col in column_names:
                print(f"   ✓ {col}")
            else:
                print(f"   ✗ {col} (缺失)")
                missing_columns.append(col)
        
        if missing_columns:
            print(f"\n   缺失列: {missing_columns}")
            print("   需要运行数据库迁移脚本")
    except Exception as e:
        print(f"   错误: {e}")
        return
    
    # 3. 检查是否有数据
    print("\n3. 检查user_scores表数据:")
    try:
        # 检查总记录数
        all_records = POSTGRES_POOL.select_data(
            table_name='user_scores',
            conditions="1=1 LIMIT 10"
        )
        print(f"   总记录数(前10条): {len(all_records) if all_records else 0}")
        
        # 检查user_001的数据
        user_records = POSTGRES_POOL.select_data(
            table_name='user_scores',
            conditions="user_id = 'user_001' LIMIT 5"
        )
        print(f"   user_001的记录数: {len(user_records) if user_records else 0}")
        
    except Exception as e:
        print(f"   错误: {e}")
    
    # 4. 尝试直接调用get_user_valid_scores
    print("\n4. 测试get_user_valid_scores函数:")
    try:
        service = ScorePersistenceService()
        result = service.get_user_valid_scores('user_001', datetime.now())
        
        if 'error' in result:
            print(f"   ✗ 函数返回错误: {result['error']}")
        else:
            print(f"   ✓ 函数执行成功")
            print(f"   有效积分: {result['total_valid_score']}")
    except Exception as e:
        print(f"   ✗ 发生异常: {e}")
        print(f"   详细错误:\n{traceback.format_exc()}")
    
    # 5. 测试原始SQL查询
    print("\n5. 测试原始SQL查询:")
    try:
        conn = POSTGRES_POOL.get_connection()
        cursor = conn.cursor()
        
        # 测试基本查询
        cursor.execute("""
            SELECT COUNT(*) FROM user_scores 
            WHERE user_id = 'user_001' 
            AND is_expired = FALSE
        """)
        count = cursor.fetchone()[0]
        print(f"   user_001的未过期记录数: {count}")
        
        # 测试完整查询
        cursor.execute("""
            SELECT * FROM user_scores
            WHERE user_id = 'user_001' 
            AND is_expired = FALSE 
            AND (expire_date IS NULL OR expire_date > %s)
            AND dimension != 'total'
            LIMIT 5
        """, (datetime.now(),))
        
        records = cursor.fetchall()
        print(f"   查询成功，返回{len(records)}条记录")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"   ✗ SQL查询失败: {e}")
        print(f"   这可能是问题的根源！")
        
    # 6. 建议的解决方案
    print("\n6. 可能的解决方案:")
    print("   a) 如果表不存在: python scripts/init_lsp_tables.py")
    print("   b) 如果缺少列: python scripts/add_score_expiration_fields.py")
    print("   c) 如果没有数据: 先运行积分计算接口生成数据")
    print("   d) 如果是数据类型问题: 检查数据库字段类型是否正确")

if __name__ == "__main__":
    diagnose_error()