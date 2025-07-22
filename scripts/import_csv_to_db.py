#!/usr/bin/env python3
"""
创建health_metric表并从CSV文件导入数据
"""
import pandas as pd
import psycopg2
from postgresql import POSTGRES_POOL
from configs.global_config import POSTGRES_CONFIG
from datetime import datetime

def create_table():
    """创建health_metric表"""
    print("创建health_metric表...")
    
    conn = psycopg2.connect(
        dbname=POSTGRES_CONFIG.dbname,
        user=POSTGRES_CONFIG.user,
        password=POSTGRES_CONFIG.pwd.get_secret_value(),
        host=POSTGRES_CONFIG.host,
        port=POSTGRES_CONFIG.port
    )
    
    try:
        with conn.cursor() as cursor:
            # 创建表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS health_metric (
                    id SERIAL PRIMARY KEY,
                    type VARCHAR(255) NOT NULL,
                    source_name VARCHAR(255),
                    source_version VARCHAR(50),
                    unit VARCHAR(50),
                    creation_date TIMESTAMP WITH TIME ZONE,
                    start_date TIMESTAMP WITH TIME ZONE,
                    end_date TIMESTAMP WITH TIME ZONE,
                    value VARCHAR(255),
                    device VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # 创建索引以提高查询性能
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON health_metric(type);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_start_date ON health_metric(start_date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_end_date ON health_metric(end_date);")
            
            conn.commit()
            print("✅ 表创建成功!")
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        conn.rollback()
    finally:
        conn.close()

def import_csv_data(csv_file):
    """导入CSV数据到数据库"""
    print(f"\n读取CSV文件: {csv_file}")
    
    # 读取CSV文件
    df = pd.read_csv(csv_file)
    print(f"发现 {len(df)} 条记录")
    
    # 查看数据结构
    print("\n数据列:", df.columns.tolist())
    print("\n前5行数据:")
    print(df.head())
    
    # 处理空值
    df = df.where(pd.notnull(df), None)
    
    conn = psycopg2.connect(
        dbname=POSTGRES_CONFIG.dbname,
        user=POSTGRES_CONFIG.user,
        password=POSTGRES_CONFIG.pwd.get_secret_value(),
        host=POSTGRES_CONFIG.host,
        port=POSTGRES_CONFIG.port
    )
    
    try:
        with conn.cursor() as cursor:
            # 准备数据批量插入
            print("\n开始导入数据...")
            
            # 批量插入，每批1000条
            batch_size = 1000
            total_inserted = 0
            
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                
                # 准备插入数据
                values = []
                for _, row in batch.iterrows():
                    values.append((
                        row['type'],
                        row['source_name'] if pd.notna(row['source_name']) else None,
                        row['source_version'] if pd.notna(row['source_version']) else None,
                        row['unit'] if pd.notna(row['unit']) else None,
                        row['creation_date'] if pd.notna(row['creation_date']) else None,
                        row['start_date'] if pd.notna(row['start_date']) else None,
                        row['end_date'] if pd.notna(row['end_date']) else None,
                        str(row['value']) if pd.notna(row['value']) else None,
                        row['device'] if pd.notna(row['device']) else None
                    ))
                
                # 批量插入
                cursor.executemany("""
                    INSERT INTO health_metric 
                    (type, source_name, source_version, unit, creation_date, 
                     start_date, end_date, value, device)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, values)
                
                total_inserted += len(values)
                print(f"已导入 {total_inserted}/{len(df)} 条记录...")
            
            conn.commit()
            print(f"\n✅ 成功导入 {total_inserted} 条记录!")
            
            # 验证导入结果
            cursor.execute("SELECT COUNT(*) FROM health_metric;")
            count = cursor.fetchone()[0]
            print(f"数据库中现有 {count} 条记录")
            
            # 显示数据类型统计
            cursor.execute("""
                SELECT type, COUNT(*) as count 
                FROM health_metric 
                GROUP BY type 
                ORDER BY count DESC 
                LIMIT 10;
            """)
            
            print("\n数据类型统计 (前10种):")
            print(f"{'数据类型':<50} {'记录数':<10}")
            print("-" * 60)
            for row in cursor.fetchall():
                print(f"{row[0]:<50} {row[1]:<10}")
                
    except Exception as e:
        print(f"❌ 导入数据失败: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """主函数"""
    # 创建表
    create_table()
    
    # 导入CSV数据
    csv_file = "/Users/longevitygo/Documents/avinasi/lsp_system/data_30_20250709.csv"
    import_csv_data(csv_file)

if __name__ == "__main__":
    main()