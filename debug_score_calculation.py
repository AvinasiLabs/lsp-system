#!/usr/bin/env python3
"""
调试积分计算错误
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from src.core.score_engine import ScoreEngine
from src.utils.logger import logger

def test_score_calculation():
    """测试积分计算"""
    try:
        # 初始化积分引擎
        score_engine = ScoreEngine(auto_save=False)
        
        # 测试参数
        user_id = "user_001"
        test_date = datetime(2025, 7, 8)
        
        print(f"测试积分计算：用户={user_id}, 日期={test_date}")
        
        # 直接调用计算方法
        result = score_engine.calculate_daily_score(user_id, test_date)
        
        print("\n计算成功！")
        print(f"总积分: {result['total_score']}")
        print(f"维度积分: {result['dimension_scores']}")
        
    except Exception as e:
        print(f"\n计算失败！")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        
        # 打印详细的堆栈跟踪
        import traceback
        print("\n详细错误信息:")
        traceback.print_exc()

if __name__ == "__main__":
    test_score_calculation()