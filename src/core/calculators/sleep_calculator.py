"""
睡眠维度积分计算器
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
from .base import DimensionCalculator
from ...models.health_data import DailyHealthSummary, ScoreDimension
from ...utils.logger import logger


class SleepCalculator(DimensionCalculator):
    """睡眠维度计算器"""
    
    def __init__(self):
        super().__init__()
        self.dimension = ScoreDimension.SLEEP
    
    def get_rules(self) -> Dict:
        """获取睡眠维度规则"""
        return {
            'easy': {
                'target_hours': 7.5,
                'min_hours': 6.0,
                'base_points': 1000,
                'deduction_per_minute': 5  # 每少1分钟扣5分
            },
            'medium': {
                'deep_sleep_hours': 1.5,
                'rem_sleep_hours': 1.5,
                'base_points': 2000
            },
            'hard': {
                'sleep_before': '23:30',  # 11:30 PM
                'wake_before': '07:30',   # 7:30 AM
                'base_points': 4000,
                'requires_easy_medium': True
            },
            'super_hard': {
                'continuous_days': 15,
                'base_points': 10000
            },
            'chain_punishment': {
                'condition': 'sleep_hours < 6 for 3 days',
                'affects': ['sleep', 'exercise', 'cognition'],
                'recovery': 'sleep_hours >= 7.5 for 6 days',
                'recovery_points': 5000
            }
        }
    
    def calculate(self, health_data: DailyHealthSummary) -> Dict[str, int]:
        """计算睡眠积分"""
        scores = {
            'easy': 0,
            'medium': 0,
            'hard': 0,
            'super_hard': 0,
            'total': 0
        }
        
        # 易：睡够7.5小时
        scores['easy'] = self._calculate_easy(health_data)
        
        # 中：深度睡眠>1.5小时 + REM睡眠>1.5小时
        scores['medium'] = self._calculate_medium(health_data)
        
        # 难：在满足易+中的基础上，11:30前入睡，7:30前起床
        if scores['easy'] > 0 and scores['medium'] > 0:
            scores['hard'] = self._calculate_hard(health_data)
        
        # 超难：易中难持续15天
        # TODO: 需要历史数据支持
        
        # 计算总分
        scores['total'] = sum([scores[k] for k in ['easy', 'medium', 'hard', 'super_hard']])
        
        return scores
    
    def _calculate_easy(self, health_data: DailyHealthSummary) -> int:
        """计算易难度积分"""
        if not health_data.sleep_hours:
            return 0
        
        rules = self.rules['easy']
        sleep_hours = health_data.sleep_hours
        
        # 如果睡眠不足6小时，没有积分
        if sleep_hours < rules['min_hours']:
            logger.info(f"睡眠不足{rules['min_hours']}小时，无积分")
            return 0
        
        # 如果睡够7.5小时，获得满分
        if sleep_hours >= rules['target_hours']:
            return rules['base_points']
        
        # 6-7.5小时之间，按比例扣分
        minutes_short = (rules['target_hours'] - sleep_hours) * 60
        deduction = int(minutes_short * rules['deduction_per_minute'])
        score = max(0, rules['base_points'] - deduction)
        
        logger.info(f"睡眠{sleep_hours:.1f}小时，获得{score}分")
        return score
    
    def _calculate_medium(self, health_data: DailyHealthSummary) -> int:
        """计算中难度积分"""
        # TODO: 当前HealthKit数据中没有深度睡眠和REM睡眠的详细数据
        # 暂时跳过此计算
        logger.info("深度睡眠和REM睡眠数据暂不可用")
        return 0
    
    def _calculate_hard(self, health_data: DailyHealthSummary) -> int:
        """计算难难度积分"""
        # TODO: 需要获取具体的入睡和起床时间
        # 当前数据结构中没有这些信息
        logger.info("入睡和起床时间数据暂不可用")
        return 0
    
    def check_chain_punishment(self, history_data: Dict[str, DailyHealthSummary]) -> Optional[Dict]:
        """检查连锁惩罚"""
        if len(history_data) < 3:
            return None
        
        # 获取最近3天的数据
        recent_dates = sorted(history_data.keys())[-3:]
        sleep_insufficient_days = 0
        
        for date in recent_dates:
            summary = history_data[date]
            if summary.sleep_hours and summary.sleep_hours < 6:
                sleep_insufficient_days += 1
        
        # 如果连续3天睡眠不足6小时
        if sleep_insufficient_days >= 3:
            return {
                'type': 'sleep_insufficient',
                'message': '连续3天睡眠不足6小时',
                'affects': ['sleep', 'exercise', 'cognition'],
                'recovery_condition': '连续6天睡够7.5小时',
                'recovery_points': 5000
            }
        
        return None