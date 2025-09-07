#!/usr/bin/env python
"""
测试积分百分比计算功能
验证新增的百分比计算是否正确工作
"""

import sys
import os
from datetime import datetime, timedelta
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.score_engine import ScoreEngine
from src.core.score_config import DIMENSION_MAX_SCORES, calculate_percentage
from src.utils.logger import logger


def test_percentage_calculation():
    """测试百分比计算函数"""
    logger.info("=" * 50)
    logger.info("测试百分比计算函数")
    logger.info("=" * 50)
    
    # 测试各种维度和得分
    test_cases = [
        ("sleep", 1000, "easy", 100.0),     # 满分情况
        ("sleep", 500, "easy", 50.0),       # 50%情况
        ("sleep", 8500, "total", 50.0),     # 总分50%情况
        ("exercise", 1500, "easy", 53.96),  # 运动easy维度
        ("diet", 100, "easy", 10.0),        # 饮食10%情况
        ("mental", 1500, "medium", 50.0),   # 心理medium 50%
    ]
    
    all_passed = True
    for dimension, score, difficulty, expected in test_cases:
        actual = calculate_percentage(score, dimension, difficulty)
        passed = abs(actual - expected) < 0.01  # 允许小数点误差
        status = "✓" if passed else "✗"
        logger.info(f"{status} {dimension}/{difficulty}: {score}分 -> {actual}% (期望: {expected}%)")
        if not passed:
            all_passed = False
    
    return all_passed


def test_score_engine_with_percentage():
    """测试积分引擎的百分比计算"""
    logger.info("\n" + "=" * 50)
    logger.info("测试积分引擎百分比计算")
    logger.info("=" * 50)
    
    # 创建积分引擎（不自动保存）
    engine = ScoreEngine(auto_save=False)
    
    # 测试用户和日期
    test_user = "test_percentage_user"
    test_date = datetime(2025, 7, 18)
    
    # 计算积分
    result = engine.calculate_daily_score(test_user, test_date)
    
    # 检查是否包含百分比数据
    if 'dimension_percentages' not in result:
        logger.error("✗ 结果中缺少 dimension_percentages 字段")
        return False
    
    logger.info("✓ 结果包含 dimension_percentages 字段")
    
    # 打印各维度的积分和百分比
    logger.info("\n维度积分和百分比详情:")
    logger.info("-" * 40)
    
    for dimension in result['dimension_scores'].keys():
        scores = result['dimension_scores'][dimension]
        percentages = result['dimension_percentages'][dimension]
        
        logger.info(f"\n{dimension}维度:")
        logger.info(f"  总分: {scores['total']}分 ({percentages['total']}%)")
        logger.info(f"  - 易: {scores['easy']}分 ({percentages['easy']}%)")
        logger.info(f"  - 中: {scores['medium']}分 ({percentages['medium']}%)")
        logger.info(f"  - 难: {scores['hard']}分 ({percentages['hard']}%)")
        logger.info(f"  - 超难: {scores['super_hard']}分 ({percentages['super_hard']}%)")
    
    return True


def test_api_endpoints():
    """测试API端点是否返回百分比"""
    logger.info("\n" + "=" * 50)
    logger.info("测试API端点百分比返回")
    logger.info("=" * 50)
    
    import requests
    
    # API基础URL
    base_url = "http://localhost:8000/lsp/api/v1"
    
    # 测试用户
    test_user = "test_user"
    
    try:
        # 测试有效积分端点
        logger.info("\n测试 /scores/valid 端点...")
        response = requests.get(
            f"{base_url}/scores/valid",
            params={"user_id": test_user}
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'dimension_percentages' in data:
                logger.info("✓ /scores/valid 端点返回百分比数据")
                logger.info(f"  百分比数据: {json.dumps(data['dimension_percentages'], indent=2, ensure_ascii=False)}")
            else:
                logger.warning("✗ /scores/valid 端点缺少百分比数据")
        else:
            logger.error(f"✗ API调用失败: {response.status_code}")
        
        # 测试月度汇总端点
        logger.info("\n测试 /scores/summary 端点...")
        current_date = datetime.now()
        response = requests.get(
            f"{base_url}/scores/summary/{current_date.year}/{current_date.month}",
            params={"user_id": test_user}
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'dimension_percentages' in data:
                logger.info("✓ /scores/summary 端点返回百分比数据")
                logger.info(f"  百分比数据: {json.dumps(data['dimension_percentages'], indent=2, ensure_ascii=False)}")
            else:
                logger.warning("✗ /scores/summary 端点缺少百分比数据")
        else:
            logger.error(f"✗ API调用失败: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        logger.warning("⚠ 无法连接到API服务器，请确保服务器正在运行")
        logger.info("  提示: 运行 'python start_server.py' 启动服务器")
        return False
    except Exception as e:
        logger.error(f"✗ 测试API时出错: {e}")
        return False
    
    return True


def display_max_scores():
    """显示各维度的最高分配置"""
    logger.info("\n" + "=" * 50)
    logger.info("各维度最高分配置")
    logger.info("=" * 50)
    
    for dimension, scores in DIMENSION_MAX_SCORES.items():
        if scores['total'] > 0:  # 只显示已实现的维度
            logger.info(f"\n{dimension}维度:")
            logger.info(f"  易: {scores['easy']}分")
            logger.info(f"  中: {scores['medium']}分")
            logger.info(f"  难: {scores['hard']}分")
            logger.info(f"  超难: {scores['super_hard']}分")
            logger.info(f"  总计: {scores['total']}分")


def main():
    """主测试函数"""
    logger.info("\n" + "=" * 60)
    logger.info("开始测试积分百分比计算功能")
    logger.info("=" * 60)
    
    # 显示最高分配置
    display_max_scores()
    
    # 运行各项测试
    tests_passed = []
    
    # 测试1: 百分比计算函数
    tests_passed.append(test_percentage_calculation())
    
    # 测试2: 积分引擎
    tests_passed.append(test_score_engine_with_percentage())
    
    # 测试3: API端点（可选）
    logger.info("\n" + "-" * 50)
    logger.info("尝试测试API端点...")
    test_api_endpoints()
    
    # 汇总结果
    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)
    
    if all(tests_passed):
        logger.info("✓ 所有测试通过！百分比计算功能正常工作")
    else:
        logger.warning("✗ 部分测试失败，请检查日志")
    
    logger.info("\n提示:")
    logger.info("1. 运行 'python start_server.py' 启动API服务器")
    logger.info("2. 访问 http://localhost:8000/lsp/docs 查看API文档")
    logger.info("3. 百分比数据现在会在所有积分查询中返回")


if __name__ == "__main__":
    main()