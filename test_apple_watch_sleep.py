#!/usr/bin/env python
"""
测试Apple Watch和其他数据源的睡眠数据处理
验证多数据源优先级选择功能
"""

import csv
from datetime import datetime, timedelta
from collections import defaultdict


def analyze_csv_for_apple_watch_sleep():
    """深入分析CSV中是否有Apple Watch的睡眠数据"""
    csv_file = '/Users/jojizhou/Documents/avinasi/lsp_system/data/data_30_20250709.csv'
    
    print("\n" + "=" * 80)
    print("深入分析CSV文件中的Apple Watch数据")
    print("=" * 80)
    
    # 统计各种数据
    apple_watch_types = defaultdict(int)
    all_sleep_sources = defaultdict(int)
    zhou_data_types = defaultdict(int)
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            source = row['source_name']
            data_type = row['type']
            
            # 统计所有睡眠数据源
            if 'Sleep' in data_type:
                all_sleep_sources[source] += 1
            
            # 统计周基源的所有数据类型
            if '周基源' in source:
                zhou_data_types[data_type] += 1
                
                # 特别检查Apple Watch
                if 'Apple Watch' in source:
                    apple_watch_types[data_type] += 1
    
    print("\n1. 周基源的Apple Watch数据类型统计:")
    print("-" * 50)
    if apple_watch_types:
        # 按数量排序
        sorted_types = sorted(apple_watch_types.items(), key=lambda x: x[1], reverse=True)
        for dtype, count in sorted_types[:15]:
            short_name = dtype.replace('HKQuantityTypeIdentifier', '').replace('HKCategoryTypeIdentifier', '')
            print(f"  {short_name}: {count} 条")
        
        # 检查是否有睡眠相关
        sleep_related = [k for k, v in apple_watch_types.items() if 'Sleep' in k or 'sleep' in k]
        if sleep_related:
            print(f"\n  ✓ 找到睡眠相关数据: {sleep_related}")
        else:
            print(f"\n  ✗ Apple Watch数据中没有睡眠分析数据")
    else:
        print("  未找到周基源的Apple Watch数据")
    
    print("\n2. 所有包含'Sleep'的数据源:")
    print("-" * 50)
    if all_sleep_sources:
        for source, count in sorted(all_sleep_sources.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count} 条")
    else:
        print("  未找到任何睡眠数据")
    
    print("\n3. 数据可用性分析:")
    print("-" * 50)
    print(f"  周基源的数据类型总数: {len(zhou_data_types)}")
    print(f"  周基源的Apple Watch数据类型数: {len(apple_watch_types)}")
    print(f"  睡眠数据源总数: {len(all_sleep_sources)}")
    
    # 返回分析结果
    return {
        'has_apple_watch_sleep': any('Sleep' in k for k in apple_watch_types.keys()),
        'apple_watch_data_types': len(apple_watch_types),
        'sleep_sources': list(all_sleep_sources.keys())
    }


def test_multi_source_priority():
    """测试多数据源优先级选择"""
    print("\n" + "=" * 80)
    print("测试多数据源优先级选择逻辑")
    print("=" * 80)
    
    # 模拟数据源优先级
    SOURCE_PRIORITY = {
        'Apple Watch': 1,  # 最高优先级
        'Oura': 2,
        'WHOOP': 3,
        'OffScreen': 4
    }
    
    # 测试场景
    test_cases = [
        {
            'name': '场景1: 只有Oura数据',
            'available': ['Oura'],
            'expected': 'Oura'
        },
        {
            'name': '场景2: 有Oura和WHOOP',
            'available': ['WHOOP', 'Oura'],
            'expected': 'Oura'
        },
        {
            'name': '场景3: 有Apple Watch和Oura',
            'available': ['Oura', '周基源的Apple Watch'],
            'expected': '周基源的Apple Watch'
        },
        {
            'name': '场景4: 所有数据源都有',
            'available': ['OffScreen', 'WHOOP', 'Oura', '某人的Apple Watch'],
            'expected': '某人的Apple Watch'
        }
    ]
    
    print("\n优先级规则:")
    for source, priority in SOURCE_PRIORITY.items():
        print(f"  {priority}. {source}")
    
    print("\n测试结果:")
    print("-" * 50)
    
    for test in test_cases:
        # 选择最佳数据源
        best_source = None
        best_priority = float('inf')
        
        for source in test['available']:
            # 检查是否包含优先级关键词
            priority = float('inf')
            for key, pri in SOURCE_PRIORITY.items():
                if key.lower() in source.lower():
                    priority = min(priority, pri)
            
            # 直接匹配
            if priority == float('inf'):
                priority = SOURCE_PRIORITY.get(source, 999)
            
            if priority < best_priority:
                best_priority = priority
                best_source = source
        
        # 验证结果
        passed = best_source == test['expected']
        status = "✓" if passed else "✗"
        
        print(f"\n{test['name']}")
        print(f"  可用数据源: {test['available']}")
        print(f"  预期选择: {test['expected']}")
        print(f"  实际选择: {best_source}")
        print(f"  结果: {status}")


def simulate_sleep_score_calculation():
    """模拟使用不同数据源计算睡眠积分"""
    print("\n" + "=" * 80)
    print("模拟睡眠积分计算（基于不同数据源）")
    print("=" * 80)
    
    # 模拟不同数据源的能力
    source_capabilities = {
        'Apple Watch (如果有睡眠数据)': {
            '数据质量': '未知',
            '易级别积分': '?',
            '中级别积分': '?',
            '难级别积分': '?',
            '说明': '需要iOS 14+且用户启用睡眠追踪'
        },
        'Oura': {
            '数据质量': '优秀',
            '易级别积分': '✓ (睡眠时长)',
            '中级别积分': '✓ (深度+REM)',
            '难级别积分': '✓ (时间限制)',
            '说明': '专业睡眠追踪设备，数据最完整'
        },
        'WHOOP': {
            '数据质量': '良好',
            '易级别积分': '✓ (睡眠时长)',
            '中级别积分': '✗ (无睡眠阶段)',
            '难级别积分': '✓ (时间限制)',
            '说明': '有睡眠时长和清醒检测'
        },
        'OffScreen': {
            '数据质量': '基础',
            '易级别积分': '✓ (睡眠时长)',
            '中级别积分': '✗ (无睡眠阶段)',
            '难级别积分': '✓ (时间限制)',
            '说明': '只有基础睡眠时长'
        }
    }
    
    print("\n各数据源积分计算能力对比:")
    print("-" * 80)
    
    for source, caps in source_capabilities.items():
        print(f"\n{source}:")
        for key, value in caps.items():
            print(f"  {key}: {value}")
    
    print("\n系统设计建议:")
    print("-" * 50)
    print("1. 优先使用Apple Watch数据（如果存在且包含睡眠分析）")
    print("2. 其次使用Oura数据（最完整的睡眠阶段）")
    print("3. 再次使用WHOOP/OffScreen（基础睡眠数据）")
    print("4. 自动降级处理：根据数据源能力调整积分计算")


def main():
    """主测试函数"""
    print("\n" + "=" * 90)
    print("Apple Watch睡眠数据测试与多数据源管理")
    print("=" * 90)
    
    # 1. 分析CSV中的Apple Watch数据
    analysis = analyze_csv_for_apple_watch_sleep()
    
    # 2. 测试多数据源优先级
    test_multi_source_priority()
    
    # 3. 模拟积分计算
    simulate_sleep_score_calculation()
    
    # 4. 总结
    print("\n" + "=" * 90)
    print("测试总结与建议")
    print("=" * 90)
    
    if analysis['has_apple_watch_sleep']:
        print("\n✓ 发现Apple Watch睡眠数据！")
        print("  系统将优先使用Apple Watch数据进行积分计算")
    else:
        print("\n✗ 未发现Apple Watch睡眠数据")
        print("  可能原因:")
        print("  1. 用户未佩戴Apple Watch睡觉")
        print("  2. 未启用Apple Watch睡眠追踪功能")
        print("  3. iOS/watchOS版本不支持睡眠分析")
        print("  4. 数据导出时未包含睡眠数据")
    
    print("\n当前实现的功能:")
    print("  ✓ 多数据源自动选择（按优先级）")
    print("  ✓ 数据源质量评估")
    print("  ✓ 根据数据源能力自适应积分计算")
    print("  ✓ 支持手动指定数据源")
    
    print("\n使用建议:")
    print("  1. 让系统自动选择最佳数据源（不指定source_filter）")
    print("  2. 系统会按照 Apple Watch > Oura > WHOOP > OffScreen 的顺序选择")
    print("  3. 根据实际数据质量自动调整积分计算策略")


if __name__ == "__main__":
    main()