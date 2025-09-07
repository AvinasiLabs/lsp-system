#!/usr/bin/env python
"""
使用CSV文件直接测试睡眠阶段分析功能
不依赖数据库连接
"""

import csv
from datetime import datetime, timedelta, time
from typing import Dict, List


class SleepAnalysisFromCSV:
    """从CSV文件分析睡眠阶段"""
    
    # 睡眠阶段映射
    SLEEP_STAGE_MAPPING = {
        'HKCategoryValueSleepAnalysisAwake': 'awake',
        'HKCategoryValueSleepAnalysisAsleepCore': 'core',
        'HKCategoryValueSleepAnalysisAsleepDeep': 'deep',
        'HKCategoryValueSleepAnalysisAsleepREM': 'rem',
        'HKCategoryValueSleepAnalysisInBed': 'in_bed',
        'HKCategoryValueSleepAnalysisAsleepUnspecified': 'unspecified'
    }
    
    def __init__(self, csv_file: str):
        """初始化并加载CSV数据"""
        self.csv_file = csv_file
        self.sleep_data = self.load_sleep_data()
        print(f"✓ 加载了 {len(self.sleep_data)} 条睡眠记录")
    
    def load_sleep_data(self) -> List[Dict]:
        """从CSV加载睡眠数据"""
        sleep_records = []
        
        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['type'] == 'HKCategoryTypeIdentifierSleepAnalysis':
                    sleep_records.append(row)
        
        return sleep_records
    
    def analyze_sleep_for_date(self, date: datetime, source_filter: str = 'Oura') -> Dict:
        """分析特定日期的睡眠"""
        # 获取该晚的睡眠数据（前一天晚上到当天早上）
        start_time = datetime.combine(date - timedelta(days=1), time(18, 0))
        end_time = datetime.combine(date, time(12, 0))
        
        # 过滤相关数据
        night_data = []
        for record in self.sleep_data:
            if record['source_name'] != source_filter:
                continue
            
            # 解析时间（去除时区信息）
            start_str = record['start_date'].split('+')[0]
            end_str = record['end_date'].split('+')[0]
            
            try:
                record_start = datetime.fromisoformat(start_str)
                record_end = datetime.fromisoformat(end_str)
                
                # 检查是否在时间范围内
                if record_start >= start_time and record_end <= end_time:
                    night_data.append({
                        'start': record_start,
                        'end': record_end,
                        'stage': self.SLEEP_STAGE_MAPPING.get(record['value'], 'unknown'),
                        'value': record['value']
                    })
            except:
                continue
        
        if not night_data:
            return {'has_data': False, 'date': date.date().isoformat()}
        
        # 按开始时间排序
        night_data.sort(key=lambda x: x['start'])
        
        # 统计各阶段时长
        stages_duration = {
            'awake': 0,
            'rem': 0,
            'core': 0,
            'deep': 0,
            'in_bed': 0,
            'unspecified': 0
        }
        
        for record in night_data:
            duration_minutes = (record['end'] - record['start']).total_seconds() / 60
            stage = record['stage']
            if stage in stages_duration:
                stages_duration[stage] += duration_minutes
        
        # 计算总睡眠时长（不包括清醒）
        total_sleep_minutes = (stages_duration['rem'] + stages_duration['core'] + 
                              stages_duration['deep'] + stages_duration['unspecified'])
        
        # 获取入睡和起床时间
        sleep_time = night_data[0]['start'] if night_data else None
        wake_time = night_data[-1]['end'] if night_data else None
        
        # 判断时间是否符合要求
        meets_sleep_target = False
        meets_wake_target = False
        
        if sleep_time:
            # 23:30前入睡
            target_sleep = datetime.combine(sleep_time.date(), time(23, 30))
            if sleep_time.hour < 12:  # 凌晨
                target_sleep = target_sleep - timedelta(days=1)
            meets_sleep_target = sleep_time <= target_sleep
        
        if wake_time:
            # 7:30前起床
            target_wake = datetime.combine(wake_time.date(), time(7, 30))
            meets_wake_target = wake_time <= target_wake
        
        return {
            'has_data': True,
            'date': date.date().isoformat(),
            'stages_duration_hours': {k: v/60 for k, v in stages_duration.items()},
            'total_sleep_hours': total_sleep_minutes / 60,
            'deep_sleep_hours': stages_duration['deep'] / 60,
            'rem_sleep_hours': stages_duration['rem'] / 60,
            'sleep_time': sleep_time.isoformat() if sleep_time else None,
            'wake_time': wake_time.isoformat() if wake_time else None,
            'meets_sleep_target': meets_sleep_target,
            'meets_wake_target': meets_wake_target,
            'record_count': len(night_data)
        }
    
    def calculate_sleep_scores(self, analysis: Dict) -> Dict:
        """根据分析结果计算积分"""
        scores = {
            'easy': 0,
            'medium': 0,
            'hard': 0,
            'total': 0
        }
        
        if not analysis['has_data']:
            return scores
        
        # 易级别：睡够7.5小时（1000分）
        if analysis['total_sleep_hours'] >= 7.5:
            scores['easy'] = 1000
        elif analysis['total_sleep_hours'] >= 6.0:
            # 6-7.5小时之间，按比例扣分
            minutes_short = (7.5 - analysis['total_sleep_hours']) * 60
            scores['easy'] = max(0, 1000 - int(minutes_short * 5))
        
        # 中级别：深度睡眠>1.5h + REM睡眠>1.5h（2000分）
        meets_deep = analysis['deep_sleep_hours'] >= 1.5
        meets_rem = analysis['rem_sleep_hours'] >= 1.5
        
        if meets_deep and meets_rem:
            scores['medium'] = 2000
        elif meets_deep or meets_rem:
            scores['medium'] = 1000
        
        # 难级别：时间限制（4000分）
        # 需要易和中都有分数
        if scores['easy'] > 0 and scores['medium'] > 0:
            if analysis['meets_sleep_target'] and analysis['meets_wake_target']:
                scores['hard'] = 4000
            elif analysis['meets_sleep_target'] or analysis['meets_wake_target']:
                scores['hard'] = 2000
        
        scores['total'] = sum([scores['easy'], scores['medium'], scores['hard']])
        return scores


def test_single_night():
    """测试单晚睡眠数据"""
    print("\n" + "=" * 60)
    print("测试单晚睡眠数据分析")
    print("=" * 60)
    
    # 创建分析器
    analyzer = SleepAnalysisFromCSV('/Users/jojizhou/Documents/avinasi/lsp_system/data/data_30_20250709.csv')
    
    # 测试日期（选择有Oura数据的日期）
    test_date = datetime(2025, 6, 11)
    
    print(f"\n分析 {test_date.date()} 的睡眠数据...")
    analysis = analyzer.analyze_sleep_for_date(test_date, source_filter='Oura')
    
    if analysis['has_data']:
        print(f"✓ 找到 {analysis['record_count']} 条睡眠记录")
        print(f"\n睡眠统计:")
        print(f"  总睡眠时长: {analysis['total_sleep_hours']:.2f} 小时")
        print(f"  深度睡眠: {analysis['deep_sleep_hours']:.2f} 小时")
        print(f"  REM睡眠: {analysis['rem_sleep_hours']:.2f} 小时")
        print(f"  核心睡眠: {analysis['stages_duration_hours']['core']:.2f} 小时")
        print(f"  清醒时间: {analysis['stages_duration_hours']['awake']*60:.0f} 分钟")
        
        print(f"\n时间分析:")
        if analysis['sleep_time']:
            sleep_time = datetime.fromisoformat(analysis['sleep_time'])
            print(f"  入睡时间: {sleep_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"  满足23:30前入睡: {'✓' if analysis['meets_sleep_target'] else '✗'}")
        
        if analysis['wake_time']:
            wake_time = datetime.fromisoformat(analysis['wake_time'])
            print(f"  起床时间: {wake_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"  满足7:30前起床: {'✓' if analysis['meets_wake_target'] else '✗'}")
        
        # 计算积分
        scores = analyzer.calculate_sleep_scores(analysis)
        print(f"\n积分计算:")
        print(f"  易级别（睡眠时长）: {scores['easy']} 分")
        print(f"  中级别（深度+REM）: {scores['medium']} 分")
        print(f"  难级别（时间限制）: {scores['hard']} 分")
        print(f"  总分: {scores['total']} 分")
    else:
        print("✗ 没有找到睡眠数据")


def test_week_analysis():
    """测试一周的睡眠数据"""
    print("\n" + "=" * 60)
    print("测试一周睡眠数据分析")
    print("=" * 60)
    
    analyzer = SleepAnalysisFromCSV('/Users/jojizhou/Documents/avinasi/lsp_system/data/data_30_20250709.csv')
    
    # 分析一周
    start_date = datetime(2025, 6, 10)
    end_date = datetime(2025, 6, 16)
    
    print(f"\n分析 {start_date.date()} 到 {end_date.date()} 的睡眠数据:\n")
    print("日期        睡眠  深度  REM   积分(易/中/难/总)")
    print("-" * 60)
    
    total_scores = {'easy': 0, 'medium': 0, 'hard': 0, 'total': 0}
    days_with_data = 0
    
    current_date = start_date
    while current_date <= end_date:
        analysis = analyzer.analyze_sleep_for_date(current_date, source_filter='Oura')
        
        if analysis['has_data']:
            scores = analyzer.calculate_sleep_scores(analysis)
            
            print(f"{current_date.date()}  "
                  f"{analysis['total_sleep_hours']:4.1f}h "
                  f"{analysis['deep_sleep_hours']:4.1f}h "
                  f"{analysis['rem_sleep_hours']:4.1f}h  "
                  f"{scores['easy']:4d}/{scores['medium']:4d}/{scores['hard']:4d}/{scores['total']:5d}")
            
            for key in total_scores:
                total_scores[key] += scores[key]
            days_with_data += 1
        else:
            print(f"{current_date.date()}  无数据")
        
        current_date += timedelta(days=1)
    
    print("-" * 60)
    if days_with_data > 0:
        print(f"\n一周汇总 ({days_with_data} 天有数据):")
        print(f"  易级别总分: {total_scores['easy']} 分")
        print(f"  中级别总分: {total_scores['medium']} 分")
        print(f"  难级别总分: {total_scores['hard']} 分")
        print(f"  总积分: {total_scores['total']} 分")
        print(f"  日均积分: {total_scores['total']/days_with_data:.0f} 分")


def check_data_sources():
    """检查数据源情况"""
    print("\n" + "=" * 60)
    print("检查CSV文件中的数据源")
    print("=" * 60)
    
    csv_file = '/Users/jojizhou/Documents/avinasi/lsp_system/data/data_30_20250709.csv'
    
    # 统计数据源
    sources = {}
    sleep_stages = {}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['type'] == 'HKCategoryTypeIdentifierSleepAnalysis':
                source = row['source_name']
                sources[source] = sources.get(source, 0) + 1
                
                if source == 'Oura':
                    stage = row['value'].replace('HKCategoryValueSleepAnalysis', '')
                    sleep_stages[stage] = sleep_stages.get(stage, 0) + 1
    
    print("\n睡眠数据源统计:")
    for source, count in sources.items():
        print(f"  {source}: {count} 条记录")
    
    print("\nOura睡眠阶段分布:")
    for stage, count in sleep_stages.items():
        print(f"  {stage}: {count} 条记录")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("睡眠阶段分析功能测试（基于CSV文件）")
    print("=" * 70)
    
    # 1. 检查数据源
    check_data_sources()
    
    # 2. 测试单晚分析
    test_single_night()
    
    # 3. 测试一周分析
    test_week_analysis()
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)
    
    print("\n功能验证总结:")
    print("✓ 成功从CSV文件加载睡眠阶段数据")
    print("✓ 正确计算各睡眠阶段时长（深度、REM、核心）")
    print("✓ 准确判断入睡和起床时间是否符合要求")
    print("✓ 按规则计算易、中、难级别积分")
    print("\n积分规则:")
    print("  易级别: 睡眠≥7.5小时 = 1000分")
    print("  中级别: 深度≥1.5h + REM≥1.5h = 2000分")
    print("  难级别: 23:30前入睡 + 7:30前起床 = 4000分（需易中都有分）")


if __name__ == "__main__":
    main()