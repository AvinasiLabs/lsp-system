"""
积分计算引擎
整合所有维度的计算器，提供统一的积分计算接口
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from ..models.health_data import DailyHealthSummary, ScoreDimension
from ..services.health_data_service import HealthDataService
from .calculators.sleep_calculator import SleepCalculator
from .calculators.exercise_calculator import ExerciseCalculator
from .calculators.diet_calculator import DietCalculator
from .calculators.mental_calculator import MentalCalculator
from ..utils.logger import logger


class ScoreEngine:
    """积分计算引擎"""
    
    def __init__(self):
        self.health_service = HealthDataService()
        
        # 初始化所有计算器
        self.calculators = {
            ScoreDimension.SLEEP: SleepCalculator(),
            ScoreDimension.EXERCISE: ExerciseCalculator(),
            ScoreDimension.DIET: DietCalculator(),
            ScoreDimension.MENTAL: MentalCalculator(),
            # TODO: 添加其他维度计算器
        }
        
        # 用户等级（暂时硬编码为BRONZE）
        self.user_level = 'BRONZE'
    
    def calculate_daily_score(self, user_id: str, date: datetime) -> Dict:
        """
        计算指定日期的积分
        
        Args:
            user_id: 用户ID
            date: 日期
            
        Returns:
            积分结果字典
        """
        # 获取当日健康数据汇总
        health_summary = self.health_service.get_daily_summary(user_id, date)
        
        # 获取历史数据（用于连锁反应检查）
        history_data = self._get_history_data(user_id, date, days=7)
        
        # 计算各维度积分
        dimension_scores = {}
        total_score = 0
        
        for dimension, calculator in self.calculators.items():
            # 计算基础积分
            scores = calculator.calculate(health_summary)
            
            # 检查连锁惩罚
            punishment = calculator.check_chain_punishment(history_data)
            if punishment:
                logger.warning(f"{dimension} 触发连锁惩罚: {punishment['message']}")
                # TODO: 实现惩罚逻辑
            
            # 应用等级倍数
            scores['total'] = calculator.apply_level_multiplier(scores['total'], self.user_level)
            
            dimension_scores[dimension.value] = scores
            total_score += scores['total']
        
        return {
            'user_id': user_id,
            'date': date.isoformat(),
            'health_summary': health_summary.dict(),
            'dimension_scores': dimension_scores,
            'total_score': total_score,
            'user_level': self.user_level,
            'timestamp': datetime.now().isoformat()
        }
    
    def calculate_date_range_scores(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        计算日期范围内的积分
        
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            每日积分列表
        """
        scores = []
        current_date = start_date
        
        while current_date <= end_date:
            try:
                daily_score = self.calculate_daily_score(user_id, current_date)
                scores.append(daily_score)
            except Exception as e:
                logger.error(f"计算{current_date}积分失败: {e}")
            
            current_date += timedelta(days=1)
        
        return scores
    
    def get_available_dimensions(self, user_id: str = "default_user") -> Dict[str, bool]:
        """
        获取可用的积分维度
        
        Returns:
            维度可用性字典
        """
        available = {}
        
        # 检查每个维度是否有数据
        test_date = datetime.now()
        health_summary = self.health_service.get_daily_summary(user_id, test_date)
        
        available[ScoreDimension.SLEEP] = health_summary.sleep_hours is not None
        available[ScoreDimension.EXERCISE] = any([
            health_summary.steps is not None,
            health_summary.exercise_minutes is not None,
            health_summary.stand_hours is not None
        ])
        available[ScoreDimension.DIET] = health_summary.water_ml is not None
        available[ScoreDimension.MENTAL] = health_summary.hrv is not None
        
        # 其他维度暂时标记为不可用
        for dimension in ScoreDimension:
            if dimension not in available:
                available[dimension] = False
        
        return available
    
    def _get_history_data(self, user_id: str, date: datetime, days: int = 7) -> Dict[str, DailyHealthSummary]:
        """获取历史数据"""
        history = {}
        
        for i in range(1, days + 1):
            past_date = date - timedelta(days=i)
            try:
                summary = self.health_service.get_daily_summary(user_id, past_date)
                history[past_date.strftime('%Y-%m-%d')] = summary
            except Exception as e:
                logger.error(f"获取{past_date}历史数据失败: {e}")
        
        return history