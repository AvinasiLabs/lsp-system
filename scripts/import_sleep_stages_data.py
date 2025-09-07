#!/usr/bin/env python
"""
导入睡眠阶段数据到数据库
用于测试睡眠阶段分析功能
"""

import sys
import os
import csv
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.postgresql import POSTGRES_POOL
from src.utils.logger import logger


def import_sleep_stages_from_csv():
    """从CSV文件导入睡眠阶段数据"""
    csv_file = '/Users/jojizhou/Documents/avinasi/lsp_system/data/data_30_20250709.csv'
    
    logger.info(f"开始从CSV导入睡眠阶段数据: {csv_file}")
    
    # 读取CSV文件
    sleep_records = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 只处理睡眠分析数据
            if row['type'] == 'HKCategoryTypeIdentifierSleepAnalysis':
                # 只处理Oura数据（有完整的睡眠阶段）
                if row['source_name'] in ['Oura', 'WHOOP']:
                    sleep_records.append(row)
    
    logger.info(f"找到 {len(sleep_records)} 条睡眠阶段记录")
    
    # 批量插入数据
    batch_size = 100
    inserted_count = 0
    
    for i in range(0, len(sleep_records), batch_size):
        batch = sleep_records[i:i+batch_size]
        
        for record in batch:
            try:
                # 准备数据
                data = {
                    'type': record['type'],
                    'source_name': record['source_name'],
                    'source_version': record['source_version'],
                    'unit': record['unit'],
                    'creation_date': record['creation_date'],
                    'start_date': record['start_date'],
                    'end_date': record['end_date'],
                    'value': record['value'],
                    'device': record.get('device', ''),
                    'user_id': 'default_user'  # 默认用户
                }
                
                # 插入数据
                POSTGRES_POOL.insert_data(
                    table_name='health_metric',
                    columns=['type', 'source_name', 'source_version', 'unit', 
                            'creation_date', 'start_date', 'end_date', 'value', 
                            'device', 'user_id'],
                    values=(data['type'], data['source_name'], data['source_version'],
                           data['unit'], data['creation_date'], data['start_date'],
                           data['end_date'], data['value'], data['device'], data['user_id']),
                    on_conflict='ON CONFLICT (type, start_date, end_date, user_id) DO NOTHING'
                )
                inserted_count += 1
                
            except Exception as e:
                logger.error(f"插入记录失败: {e}")
        
        logger.info(f"已插入 {inserted_count}/{len(sleep_records)} 条记录")
    
    logger.info(f"导入完成！共插入 {inserted_count} 条睡眠阶段记录")
    
    # 验证导入结果
    verify_imported_data()


def verify_imported_data():
    """验证导入的数据"""
    logger.info("\n验证导入的数据...")
    
    # 统计各数据源的记录数
    query = """
        SELECT source_name, COUNT(*) as count
        FROM health_metric
        WHERE type = 'HKCategoryTypeIdentifierSleepAnalysis'
        AND user_id = 'default_user'
        GROUP BY source_name
    """
    
    result = POSTGRES_POOL._execute_query(query)
    
    logger.info("数据源统计:")
    for row in result:
        logger.info(f"  {row[0]}: {row[1]} 条记录")
    
    # 统计睡眠阶段类型
    query = """
        SELECT value, COUNT(*) as count
        FROM health_metric
        WHERE type = 'HKCategoryTypeIdentifierSleepAnalysis'
        AND user_id = 'default_user'
        AND source_name = 'Oura'
        GROUP BY value
    """
    
    result = POSTGRES_POOL._execute_query(query)
    
    logger.info("\nOura睡眠阶段统计:")
    for row in result:
        stage = row[0].replace('HKCategoryValueSleepAnalysis', '')
        logger.info(f"  {stage}: {row[1]} 条记录")
    
    # 获取日期范围
    query = """
        SELECT MIN(DATE(start_date)), MAX(DATE(end_date))
        FROM health_metric
        WHERE type = 'HKCategoryTypeIdentifierSleepAnalysis'
        AND user_id = 'default_user'
    """
    
    result = POSTGRES_POOL._execute_query(query)
    if result and result[0]:
        logger.info(f"\n数据日期范围: {result[0][0]} 到 {result[0][1]}")


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("睡眠阶段数据导入工具")
    logger.info("=" * 60)
    
    try:
        import_sleep_stages_from_csv()
        logger.info("\n✓ 数据导入成功！现在可以运行测试脚本了")
        logger.info("  运行: python scripts/test_sleep_stages.py")
    except Exception as e:
        logger.error(f"✗ 导入失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()