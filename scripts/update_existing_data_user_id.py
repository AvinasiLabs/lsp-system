#!/usr/bin/env python3
"""
更新现有apple_healthkit数据的user_id字段
为所有user_id为NULL或'default_user'的记录设置特定的user_id
"""
import psycopg2
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.configs.global_config import POSTGRES_CONFIG


def update_user_ids(target_user_id="user_001"):
    """更新现有数据的user_id"""
    print(f"开始更新user_id为: {target_user_id}")
    
    conn = psycopg2.connect(
        dbname=POSTGRES_CONFIG.dbname,
        user=POSTGRES_CONFIG.user,
        password=POSTGRES_CONFIG.pwd.get_secret_value(),
        host=POSTGRES_CONFIG.host,
        port=POSTGRES_CONFIG.port
    )
    
    try:
        with conn.cursor() as cursor:
            # 首先检查当前user_id的分布
            print("\n检查当前user_id分布...")
            cursor.execute("""
                SELECT user_id, COUNT(*) as count
                FROM apple_healthkit
                GROUP BY user_id
                ORDER BY count DESC
            """)
            
            print(f"{'User ID':<20} {'记录数':<10}")
            print("-" * 30)
            for row in cursor.fetchall():
                user_id = row[0] if row[0] else 'NULL'
                print(f"{user_id:<20} {row[1]:<10}")
            
            # 更新默认用户的记录
            print(f"\n更新user_id为'default_user'或NULL的记录到'{target_user_id}'...")
            cursor.execute("""
                UPDATE apple_healthkit
                SET user_id = %s
                WHERE user_id = 'default_user' OR user_id IS NULL
            """, (target_user_id,))
            
            updated_count = cursor.rowcount
            print(f"✅ 更新了 {updated_count} 条记录")
            
            # 显示更新后的分布
            print("\n更新后的user_id分布:")
            cursor.execute("""
                SELECT user_id, COUNT(*) as count
                FROM apple_healthkit
                GROUP BY user_id
                ORDER BY count DESC
            """)
            
            print(f"{'User ID':<20} {'记录数':<10}")
            print("-" * 30)
            for row in cursor.fetchall():
                print(f"{row[0]:<20} {row[1]:<10}")
            
            conn.commit()
            print("\n✅ 更新成功!")
            
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def assign_user_ids_by_source():
    """根据source_name分配不同的user_id（可选功能）"""
    print("\n根据数据源分配user_id...")
    
    conn = psycopg2.connect(
        dbname=POSTGRES_CONFIG.dbname,
        user=POSTGRES_CONFIG.user,
        password=POSTGRES_CONFIG.pwd.get_secret_value(),
        host=POSTGRES_CONFIG.host,
        port=POSTGRES_CONFIG.port
    )
    
    try:
        with conn.cursor() as cursor:
            # 查看不同的数据源
            cursor.execute("""
                SELECT DISTINCT source_name, COUNT(*) as count
                FROM apple_healthkit
                WHERE source_name IS NOT NULL
                GROUP BY source_name
                ORDER BY count DESC
                LIMIT 10
            """)
            
            print(f"{'数据源':<50} {'记录数':<10}")
            print("-" * 60)
            sources = cursor.fetchall()
            for row in sources:
                print(f"{row[0]:<50} {row[1]:<10}")
            
            # 如果需要，可以根据source_name分配不同的user_id
            # 例如：
            # user_mappings = {
            #     'iPhone': 'user_001',
            #     'Apple Watch': 'user_002',
            # }
            # 
            # for source, user_id in user_mappings.items():
            #     cursor.execute("""
            #         UPDATE apple_healthkit
            #         SET user_id = %s
            #         WHERE source_name LIKE %s
            #     """, (user_id, f'%{source}%'))
            
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        conn.rollback()
    finally:
        conn.close()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='更新apple_healthkit表的user_id字段')
    parser.add_argument('--user-id', default='user_001', help='要设置的目标user_id (默认: user_001)')
    parser.add_argument('--by-source', action='store_true', help='显示按数据源分组的统计信息')
    
    args = parser.parse_args()
    
    try:
        # 更新user_id
        update_user_ids(args.user_id)
        
        # 如果需要，显示数据源信息
        if args.by_source:
            assign_user_ids_by_source()
        
        print("\n🎉 所有操作完成!")
        
    except Exception as e:
        print(f"\n操作过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()