"""
运动维度积分计算器
"""
from typing import Dict, Optional
from .base import DimensionCalculator
from ...models.health_data import DailyHealthSummary, ScoreDimension
from ...utils.logger import logger


class ExerciseCalculator(DimensionCalculator):
    """运动维度计算器"""
    
    def __init__(self):
        super().__init__()
        self.dimension = ScoreDimension.EXERCISE
    
    def get_rules(self) -> Dict:
        """获取运动维度规则"""
        return {
            'easy': {
                'steps': {
                    'points_per_step': 0.05,
                    'max_steps': 30000,
                    'max_points': 1500  # 30000 * 0.05
                },
                'stand': {
                    'points_per_hour': 80,
                    'max_hours': 16,
                    'max_points': 1280  # 16 * 80
                }
            },
            'medium': {
                'zone2_or_strength': {
                    'points_per_30min': 800,
                    'max_hours': 2,
                    'max_points': 3200  # 4 * 800
                }
            },
            'hard': {
                'weekly_variety': {
                    'required_types': ['aerobic', 'strength', 'flexibility'],
                    'daily_points': 3500
                }
            },
            'super_hard': {
                'different_exercise_28days': {
                    'continuous_days': 28,
                    'daily_points': 12000
                }
            }
        }
    
    def calculate(self, health_data: DailyHealthSummary) -> Dict[str, int]:
        """计算运动积分"""
        scores = {
            'easy': 0,
            'medium': 0,
            'hard': 0,
            'super_hard': 0,
            'total': 0
        }
        
        # 易：步数 + 站立
        scores['easy'] = self._calculate_easy(health_data)
        
        # 中：Zone 2/力量运动/其他运动
        scores['medium'] = self._calculate_medium(health_data)
        
        # 难：每周包含3类运动
        # TODO: 需要一周的数据
        
        # 超难：每天都做与前2天不一样的运动并持续28天
        # TODO: 需要历史数据
        
        # 计算总分
        scores['total'] = sum([scores[k] for k in ['easy', 'medium', 'hard', 'super_hard']])
        
        return scores
    
    def _calculate_easy(self, health_data: DailyHealthSummary) -> int:
        """计算易难度积分"""
        total_score = 0
        
        # 步数积分
        if health_data.steps:
            step_rules = self.rules['easy']['steps']
            steps = min(health_data.steps, step_rules['max_steps'])
            step_score = int(steps * step_rules['points_per_step'])
            total_score += step_score
            logger.info(f"步数{health_data.steps}，获得{step_score}分")
        
        # 站立积分
        if health_data.stand_hours:
            stand_rules = self.rules['easy']['stand']
            hours = min(health_data.stand_hours, stand_rules['max_hours'])
            stand_score = hours * stand_rules['points_per_hour']
            total_score += stand_score
            logger.info(f"站立{health_data.stand_hours}小时，获得{stand_score}分")
        
        return total_score
    
    def _calculate_medium(self, health_data: DailyHealthSummary) -> int:
        """计算中难度积分"""
        if not health_data.exercise_minutes:
            return 0
        
        rules = self.rules['medium']['zone2_or_strength']
        
        # 将运动分钟数转换为30分钟的块数
        blocks = min(health_data.exercise_minutes // 30, 4)  # 最多2小时
        score = blocks * rules['points_per_30min']
        
        logger.info(f"运动{health_data.exercise_minutes}分钟，获得{score}分")
        return score
    
    def check_chain_punishment(self, history_data: Dict[str, DailyHealthSummary]) -> Optional[Dict]:
        """检查连锁惩罚"""
        if len(history_data) < 5:
            return None
        
        # 检查最近5天是否都没有达到3000步或运动
        recent_dates = sorted(history_data.keys())[-5:]
        inactive_days = 0
        
        for date in recent_dates:
            summary = history_data[date]
            steps = summary.steps or 0
            exercise = summary.exercise_minutes or 0
            
            if steps < 3000 and exercise == 0:
                inactive_days += 1
        
        if inactive_days >= 5:
            return {
                'type': 'inactive',
                'message': '连续5天没有达到3000步或运动',
                'affects': ['exercise', 'cognition', 'mental', 'prevention'],
                'recovery_condition': '连续3天回归运动',
                'recovery_points': 3000
            }
        
        return None