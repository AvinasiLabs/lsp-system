"""
心理维度积分计算器
"""
from typing import Dict, Optional
from .base import DimensionCalculator
from ...models.health_data import DailyHealthSummary, ScoreDimension
from ...utils.logger import logger


class MentalCalculator(DimensionCalculator):
    """心理维度计算器"""
    
    def __init__(self):
        super().__init__()
        self.dimension = ScoreDimension.MENTAL
        self.baseline_hrv = None  # 应该从用户历史数据计算
    
    def get_rules(self) -> Dict:
        """获取心理维度规则"""
        return {
            'easy': {
                'rem_sleep': {
                    'min_hours': 1.2,
                    'points': 1000
                }
            },
            'medium': {
                'hrv': {
                    'points': 3000  # HRV >= 平均值时获得
                }
            }
        }
    
    def calculate(self, health_data: DailyHealthSummary) -> Dict[str, int]:
        """计算心理积分"""
        scores = {
            'easy': 0,
            'medium': 0,
            'hard': 0,
            'super_hard': 0,
            'total': 0
        }
        
        # 易：REM快速眼动睡眠 >1.2hr/day
        # TODO: 当前没有REM睡眠数据
        
        # 中：HRV ≥ 平均值
        scores['medium'] = self._calculate_medium(health_data)
        
        # 计算总分
        scores['total'] = scores['medium']
        
        return scores
    
    def _calculate_medium(self, health_data: DailyHealthSummary) -> int:
        """计算中难度积分（HRV）"""
        if not health_data.hrv:
            return 0
        
        # TODO: 应该基于用户的历史HRV平均值
        # 暂时使用固定值作为示例
        if not self.baseline_hrv:
            self.baseline_hrv = 50  # 毫秒，一般成年人的平均值
        
        if health_data.hrv >= self.baseline_hrv:
            score = self.rules['medium']['hrv']['points']
            logger.info(f"HRV {health_data.hrv}ms >= 基线 {self.baseline_hrv}ms，获得{score}分")
            return score
        else:
            logger.info(f"HRV {health_data.hrv}ms < 基线 {self.baseline_hrv}ms，无积分")
            return 0