"""
积分计算器基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
from datetime import datetime
from ...models.health_data import DailyHealthSummary, ScoreDimension


class DimensionCalculator(ABC):
    """维度计算器抽象基类"""
    
    def __init__(self):
        self.dimension = None
        self.rules = self.get_rules()
    
    @abstractmethod
    def calculate(self, health_data: DailyHealthSummary) -> Dict[str, int]:
        """
        计算该维度的积分
        
        Args:
            health_data: 每日健康数据汇总
            
        Returns:
            包含各难度等级积分的字典
            {
                'easy': 1000,
                'medium': 2000,
                'hard': 0,
                'super_hard': 0,
                'total': 3000
            }
        """
        pass
    
    @abstractmethod
    def get_rules(self) -> Dict:
        """
        获取该维度的规则配置
        
        Returns:
            规则配置字典
        """
        pass
    
    def check_chain_punishment(self, history_data: Dict[str, DailyHealthSummary]) -> Optional[Dict]:
        """
        检查连锁惩罚
        
        Args:
            history_data: 历史数据（日期字符串到汇总的映射）
            
        Returns:
            惩罚信息或None
        """
        # 子类可以重写此方法实现连锁惩罚逻辑
        return None
    
    def apply_level_multiplier(self, base_score: int, user_level: str) -> int:
        """
        应用等级倍数
        
        Args:
            base_score: 基础积分
            user_level: 用户等级
            
        Returns:
            应用倍数后的积分
        """
        multipliers = {
            'BRONZE': 1.0,
            'SILVER': 1.2,
            'GOLD': 1.5,
            'PLATINUM': 2.0,
            'DIAMOND': 3.0,
            'AMBASSADOR': 5.0
        }
        
        multiplier = multipliers.get(user_level, 1.0)
        return int(base_score * multiplier)