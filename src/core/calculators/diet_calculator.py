"""
饮食维度积分计算器
"""
from typing import Dict, Optional
from .base import DimensionCalculator
from ...models.health_data import DailyHealthSummary, ScoreDimension
from ...utils.logger import logger


class DietCalculator(DimensionCalculator):
    """饮食维度计算器"""
    
    def __init__(self):
        super().__init__()
        self.dimension = ScoreDimension.DIET
    
    def get_rules(self) -> Dict:
        """获取饮食维度规则"""
        return {
            'easy': {
                'water': {
                    'points_per_hour': 100,
                    'min_ml_per_hour': 100,  # 假设每小时至少喝100ml算一次
                    'max_hours': 10
                }
            },
            'medium': {
                # 需要食物拍照识别，暂时无法实现
            },
            'hard': {
                # 需要CGM数据，暂时无法实现
            }
        }
    
    def calculate(self, health_data: DailyHealthSummary) -> Dict[str, int]:
        """计算饮食积分"""
        scores = {
            'easy': 0,
            'medium': 0,
            'hard': 0,
            'super_hard': 0,
            'total': 0
        }
        
        # 易：喝水
        scores['easy'] = self._calculate_easy(health_data)
        
        # 中难度和高难度需要额外数据源，暂时跳过
        logger.info("食物识别和血糖数据暂不可用")
        
        # 计算总分
        scores['total'] = scores['easy']
        
        return scores
    
    def _calculate_easy(self, health_data: DailyHealthSummary) -> int:
        """计算易难度积分（喝水）"""
        if not health_data.water_ml:
            return 0
        
        rules = self.rules['easy']['water']
        
        # 估算喝水的小时数（假设每次记录至少100ml）
        # 这是一个简化的计算，实际应该基于详细的时间记录
        estimated_hours = min(int(health_data.water_ml / rules['min_ml_per_hour']), rules['max_hours'])
        score = estimated_hours * rules['points_per_hour']
        
        logger.info(f"饮水{health_data.water_ml}ml，估计{estimated_hours}小时，获得{score}分")
        return score