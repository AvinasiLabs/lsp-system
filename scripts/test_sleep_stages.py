#!/usr/bin/env python
"""
测试睡眠阶段分析和积分计算功能
验证新增的深度睡眠、REM睡眠和时间限制积分计算
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.sleep_analysis_service import SleepAnalysisService
from src.core.calculators.sleep_calculator import SleepCalculator
from src.models.health_data import DailyHealthSummary
from src.utils.logger import logger


def test_sleep_analysis_service():
    """测试睡眠阶段分析服务"""
    logger.info("=" * 60)
    logger.info("测试睡眠阶段分析服务")
    logger.info("=" * 60)
    
    service = SleepAnalysisService()
    
    # 测试用户和日期
    test_user = "default_user"
    test_date = datetime(2025, 6, 11)  # 根据CSV数据选择的日期
    
    # 分析睡眠阶段
    logger.info(f"\n分析 {test_date.date()} 的睡眠数据...")
    analysis = service.analyze_sleep_stages(test_user, test_date, source_filter='Oura')
    
    if analysis['has_data']:
        logger.info(f"✓ 找到睡眠数据")
        logger.info(f"  总睡眠时长: {analysis['total_sleep_hours']:.2f} 小时")
        logger.info(f"  深度睡眠: {analysis['deep_sleep_hours']:.2f} 小时")
        logger.info(f"  REM睡眠: {analysis['rem_sleep_hours']:.2f} 小时")
        logger.info(f"  核心睡眠: {analysis['core_sleep_hours']:.2f} 小时")
        logger.info(f"  清醒时间: {analysis['awake_minutes']:.0f} 分钟")
        
        if analysis['sleep_time']:
            logger.info(f"  入睡时间: {analysis['sleep_time']}")
        if analysis['wake_time']:
            logger.info(f"  起床时间: {analysis['wake_time']}")
    else:
        logger.warning("✗ 没有找到睡眠数据")
    
    # 测试睡眠时间详情
    logger.info(f"\n分析睡眠时间限制...")
    time_details = service.get_sleep_time_details(test_user, test_date, source_filter='Oura')
    
    if time_details['has_data']:
        logger.info(f"  满足23:30前入睡: {'✓' if time_details['meets_sleep_target'] else '✗'}")
        logger.info(f"  满足7:30前起床: {'✓' if time_details['meets_wake_target'] else '✗'}")
    
    return analysis['has_data']


def test_sleep_calculator():
    """测试睡眠计算器的新功能"""
    logger.info("\n" + "=" * 60)
    logger.info("测试睡眠计算器积分计算")
    logger.info("=" * 60)
    
    calculator = SleepCalculator()
    
    # 创建测试数据
    health_data = DailyHealthSummary(
        user_id="default_user",
        date=datetime(2025, 6, 11).date(),
        sleep_hours=7.8,  # 满足易级别
        steps=None,
        exercise_minutes=None,
        stand_hours=None,
        water_ml=None,
        hrv=None
    )
    
    # 计算积分（传递user_id和date以使用新功能）
    scores = calculator.calculate(
        health_data, 
        user_id="default_user",
        date=datetime(2025, 6, 11)
    )
    
    logger.info(f"\n积分计算结果:")
    logger.info(f"  易级别（睡眠时长）: {scores['easy']} 分")
    logger.info(f"  中级别（深度+REM）: {scores['medium']} 分")
    logger.info(f"  难级别（时间限制）: {scores['hard']} 分")
    logger.info(f"  超难级别: {scores['super_hard']} 分")
    logger.info(f"  总分: {scores['total']} 分")
    
    # 验证规则
    logger.info(f"\n规则验证:")
    rules = calculator.get_rules()
    
    if scores['easy'] > 0:
        logger.info(f"  ✓ 易级别: 睡眠 {health_data.sleep_hours} 小时 >= {rules['easy']['min_hours']} 小时")
    else:
        logger.info(f"  ✗ 易级别: 睡眠时长不足")
    
    if scores['medium'] > 0:
        logger.info(f"  ✓ 中级别: 深度睡眠 >= {rules['medium']['deep_sleep_hours']} 小时 且 REM >= {rules['medium']['rem_sleep_hours']} 小时")
    else:
        logger.info(f"  ✗ 中级别: 深度睡眠或REM睡眠不达标")
    
    if scores['hard'] > 0:
        logger.info(f"  ✓ 难级别: {rules['hard']['sleep_before']}前入睡 且 {rules['hard']['wake_before']}前起床")
    else:
        logger.info(f"  ✗ 难级别: 入睡或起床时间不符合要求")
    
    return scores['total'] > 0


def test_multiple_days():
    """测试多天的睡眠数据"""
    logger.info("\n" + "=" * 60)
    logger.info("测试多天睡眠数据分析")
    logger.info("=" * 60)
    
    service = SleepAnalysisService()
    calculator = SleepCalculator()
    
    # 测试一周的数据
    start_date = datetime(2025, 6, 10)
    end_date = datetime(2025, 6, 16)
    current_date = start_date
    
    total_scores = {
        'easy': 0,
        'medium': 0,
        'hard': 0,
        'total': 0
    }
    
    logger.info(f"\n分析 {start_date.date()} 到 {end_date.date()} 的睡眠数据:\n")
    
    while current_date <= end_date:
        # 分析睡眠阶段
        analysis = service.analyze_sleep_stages("default_user", current_date, source_filter='Oura')
        
        if analysis['has_data']:
            # 创建健康数据
            health_data = DailyHealthSummary(
                user_id="default_user",
                date=current_date.date(),
                sleep_hours=analysis['total_sleep_hours'],
                steps=None,
                exercise_minutes=None,
                stand_hours=None,
                water_ml=None,
                hrv=None
            )
            
            # 计算积分
            scores = calculator.calculate(
                health_data,
                user_id="default_user",
                date=current_date
            )
            
            logger.info(f"{current_date.date()}: "
                       f"睡眠{analysis['total_sleep_hours']:.1f}h, "
                       f"深度{analysis['deep_sleep_hours']:.1f}h, "
                       f"REM{analysis['rem_sleep_hours']:.1f}h, "
                       f"积分: 易{scores['easy']}, 中{scores['medium']}, 难{scores['hard']}, "
                       f"总{scores['total']}")
            
            # 累计积分
            for key in ['easy', 'medium', 'hard', 'total']:
                total_scores[key] += scores[key]
        else:
            logger.info(f"{current_date.date()}: 无数据")
        
        current_date += timedelta(days=1)
    
    logger.info(f"\n一周总积分:")
    logger.info(f"  易级别: {total_scores['easy']} 分")
    logger.info(f"  中级别: {total_scores['medium']} 分")
    logger.info(f"  难级别: {total_scores['hard']} 分")
    logger.info(f"  总计: {total_scores['total']} 分")
    
    return total_scores['total'] > 0


def main():
    """主测试函数"""
    logger.info("\n" + "=" * 70)
    logger.info("开始测试睡眠阶段分析和积分计算功能")
    logger.info("=" * 70)
    
    # 运行各项测试
    tests_passed = []
    
    # 测试1: 睡眠分析服务
    logger.info("\n[测试 1/3] 睡眠阶段分析服务")
    tests_passed.append(test_sleep_analysis_service())
    
    # 测试2: 睡眠计算器
    logger.info("\n[测试 2/3] 睡眠计算器积分计算")
    tests_passed.append(test_sleep_calculator())
    
    # 测试3: 多天数据
    logger.info("\n[测试 3/3] 多天睡眠数据分析")
    tests_passed.append(test_multiple_days())
    
    # 汇总结果
    logger.info("\n" + "=" * 70)
    logger.info("测试完成")
    logger.info("=" * 70)
    
    passed_count = sum(tests_passed)
    total_count = len(tests_passed)
    
    logger.info(f"\n测试结果: {passed_count}/{total_count} 通过")
    
    if all(tests_passed):
        logger.info("✓ 所有测试通过！睡眠阶段分析功能正常工作")
    else:
        logger.warning("✗ 部分测试失败，请检查日志")
    
    logger.info("\n功能说明:")
    logger.info("1. 中级别积分: 深度睡眠>1.5小时 + REM睡眠>1.5小时 = 2000分")
    logger.info("2. 难级别积分: 23:30前入睡 + 7:30前起床 = 4000分")
    logger.info("3. 数据源: 使用Oura数据（包含完整睡眠阶段信息）")
    logger.info("4. 兼容性: 保留旧方法，无数据时自动回退")


if __name__ == "__main__":
    main()