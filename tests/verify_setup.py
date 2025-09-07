#!/usr/bin/env python3
"""
快速验证测试设置的脚本
检查所有测试脚本是否能正确导入和基本功能
"""

import os
import sys
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试关键模块导入"""
    print("🔍 测试关键模块导入...")
    
    try:
        from src.core.score_config import DIMENSION_MAX_SCORES, calculate_percentage
        print("✅ score_config 导入成功")
        
        # 测试配置
        sleep_max = DIMENSION_MAX_SCORES.get('sleep', {}).get('easy', 0)
        print(f"   睡眠易难度最高分: {sleep_max}")
        
        # 测试百分比计算
        percentage = calculate_percentage(500, 'sleep', 'easy')
        print(f"   百分比计算测试: {percentage}%")
        
    except Exception as e:
        print(f"❌ score_config 导入失败: {e}")
        return False
    
    try:
        from src.core.score_engine import ScoreEngine
        print("✅ ScoreEngine 导入成功")
        
        # 创建引擎实例
        engine = ScoreEngine(auto_save=False)
        print("   引擎实例创建成功")
        
    except Exception as e:
        print(f"❌ ScoreEngine 导入失败: {e}")
        return False
    
    try:
        from src.models.health_data import DailyHealthSummary
        print("✅ DailyHealthSummary 导入成功")
        
        # 创建测试数据
        health_data = DailyHealthSummary(sleep_hours=8.0)
        print(f"   健康数据创建成功: {health_data.sleep_hours} 小时睡眠")
        
    except Exception as e:
        print(f"❌ DailyHealthSummary 导入失败: {e}")
        return False
    
    return True


def test_basic_calculation():
    """测试基本积分计算"""
    print("\n🧮 测试基本积分计算...")
    
    try:
        from src.core.score_engine import ScoreEngine
        from src.models.health_data import DailyHealthSummary
        from datetime import datetime
        
        engine = ScoreEngine(auto_save=False)
        
        # 创建测试健康数据
        health_data = DailyHealthSummary(
            sleep_hours=7.5,
            steps=10000,
            water_ml=2000
        )
        
        # 计算积分
        result = engine.calculate_daily_score(
            user_id="test_user",
            date=datetime.now(),
            save_to_db=False
        )
        
        total_score = result.get('total_score', 0)
        dimension_scores = result.get('dimension_scores', {})
        dimension_percentages = result.get('dimension_percentages', {})
        
        print(f"✅ 积分计算成功")
        print(f"   总积分: {total_score}")
        print(f"   维度数量: {len(dimension_scores)}")
        print(f"   包含百分比: {'是' if dimension_percentages else '否'}")
        
        # 显示各维度积分
        for dimension, scores in dimension_scores.items():
            print(f"   {dimension}: {scores.get('total', 0)} 分")
        
        return True
        
    except Exception as e:
        print(f"❌ 积分计算失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_structure():
    """测试文件结构"""
    print("\n📁 检查测试文件结构...")
    
    test_files = [
        "test_documentation_validity.py",
        "test_sleep_analysis_complete.py", 
        "test_score_percentage_complete.py",
        "test_integration_complete.py",
        "generate_doc_coverage.py",
        "run_all_tests.py",
        "README.md"
    ]
    
    missing_files = []
    for filename in test_files:
        filepath = Path(__file__).parent / filename
        if filepath.exists():
            print(f"✅ {filename}")
        else:
            print(f"❌ {filename} 缺失")
            missing_files.append(filename)
    
    # 检查reports目录
    reports_dir = Path(__file__).parent / "reports"
    if reports_dir.exists():
        print("✅ reports 目录存在")
    else:
        print("❌ reports 目录缺失")
        reports_dir.mkdir(exist_ok=True)
        print("   已创建 reports 目录")
    
    return len(missing_files) == 0


def main():
    """主函数"""
    print("🚀 LSP系统测试设置验证")
    print("=" * 60)
    
    all_passed = True
    
    # 测试文件结构
    if not test_file_structure():
        all_passed = False
    
    # 测试导入
    if not test_imports():
        all_passed = False
    
    # 测试基本计算
    if not test_basic_calculation():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有验证通过！测试环境设置正确")
        print("\n💡 现在可以运行完整测试套件:")
        print("   python3 tests/run_all_tests.py")
    else:
        print("⚠️  验证发现问题，请先修复再运行测试")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())