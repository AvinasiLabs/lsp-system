#!/usr/bin/env python3
"""
简单测试百分比计算功能
不依赖复杂的依赖项
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 只导入核心配置模块
from src.core.score_config import DIMENSION_MAX_SCORES, calculate_percentage

def test_percentage_calculation():
    """测试百分比计算函数"""
    print("=" * 50)
    print("测试百分比计算功能")
    print("=" * 50)
    
    # 测试各种维度和得分
    test_cases = [
        ("sleep", 1000, "easy", 100.0),     # 满分情况
        ("sleep", 500, "easy", 50.0),       # 50%情况
        ("sleep", 8500, "total", 50.0),     # 总分50%情况
        ("exercise", 1390, "easy", 50.0),   # 运动easy维度50%
        ("diet", 100, "easy", 10.0),        # 饮食10%情况
        ("mental", 1500, "medium", 50.0),   # 心理medium 50%
    ]
    
    print("\n测试用例结果：")
    all_passed = True
    for dimension, score, difficulty, expected in test_cases:
        actual = calculate_percentage(score, dimension, difficulty)
        passed = abs(actual - expected) < 0.01  # 允许小数点误差
        status = "✓" if passed else "✗"
        print(f"{status} {dimension}/{difficulty}: {score}分 -> {actual}% (期望: {expected}%)")
        if not passed:
            all_passed = False
    
    return all_passed

def display_max_scores():
    """显示各维度的最高分配置"""
    print("\n" + "=" * 50)
    print("各维度最高分配置")
    print("=" * 50)
    
    for dimension, scores in DIMENSION_MAX_SCORES.items():
        if scores['total'] > 0:  # 只显示已实现的维度
            print(f"\n{dimension}维度:")
            print(f"  易: {scores['easy']}分")
            print(f"  中: {scores['medium']}分")
            print(f"  难: {scores['hard']}分")
            print(f"  超难: {scores['super_hard']}分")
            print(f"  总计: {scores['total']}分")

def demonstrate_usage():
    """演示使用示例"""
    print("\n" + "=" * 50)
    print("使用示例")
    print("=" * 50)
    
    # 模拟用户获得的积分
    user_scores = {
        "sleep": {"easy": 800, "medium": 0, "hard": 0, "super_hard": 0, "total": 800},
        "exercise": {"easy": 1500, "medium": 1600, "hard": 0, "super_hard": 0, "total": 3100},
        "diet": {"easy": 500, "medium": 0, "hard": 0, "super_hard": 0, "total": 500},
        "mental": {"easy": 0, "medium": 1500, "hard": 0, "super_hard": 0, "total": 1500}
    }
    
    print("\n模拟用户积分及百分比：")
    for dimension, scores in user_scores.items():
        print(f"\n{dimension}维度:")
        for difficulty, score in scores.items():
            percentage = calculate_percentage(score, dimension, difficulty)
            print(f"  {difficulty}: {score}分 ({percentage}%)")

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("积分百分比计算功能测试")
    print("=" * 60)
    
    # 显示配置
    display_max_scores()
    
    # 运行测试
    test_passed = test_percentage_calculation()
    
    # 演示用法
    demonstrate_usage()
    
    # 汇总
    print("\n" + "=" * 60)
    if test_passed:
        print("✓ 测试通过！百分比计算功能正常工作")
    else:
        print("✗ 测试失败，请检查计算逻辑")
    print("=" * 60)
    
    print("\n功能说明：")
    print("1. 百分比计算已集成到积分引擎中")
    print("2. API响应将自动包含 dimension_percentages 字段")
    print("3. 可通过 calculate_percentage 函数独立计算百分比")

if __name__ == "__main__":
    main()