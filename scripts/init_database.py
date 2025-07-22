#!/usr/bin/env python3
"""
数据库初始化脚本
用于部署时创建必要的数据库表
"""
import psycopg2
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.configs.global_config import POSTGRES_CONFIG


def init_database():
    """初始化数据库表结构"""
    print("开始初始化数据库...")
    print(f"数据库: {POSTGRES_CONFIG.dbname}")
    print(f"主机: {POSTGRES_CONFIG.host}:{POSTGRES_CONFIG.port}")
    
    # 读取SQL脚本
    sql_file = Path(__file__).parent / "create_tables.sql"
    if not sql_file.exists():
        print(f"❌ 错误: SQL脚本文件不存在: {sql_file}")
        return False
    
    try:
        # 连接数据库
        conn = psycopg2.connect(
            dbname=POSTGRES_CONFIG.dbname,
            user=POSTGRES_CONFIG.user,
            password=POSTGRES_CONFIG.pwd.get_secret_value(),
            host=POSTGRES_CONFIG.host,
            port=POSTGRES_CONFIG.port
        )
        
        with conn.cursor() as cursor:
            # 执行SQL脚本
            print("\n执行建表脚本...")
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
                cursor.execute(sql_content)
            
            conn.commit()
            print("✅ 数据库表创建成功!")
            
            # 验证表创建
            print("\n验证表结构...")
            tables = ['users', 'user_scores']
            for table in tables:
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_name = '{table}'
                """)
                exists = cursor.fetchone()[0] > 0
                if exists:
                    # 获取表的列数
                    cursor.execute(f"""
                        SELECT COUNT(*) 
                        FROM information_schema.columns 
                        WHERE table_name = '{table}'
                    """)
                    col_count = cursor.fetchone()[0]
                    
                    # 获取记录数
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]
                    
                    print(f"  ✅ {table}: {col_count} 列, {row_count} 条记录")
                else:
                    print(f"  ❌ {table}: 未创建")
            
            # 显示索引信息
            print("\n索引信息:")
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'user_scores' 
                ORDER BY indexname
            """)
            indexes = cursor.fetchall()
            for idx in indexes:
                print(f"  - {idx[0]}")
            
            return True
            
    except psycopg2.Error as e:
        print(f"\n❌ 数据库错误: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        return False
    finally:
        if conn:
            conn.close()


def check_connection():
    """检查数据库连接"""
    print("检查数据库连接...")
    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_CONFIG.dbname,
            user=POSTGRES_CONFIG.user,
            password=POSTGRES_CONFIG.pwd.get_secret_value(),
            host=POSTGRES_CONFIG.host,
            port=POSTGRES_CONFIG.port
        )
        conn.close()
        print("✅ 数据库连接成功!")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def main():
    """主函数"""
    print("LSP积分系统 - 数据库初始化")
    print("=" * 50)
    
    # 检查连接
    if not check_connection():
        print("\n请检查数据库配置和网络连接")
        sys.exit(1)
    
    # 初始化数据库
    if init_database():
        print("\n🎉 数据库初始化完成!")
        print("\n下一步:")
        print("1. 启动API服务: python start_server.py")
        print("2. 访问文档: http://localhost:8000/lsp/docs")
    else:
        print("\n数据库初始化失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()