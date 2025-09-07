#!/usr/bin/env python
"""
测试所有睡眠数据源的解析能力
包括Oura、WHOOP、OffScreen和Apple Watch（如果有）
"""

import csv
from datetime import datetime, timedelta, time
from typing import Dict, List
from collections import defaultdict


def analyze_all_sleep_sources():
    """分析CSV中所有的睡眠数据源"""
    csv_file = '/Users/jojizhou/Documents/avinasi/lsp_system/data/data_30_20250709.csv'
    
    print("\n" + "=" * 70)
    print("分析CSV文件中的所有睡眠数据源")
    print("=" * 70)
    
    # 统计各种数据
    sleep_sources = defaultdict(int)
    apple_watch_data_types = defaultdict(int)
    sleep_stages_by_source = defaultdict(lambda: defaultdict(int))
    date_ranges_by_source = defaultdict(lambda: {'min': None, 'max': None})
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            source = row['source_name']
            data_type = row['type']
            
            # 统计Apple Watch的数据类型
            if 'Apple Watch' in source:
                apple_watch_data_types[data_type] += 1
            
            # 统计睡眠分析数据
            if data_type == 'HKCategoryTypeIdentifierSleepAnalysis':
                sleep_sources[source] += 1
                
                # 统计睡眠阶段
                stage = row['value'].replace('HKCategoryValueSleepAnalysis', '')
                sleep_stages_by_source[source][stage] += 1
                
                # 记录日期范围
                try:
                    date_str = row['start_date'].split(' ')[0]
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    if date_ranges_by_source[source]['min'] is None:
                        date_ranges_by_source[source]['min'] = date_obj
                        date_ranges_by_source[source]['max'] = date_obj
                    else:
                        date_ranges_by_source[source]['min'] = min(date_ranges_by_source[source]['min'], date_obj)
                        date_ranges_by_source[source]['max'] = max(date_ranges_by_source[source]['max'], date_obj)
                except:
                    pass
    
    # 打印结果
    print("\n1. 睡眠数据源统计:")
    print("-" * 50)
    for source, count in sleep_sources.items():
        date_range = date_ranges_by_source[source]
        if date_range['min'] and date_range['max']:
            print(f"  {source}: {count} 条记录")
            print(f"    日期范围: {date_range['min'].date()} 到 {date_range['max'].date()}")
            print(f"    睡眠阶段类型:")
            for stage, stage_count in sleep_stages_by_source[source].items():
                print(f"      - {stage}: {stage_count} 条")
    
    print("\n2. Apple Watch数据类型统计:")
    print("-" * 50)
    if apple_watch_data_types:
        # 检查是否有睡眠相关数据
        sleep_related = [k for k in apple_watch_data_types.keys() if 'Sleep' in k]
        if sleep_related:
            print("  睡眠相关数据类型:")
            for dtype in sleep_related:
                print(f"    - {dtype}: {apple_watch_data_types[dtype]} 条")
        else:
            print("  ⚠️ Apple Watch数据中没有找到睡眠分析数据")
            print("  Apple Watch只有以下数据类型:")
            top_types = sorted(apple_watch_data_types.items(), key=lambda x: x[1], reverse=True)[:10]
            for dtype, count in top_types:
                short_name = dtype.replace('HKQuantityTypeIdentifier', '').replace('HKCategoryTypeIdentifier', '')
                print(f"    - {short_name}: {count} 条")
    else:
        print("  未找到Apple Watch数据")
    
    return sleep_sources, sleep_stages_by_source


def test_sleep_analysis_by_source(source_name: str):
    """测试特定数据源的睡眠分析"""
    csv_file = '/Users/jojizhou/Documents/avinasi/lsp_system/data/data_30_20250709.csv'
    
    print(f"\n" + "=" * 70)
    print(f"测试 {source_name} 数据源的睡眠分析")
    print("=" * 70)
    
    # 睡眠阶段映射
    SLEEP_STAGE_MAPPING = {
        'HKCategoryValueSleepAnalysisAwake': 'awake',
        'HKCategoryValueSleepAnalysisAsleepCore': 'core',
        'HKCategoryValueSleepAnalysisAsleepDeep': 'deep',
        'HKCategoryValueSleepAnalysisAsleepREM': 'rem',
        'HKCategoryValueSleepAnalysisInBed': 'in_bed',
        'HKCategoryValueSleepAnalysisAsleepUnspecified': 'unspecified'
    }
    
    # 加载该数据源的数据
    sleep_records = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row['type'] == 'HKCategoryTypeIdentifierSleepAnalysis' and 
                row['source_name'] == source_name):
                sleep_records.append(row)
    
    if not sleep_records:
        print(f"  未找到 {source_name} 的睡眠数据")
        return
    
    print(f"  找到 {len(sleep_records)} 条记录")
    
    # 分析第一晚的数据作为示例
    # 按日期分组
    nights = defaultdict(list)
    for record in sleep_records:
        try:
            start_str = record['start_date'].split('+')[0]
            start_time = datetime.fromisoformat(start_str)
            # 使用开始时间的日期作为分组键
            night_key = start_time.date() if start_time.hour >= 12 else (start_time - timedelta(days=1)).date()
            nights[night_key].append({
                'start': start_time,
                'end': datetime.fromisoformat(record['end_date'].split('+')[0]),
                'stage': SLEEP_STAGE_MAPPING.get(record['value'], 'unknown'),
                'raw_value': record['value']
            })
        except:
            continue
    
    # 分析第一晚
    if nights:
        first_night = sorted(nights.keys())[0]
        night_data = sorted(nights[first_night], key=lambda x: x['start'])
        
        print(f"\n  示例分析：{first_night} 晚的睡眠")
        print("  " + "-" * 40)
        
        # 统计各阶段时长
        stages_duration = defaultdict(float)
        for record in night_data:
            duration_minutes = (record['end'] - record['start']).total_seconds() / 60
            stages_duration[record['stage']] += duration_minutes
        
        # 计算总睡眠时长
        total_sleep_minutes = sum([v for k, v in stages_duration.items() if k not in ['awake', 'in_bed']])
        
        print(f"  入睡时间: {night_data[0]['start'].strftime('%H:%M')}")
        print(f"  起床时间: {night_data[-1]['end'].strftime('%H:%M')}")
        print(f"  总睡眠时长: {total_sleep_minutes/60:.2f} 小时")
        
        print(f"\n  各阶段时长:")
        for stage, minutes in stages_duration.items():
            print(f"    {stage}: {minutes/60:.2f} 小时 ({minutes:.0f} 分钟)")
        
        # 判断数据质量
        print(f"\n  数据质量评估:")
        if 'deep' in stages_duration and 'rem' in stages_duration:
            print(f"    ✓ 包含详细睡眠阶段（深度睡眠、REM睡眠）")
            print(f"    → 可以计算中级别积分")
        elif 'unspecified' in stages_duration:
            print(f"    ⚠️ 只有未指定的睡眠数据")
            print(f"    → 只能计算易级别积分（总睡眠时长）")
        else:
            print(f"    ℹ️ 包含以下阶段: {', '.join(stages_duration.keys())}")


def compare_data_sources():
    """比较不同数据源的能力"""
    print("\n" + "=" * 70)
    print("数据源能力对比")
    print("=" * 70)
    
    capabilities = {
        'Oura': {
            '睡眠时长': '✓',
            '深度睡眠': '✓',
            'REM睡眠': '✓',
            '核心睡眠': '✓',
            '清醒检测': '✓',
            '入睡时间': '✓',
            '起床时间': '✓',
            '中级别积分': '✓',
            '难级别积分': '✓'
        },
        'WHOOP': {
            '睡眠时长': '✓',
            '深度睡眠': '✗',
            'REM睡眠': '✗',
            '核心睡眠': '✗',
            '清醒检测': '✓',
            '入睡时间': '✓',
            '起床时间': '✓',
            '中级别积分': '✗',
            '难级别积分': '✓'
        },
        'OffScreen': {
            '睡眠时长': '✓',
            '深度睡眠': '✗',
            'REM睡眠': '✗',
            '核心睡眠': '✗',
            '清醒检测': '✗',
            '入睡时间': '✓',
            '起床时间': '✓',
            '中级别积分': '✗',
            '难级别积分': '✓'
        },
        'Apple Watch': {
            '睡眠时长': '✗',
            '深度睡眠': '✗',
            'REM睡眠': '✗',
            '核心睡眠': '✗',
            '清醒检测': '✗',
            '入睡时间': '✗',
            '起床时间': '✗',
            '中级别积分': '✗',
            '难级别积分': '✗'
        }
    }
    
    # 打印对比表
    print("\n功能支持对比表:")
    print("-" * 70)
    print(f"{'功能':<15} {'Oura':<10} {'WHOOP':<10} {'OffScreen':<12} {'Apple Watch':<12}")
    print("-" * 70)
    
    for feature in capabilities['Oura'].keys():
        row = f"{feature:<15}"
        for source in ['Oura', 'WHOOP', 'OffScreen', 'Apple Watch']:
            row += f" {capabilities[source][feature]:<10}"
        print(row)
    
    print("\n说明:")
    print("  ✓ = 支持该功能")
    print("  ✗ = 不支持该功能")
    print("\n注意:")
    print("  1. Apple Watch在此CSV数据中没有睡眠分析数据")
    print("  2. WHOOP只提供未指定类型的睡眠数据")
    print("  3. OffScreen只提供未指定类型的睡眠数据")
    print("  4. 只有Oura提供完整的睡眠阶段分析")


def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("全面测试各种睡眠数据源")
    print("=" * 80)
    
    # 1. 分析所有数据源
    sleep_sources, sleep_stages = analyze_all_sleep_sources()
    
    # 2. 测试每个数据源
    for source in sleep_sources.keys():
        test_sleep_analysis_by_source(source)
    
    # 3. 比较数据源能力
    compare_data_sources()
    
    # 4. 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    print("\n关键发现:")
    print("  1. CSV数据中没有Apple Watch的睡眠分析数据")
    print("     - Apple Watch有心率、运动、站立等数据")
    print("     - 但没有HKCategoryTypeIdentifierSleepAnalysis类型的数据")
    print("\n  2. Oura是唯一提供完整睡眠阶段的数据源")
    print("     - 包含深度睡眠、REM睡眠、核心睡眠等详细阶段")
    print("     - 可以计算中级别积分（深度+REM）")
    print("\n  3. WHOOP和OffScreen只提供基础睡眠数据")
    print("     - 只有AsleepUnspecified（未指定睡眠类型）")
    print("     - 只能计算易级别积分（总睡眠时长）")
    print("\n  4. 系统设计考虑:")
    print("     - 优先使用Oura数据进行完整积分计算")
    print("     - 其他数据源作为备选，只计算基础积分")
    print("     - 需要等待Apple Watch提供睡眠阶段API")


if __name__ == "__main__":
    main()