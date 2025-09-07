"""
积分配置文件
定义各维度的最高分数配置
"""

from typing import Dict

# 各维度的最高分数配置
DIMENSION_MAX_SCORES: Dict[str, Dict[str, int]] = {
    "sleep": {
        "easy": 1000,
        "medium": 2000,
        "hard": 4000,
        "super_hard": 10000,
        "total": 17000  # 所有难度的总和
    },
    "exercise": {
        "easy": 2780,  # 步数(1500) + 站立(1280)
        "medium": 3200,
        "hard": 3500,
        "super_hard": 12000,
        "total": 21480
    },
    "diet": {
        "easy": 1000,
        "medium": 0,  # 暂未实现
        "hard": 0,    # 暂未实现
        "super_hard": 0,  # 暂未实现
        "total": 1000
    },
    "mental": {
        "easy": 1000,
        "medium": 3000,
        "hard": 0,    # 暂未实现
        "super_hard": 0,  # 暂未实现
        "total": 4000
    },
    "environment": {
        "easy": 0,    # 暂未实现
        "medium": 0,  # 暂未实现
        "hard": 0,    # 暂未实现
        "super_hard": 0,  # 暂未实现
        "total": 0
    },
    "social": {
        "easy": 0,    # 暂未实现
        "medium": 0,  # 暂未实现
        "hard": 0,    # 暂未实现
        "super_hard": 0,  # 暂未实现
        "total": 0
    },
    "cognition": {
        "easy": 0,    # 暂未实现
        "medium": 0,  # 暂未实现
        "hard": 0,    # 暂未实现
        "super_hard": 0,  # 暂未实现
        "total": 0
    },
    "prevention": {
        "easy": 0,    # 暂未实现
        "medium": 0,  # 暂未实现
        "hard": 0,    # 暂未实现
        "super_hard": 0,  # 暂未实现
        "total": 0
    }
}

def get_dimension_max_score(dimension: str, difficulty: str = "total") -> int:
    """
    获取指定维度和难度的最高分数
    
    Args:
        dimension: 维度名称 (如 'sleep', 'exercise' 等)
        difficulty: 难度等级 ('easy', 'medium', 'hard', 'super_hard', 'total')
    
    Returns:
        最高分数，如果维度或难度不存在则返回0
    """
    dimension_lower = dimension.lower()
    if dimension_lower in DIMENSION_MAX_SCORES:
        return DIMENSION_MAX_SCORES[dimension_lower].get(difficulty, 0)
    return 0

def calculate_percentage(actual_score: int, dimension: str, difficulty: str = "total") -> float:
    """
    计算实际得分占最高分的百分比
    
    Args:
        actual_score: 实际得分
        dimension: 维度名称
        difficulty: 难度等级
    
    Returns:
        百分比 (0-100)
    """
    max_score = get_dimension_max_score(dimension, difficulty)
    if max_score == 0:
        return 0.0
    return round((actual_score / max_score) * 100, 2)