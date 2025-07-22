#!/usr/bin/env python3
"""
快速诊断user_scores表问题
"""
from src.db.postgresql import POSTGRES_POOL

def quick_check():
    print("=== 快速诊断 ===\n")
    
    conn = POSTGRES_POOL.get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. 检查表存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'user_scores'
            )
        """)
        exists = cursor.fetchone()[0]
        print(f"1. user_scores表存在: {exists}")
        
        if not exists:
            print("\n✗ 表不存在！需要创建表。")
            print("运行: python scripts/init_lsp_tables.py")
            return
        
        # 2. 检查表结构
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'user_scores'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print("\n2. 表结构:")
        for col_name, col_type in columns:
            print(f"   - {col_name} ({col_type})")
        
        # 3. 检查数据
        cursor.execute("SELECT COUNT(*) FROM user_scores")
        total_count = cursor.fetchone()[0]
        print(f"\n3. 总记录数: {total_count}")
        
        cursor.execute("SELECT COUNT(*) FROM user_scores WHERE user_id = 'user_001'")
        user_count = cursor.fetchone()[0]
        print(f"   user_001记录数: {user_count}")
        
        # 4. 检查问题查询
        print("\n4. 测试问题查询:")
        try:
            cursor.execute("""
                SELECT * FROM user_scores
                WHERE user_id = 'user_001' 
                AND is_expired = FALSE 
                AND (expire_date IS NULL OR expire_date > NOW())
                AND dimension != 'total'
                LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                print("   ✓ 查询成功")
            else:
                print("   ⚠️  查询成功但无数据")
        except Exception as e:
            print(f"   ✗ 查询失败: {e}")
            print(f"   错误类型: {type(e).__name__}")
            
        # 5. 检查is_expired列
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'user_scores' 
            AND column_name = 'is_expired'
        """)
        has_is_expired = cursor.fetchone()[0] > 0
        print(f"\n5. is_expired列存在: {has_is_expired}")
        
        if not has_is_expired:
            print("   ✗ 缺少is_expired列！")
            print("   运行: python scripts/add_score_expiration_fields.py")
            
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    quick_check()