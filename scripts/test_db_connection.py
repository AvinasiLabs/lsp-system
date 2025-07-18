#!/usr/bin/env python3
"""
测试PostgreSQL数据库连接并查看数据结构
"""
import sys
from postgresql import POSTGRES_POOL
import psycopg2

def test_connection():
    """测试数据库连接"""
    print("正在测试数据库连接...")
    conn = POSTGRES_POOL.get_connection()
    if conn:
        print("✅ 数据库连接成功!")
        POSTGRES_POOL.put_connection(conn)
        return True
    else:
        print("❌ 数据库连接失败!")
        return False

def list_tables():
    """列出所有表"""
    print("\n正在查询数据库中的表...")
    conn = POSTGRES_POOL.get_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cursor:
            # 查询所有用户表
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            print(f"\n发现 {len(tables)} 个表:")
            for table in tables:
                print(f"  - {table[0]}")
            
            return [table[0] for table in tables]
    except Exception as e:
        print(f"查询表失败: {e}")
        return []
    finally:
        POSTGRES_POOL.put_connection(conn)

def describe_table(table_name):
    """描述表结构"""
    print(f"\n表 '{table_name}' 的结构:")
    conn = POSTGRES_POOL.get_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cursor:
            # 查询列信息
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            
            columns = cursor.fetchall()
            
            print(f"{'列名':<30} {'数据类型':<20} {'可空':<10} {'默认值':<20}")
            print("-" * 80)
            for col in columns:
                col_name = col[0]
                data_type = col[1]
                if col[2]:  # character_maximum_length
                    data_type = f"{data_type}({col[2]})"
                is_nullable = "是" if col[3] == 'YES' else "否"
                default_val = col[4] if col[4] else "无"
                
                print(f"{col_name:<30} {data_type:<20} {is_nullable:<10} {str(default_val):<20}")
    except Exception as e:
        print(f"查询表结构失败: {e}")
    finally:
        POSTGRES_POOL.put_connection(conn)

def sample_data(table_name, limit=5):
    """查看表中的样本数据"""
    print(f"\n表 '{table_name}' 的前 {limit} 条数据:")
    conn = POSTGRES_POOL.get_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cursor:
            # 先获取总行数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"总行数: {count}")
            
            # 获取样本数据
            cursor.execute(f"SELECT * FROM {table_name} LIMIT %s;", (limit,))
            rows = cursor.fetchall()
            
            if rows:
                # 获取列名
                column_names = [desc[0] for desc in cursor.description]
                print(f"\n列: {', '.join(column_names)}")
                print("-" * 80)
                
                for row in rows:
                    print(row)
            else:
                print("表中没有数据")
    except Exception as e:
        print(f"查询数据失败: {e}")
    finally:
        POSTGRES_POOL.put_connection(conn)

def main():
    """主函数"""
    print("=== PostgreSQL 数据库探索工具 ===\n")
    
    # 测试连接
    if not test_connection():
        sys.exit(1)
    
    # 列出所有表
    tables = list_tables()
    
    if not tables:
        print("\n数据库中没有找到任何表")
        return
    
    # 对每个表显示结构和样本数据
    for table in tables:
        print(f"\n{'='*80}")
        describe_table(table)
        sample_data(table)
    
    print(f"\n{'='*80}")
    print("数据库探索完成!")

if __name__ == "__main__":
    main()