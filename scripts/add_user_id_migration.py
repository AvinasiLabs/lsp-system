#!/usr/bin/env python3
"""
数据库迁移：添加user_id字段
"""
import psycopg2
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.configs.global_config import POSTGRES_CONFIG


def add_user_id_column():
    """添加user_id字段到health_metric表"""
    print("开始数据库迁移：添加user_id字段")
    
    conn = psycopg2.connect(
        dbname=POSTGRES_CONFIG.dbname,
        user=POSTGRES_CONFIG.user,
        password=POSTGRES_CONFIG.pwd.get_secret_value(),
        host=POSTGRES_CONFIG.host,
        port=POSTGRES_CONFIG.port
    )
    
    try:
        with conn.cursor() as cursor:
            # 检查字段是否已存在
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'health_metric' 
                AND column_name = 'user_id'
            """)
            
            if cursor.fetchone():
                print("user_id字段已存在，跳过迁移")
                return
            
            # 添加user_id字段
            print("添加user_id字段...")
            cursor.execute("""
                ALTER TABLE health_metric 
                ADD COLUMN user_id VARCHAR(255) DEFAULT 'default_user'
            """)
            
            # 创建索引以提高查询性能
            print("创建user_id索引...")
            cursor.execute("""
                CREATE INDEX idx_user_id ON health_metric(user_id)
            """)
            
            # 创建复合索引用于用户+日期查询
            print("创建复合索引...")
            cursor.execute("""
                CREATE INDEX idx_user_date ON health_metric(user_id, start_date)
            """)
            
            conn.commit()
            print("✅ 迁移成功完成!")
            
            # 验证迁移结果
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'health_metric' 
                AND column_name = 'user_id'
            """)
            
            result = cursor.fetchone()
            if result:
                print(f"字段信息: {result[0]} - {result[1]}")
            
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def create_user_score_table():
    """创建用户积分记录表"""
    print("\n创建用户积分记录表...")
    
    conn = psycopg2.connect(
        dbname=POSTGRES_CONFIG.dbname,
        user=POSTGRES_CONFIG.user,
        password=POSTGRES_CONFIG.pwd.get_secret_value(),
        host=POSTGRES_CONFIG.host,
        port=POSTGRES_CONFIG.port
    )
    
    try:
        with conn.cursor() as cursor:
            # 创建用户积分记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_scores (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    score_date DATE NOT NULL,
                    dimension VARCHAR(50) NOT NULL,
                    difficulty VARCHAR(20) NOT NULL,
                    score INTEGER NOT NULL,
                    details JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, score_date, dimension, difficulty)
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_scores_user_id ON user_scores(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_scores_date ON user_scores(score_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_scores_user_date ON user_scores(user_id, score_date)")
            
            # 创建用户信息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id VARCHAR(255) PRIMARY KEY,
                    username VARCHAR(255),
                    email VARCHAR(255),
                    level VARCHAR(20) DEFAULT 'BRONZE',
                    total_points INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("✅ 用户相关表创建成功!")
            
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    """主函数"""
    try:
        # 添加user_id字段
        add_user_id_column()
        
        # 创建用户相关表
        create_user_score_table()
        
        print("\n🎉 所有迁移完成!")
        
    except Exception as e:
        print(f"\n迁移过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()