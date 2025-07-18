#!/usr/bin/env python3
"""
添加积分过期相关字段的数据库迁移脚本
"""
import sys
import os
import psycopg2
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.configs.global_config import POSTGRES_CONFIG


def add_expiration_fields():
    """添加积分过期相关字段"""
    print("开始添加积分过期相关字段...")
    
    conn = psycopg2.connect(
        dbname=POSTGRES_CONFIG.dbname,
        user=POSTGRES_CONFIG.user,
        password=POSTGRES_CONFIG.pwd.get_secret_value(),
        host=POSTGRES_CONFIG.host,
        port=POSTGRES_CONFIG.port
    )
    
    try:
        with conn.cursor() as cursor:
            # 检查表是否存在
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'user_scores'
                )
            """)
            
            if not cursor.fetchone()[0]:
                print("❌ 错误: user_scores表不存在，请先运行add_user_id_migration.py")
                return False
            
            # 添加过期日期字段
            print("添加expire_date字段...")
            cursor.execute("""
                ALTER TABLE user_scores 
                ADD COLUMN IF NOT EXISTS expire_date TIMESTAMP WITH TIME ZONE
            """)
            
            # 添加是否过期标记
            print("添加is_expired字段...")
            cursor.execute("""
                ALTER TABLE user_scores 
                ADD COLUMN IF NOT EXISTS is_expired BOOLEAN DEFAULT FALSE
            """)
            
            # 添加用户等级字段
            print("添加tier_level字段...")
            cursor.execute("""
                ALTER TABLE user_scores 
                ADD COLUMN IF NOT EXISTS tier_level VARCHAR(20) DEFAULT 'Bronze'
            """)
            
            # 添加子类别字段（如sleep的duration, quality等）
            print("添加sub_category字段...")
            cursor.execute("""
                ALTER TABLE user_scores 
                ADD COLUMN IF NOT EXISTS sub_category VARCHAR(50)
            """)
            
            # 为已存在的记录设置默认过期时间（6个月后）
            print("为现有记录设置默认过期时间...")
            cursor.execute("""
                UPDATE user_scores 
                SET expire_date = created_at + INTERVAL '6 months'
                WHERE expire_date IS NULL
            """)
            
            # 创建过期日期索引
            print("创建过期日期索引...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_scores_expire_date 
                ON user_scores(expire_date) 
                WHERE is_expired = FALSE
            """)
            
            # 创建复合索引用于查询有效积分
            print("创建有效积分查询索引...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_scores_valid 
                ON user_scores(user_id, is_expired, expire_date)
            """)
            
            conn.commit()
            print("✅ 积分过期字段添加成功!")
            
            # 显示更新后的表结构
            cursor.execute("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns
                WHERE table_name = 'user_scores'
                ORDER BY ordinal_position
            """)
            
            print("\n更新后的user_scores表结构:")
            for col in cursor.fetchall():
                print(f"  {col[0]}: {col[1]} {f'(默认: {col[2]})' if col[2] else ''}")
                
            return True
            
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def update_existing_scores():
    """更新现有积分记录的sub_category"""
    print("\n更新现有积分记录的sub_category...")
    
    conn = psycopg2.connect(
        dbname=POSTGRES_CONFIG.dbname,
        user=POSTGRES_CONFIG.user,
        password=POSTGRES_CONFIG.pwd.get_secret_value(),
        host=POSTGRES_CONFIG.host,
        port=POSTGRES_CONFIG.port
    )
    
    try:
        with conn.cursor() as cursor:
            # 根据dimension设置默认的sub_category
            updates = [
                ("sleep", "duration"),
                ("exercise", "steps"),
                ("diet", "water"),
                ("mental", "hrv")
            ]
            
            for dimension, sub_category in updates:
                cursor.execute("""
                    UPDATE user_scores 
                    SET sub_category = %s
                    WHERE dimension = %s AND sub_category IS NULL
                """, (sub_category, dimension))
                
                print(f"  更新{dimension}维度: {cursor.rowcount}条记录")
            
            conn.commit()
            print("✅ 现有记录更新完成!")
            
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        conn.rollback()
    finally:
        conn.close()


def check_migration_status():
    """检查迁移状态"""
    print("\n检查迁移状态...")
    
    conn = psycopg2.connect(
        dbname=POSTGRES_CONFIG.dbname,
        user=POSTGRES_CONFIG.user,
        password=POSTGRES_CONFIG.pwd.get_secret_value(),
        host=POSTGRES_CONFIG.host,
        port=POSTGRES_CONFIG.port
    )
    
    try:
        with conn.cursor() as cursor:
            # 统计积分记录
            cursor.execute("SELECT COUNT(*) FROM user_scores")
            total_count = cursor.fetchone()[0]
            
            # 统计有过期时间的记录
            cursor.execute("SELECT COUNT(*) FROM user_scores WHERE expire_date IS NOT NULL")
            with_expire = cursor.fetchone()[0]
            
            # 统计已过期的记录
            cursor.execute("SELECT COUNT(*) FROM user_scores WHERE expire_date < NOW()")
            expired = cursor.fetchone()[0]
            
            print(f"\n积分记录统计:")
            print(f"  总记录数: {total_count}")
            print(f"  有过期时间: {with_expire}")
            print(f"  已过期: {expired}")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
    finally:
        conn.close()


def main():
    """主函数"""
    try:
        # 添加过期字段
        if add_expiration_fields():
            # 更新现有记录
            update_existing_scores()
            # 检查迁移状态
            check_migration_status()
        
    except Exception as e:
        print(f"\n迁移过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()