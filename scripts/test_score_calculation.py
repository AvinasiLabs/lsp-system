#!/usr/bin/env python3
"""
测试积分计算功能
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.score_engine import ScoreEngine
from src.services.health_data_service import HealthDataService


def test_health_data_service():
    """测试健康数据服务"""
    print("=== 测试健康数据服务 ===\n")
    
    service = HealthDataService()
    
    # 测试最近7天的数据
    end_date = datetime(2025, 7, 9)  # 数据的最后日期
    start_date = end_date - timedelta(days=6)
    
    print(f"获取 {start_date.date()} 到 {end_date.date()} 的健康数据汇总:\n")
    
    current_date = start_date
    while current_date <= end_date:
        summary = service.get_daily_summary(current_date)
        
        print(f"日期: {current_date.date()}")
        print(f"  睡眠: {summary.sleep_hours:.1f} 小时" if summary.sleep_hours else "  睡眠: 无数据")
        print(f"  步数: {summary.steps:,} 步" if summary.steps else "  步数: 无数据")
        print(f"  运动: {summary.exercise_minutes} 分钟" if summary.exercise_minutes else "  运动: 无数据")
        print(f"  站立: {summary.stand_hours} 小时" if summary.stand_hours else "  站立: 无数据")
        print(f"  心率: {summary.avg_heart_rate:.1f} bpm" if summary.avg_heart_rate else "  心率: 无数据")
        print(f"  HRV: {summary.hrv:.1f} ms" if summary.hrv else "  HRV: 无数据")
        print(f"  饮水: {summary.water_ml:.0f} ml" if summary.water_ml else "  饮水: 无数据")
        print()
        
        current_date += timedelta(days=1)


def test_score_calculation():
    """测试积分计算"""
    print("\n=== 测试积分计算 ===\n")
    
    engine = ScoreEngine()
    
    # 检查可用维度
    print("可用的积分维度:")
    available = engine.get_available_dimensions()
    for dimension, is_available in available.items():
        status = "✅" if is_available else "❌"
        print(f"  {status} {dimension}")
    print()
    
    # 计算特定日期的积分
    test_date = datetime(2025, 7, 8)
    print(f"计算 {test_date.date()} 的积分:\n")
    
    result = engine.calculate_daily_score(test_date)
    
    # 显示健康数据
    print("健康数据汇总:")
    summary = result['health_summary']
    for key, value in summary.items():
        if value is not None and key != 'date':
            print(f"  {key}: {value}")
    print()
    
    # 显示各维度积分
    print("各维度积分:")
    for dimension, scores in result['dimension_scores'].items():
        if scores['total'] > 0:
            print(f"\n  {dimension}:")
            print(f"    易: {scores['easy']} 分")
            print(f"    中: {scores['medium']} 分")
            print(f"    难: {scores['hard']} 分")
            print(f"    超难: {scores['super_hard']} 分")
            print(f"    小计: {scores['total']} 分")
    
    print(f"\n总积分: {result['total_score']} 分")
    print(f"用户等级: {result['user_level']}")


def test_date_range_scores():
    """测试日期范围积分计算"""
    print("\n\n=== 测试日期范围积分计算 ===\n")
    
    engine = ScoreEngine()
    
    # 计算一周的积分
    end_date = datetime(2025, 7, 9)
    start_date = end_date - timedelta(days=6)
    
    print(f"计算 {start_date.date()} 到 {end_date.date()} 的积分:\n")
    
    scores = engine.calculate_date_range_scores(start_date, end_date)
    
    # 显示每日积分
    print("日期          睡眠   运动   饮食   心理   总分")
    print("-" * 60)
    
    for score in scores:
        date = score['date'][:10]
        sleep = score['dimension_scores'].get('sleep', {}).get('total', 0)
        exercise = score['dimension_scores'].get('exercise', {}).get('total', 0)
        diet = score['dimension_scores'].get('diet', {}).get('total', 0)
        mental = score['dimension_scores'].get('mental', {}).get('total', 0)
        total = score['total_score']
        
        print(f"{date}  {sleep:>6} {exercise:>6} {diet:>6} {mental:>6} {total:>6}")
    
    # 计算平均分
    if scores:
        avg_score = sum(s['total_score'] for s in scores) / len(scores)
        print(f"\n平均每日积分: {avg_score:.0f} 分")


def main():
    """主函数"""
    print("LSP积分系统 - 功能测试\n")
    
    try:
        # 测试健康数据服务
        test_health_data_service()
        
        # 测试积分计算
        test_score_calculation()
        
        # 测试日期范围积分
        test_date_range_scores()
        
        print("\n\n✅ 所有测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()