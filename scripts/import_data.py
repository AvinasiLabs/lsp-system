#!/usr/bin/env python3
"""
导入SQL dump文件到PostgreSQL数据库
"""
import psycopg2
from configs.global_config import POSTGRES_CONFIG
import re

def import_sql_dump(filename):
    """导入SQL dump文件"""
    # 连接数据库
    conn = psycopg2.connect(
        dbname=POSTGRES_CONFIG.dbname,
        user=POSTGRES_CONFIG.user,
        password=POSTGRES_CONFIG.pwd.get_secret_value(),
        host=POSTGRES_CONFIG.host,
        port=POSTGRES_CONFIG.port
    )
    
    try:
        with conn.cursor() as cursor:
            # 读取SQL文件
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分割SQL语句
            statements = content.split(';\n')
            
            # 跳过表创建语句（因为表已存在）
            skip_patterns = [
                r'^CREATE TABLE',
                r'^CREATE SEQUENCE',
                r'^ALTER SEQUENCE',
                r'^ALTER TABLE.*OWNER TO'
            ]
            
            copy_mode = False
            copy_data = []
            current_table = None
            
            for statement in statements:
                statement = statement.strip()
                if not statement:
                    continue
                
                # 检查是否需要跳过
                if any(re.match(pattern, statement, re.IGNORECASE) for pattern in skip_patterns):
                    print(f"跳过: {statement[:50]}...")
                    continue
                
                # 处理COPY命令
                if statement.startswith('COPY'):
                    match = re.match(r'COPY\s+public\.(\w+)\s*\((.*?)\)\s+FROM\s+stdin', statement)
                    if match:
                        current_table = match.group(1)
                        columns = match.group(2)
                        print(f"\n开始导入表 {current_table}...")
                        copy_mode = True
                        copy_data = []
                    continue
                
                # 在COPY模式下收集数据
                if copy_mode:
                    if statement == '\\.':
                        # COPY数据结束
                        print(f"导入 {len(copy_data)} 条数据到 {current_table}...")
                        if copy_data and current_table == 'apple_healthkit':
                            # 批量插入数据
                            for line in copy_data:
                                parts = line.split('\t')
                                if len(parts) == 10:  # 确保有正确的列数
                                    try:
                                        cursor.execute("""
                                            INSERT INTO apple_healthkit 
                                            (id, type, source_name, source_version, unit, 
                                             creation_date, start_date, end_date, value, created_at)
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                        """, parts)
                                    except Exception as e:
                                        print(f"插入失败: {e}, 数据: {parts[0]}")
                        copy_mode = False
                        copy_data = []
                        current_table = None
                    else:
                        # 收集COPY数据行
                        copy_data.extend(statement.split('\n'))
                    continue
                
                # 执行其他SQL语句
                try:
                    if statement:
                        cursor.execute(statement + ';')
                except Exception as e:
                    print(f"执行失败: {e}\n语句: {statement[:100]}...")
            
            # 提交事务
            conn.commit()
            print("\n数据导入完成!")
            
            # 检查导入结果
            cursor.execute("SELECT COUNT(*) FROM apple_healthkit")
            count = cursor.fetchone()[0]
            print(f"apple_healthkit 表中现有 {count} 条记录")
            
            cursor.execute("SELECT COUNT(*) FROM intermediate_data")
            count = cursor.fetchone()[0]
            print(f"intermediate_data 表中现有 {count} 条记录")
            
    except Exception as e:
        print(f"导入过程中发生错误: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    import_sql_dump("/Users/longevitygo/Documents/avinasi/lsp_system/sponge_no_perms.sql")