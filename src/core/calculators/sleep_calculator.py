"""
睡眠维度积分计算器
"""
from typing import Dict, Optional
from datetime import datetime, timedelta, time
from .base import DimensionCalculator
from ...models.health_data import DailyHealthSummary, ScoreDimension
from ...services.sleep_analysis_service import SleepAnalysisService
from ...utils.logger import logger


class SleepCalculator(DimensionCalculator):
    """睡眠维度计算器"""
    
    def __init__(self):
        super().__init__()
        self.dimension = ScoreDimension.SLEEP
        self.sleep_service = SleepAnalysisService()
        self.user_id = None  # 将在计算时设置
        self.current_date = None  # 将在计算时设置
    
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
    
    def calculate(self, health_data: DailyHealthSummary, user_id: str = None, date: datetime = None) -> Dict[str, int]:
        """
        计算睡眠积分
        
        Args:
            health_data: 每日健康数据汇总
            user_id: 用户ID（用于查询睡眠阶段数据）
            date: 日期（用于查询睡眠阶段数据）
        """
        # 设置用户ID和日期
        self.user_id = user_id or 'default_user'
        self.current_date = date or datetime.now()
        
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
        scores['medium'] = self._calculate_medium_with_stages()
        
        # 难：在满足易+中的基础上，11:30前入睡，7:30前起床
        if scores['easy'] > 0 and scores['medium'] > 0:
            scores['hard'] = self._calculate_hard_with_time_limits()
        
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
            logger.info(f"睡眠{sleep_hours:.1f}小时，达到目标，获得{rules['base_points']}分")
            return rules['base_points']
        
        # 6-7.5小时之间，按比例扣分
        minutes_short = (rules['target_hours'] - sleep_hours) * 60
        deduction = int(minutes_short * rules['deduction_per_minute'])
        score = max(0, rules['base_points'] - deduction)
        
        logger.info(f"睡眠{sleep_hours:.1f}小时，获得{score}分")
        return score
    
    def _calculate_medium_with_stages(self) -> int:
        """
        计算中难度积分（深度睡眠和REM睡眠）
        使用睡眠阶段分析服务获取数据
        """
        if not self.user_id or not self.current_date:
            logger.info("缺少用户ID或日期，无法计算睡眠阶段积分")
            return 0
        
        # 获取睡眠阶段分析
        # 优先使用Oura数据，因为它有完整的睡眠阶段信息
        analysis = self.sleep_service.analyze_sleep_stages(
            self.user_id, 
            self.current_date,
            source_filter='Oura'  # 可以改为None来使用所有数据源
        )
        
        if not analysis['has_data']:
            logger.info("没有睡眠阶段数据，中级别积分为0")
            return 0
        
        rules = self.rules['medium']
        deep_sleep_hours = analysis['deep_sleep_hours']
        rem_sleep_hours = analysis['rem_sleep_hours']
        
        logger.info(f"深度睡眠: {deep_sleep_hours:.2f}小时, REM睡眠: {rem_sleep_hours:.2f}小时")
        
        # 检查是否满足条件
        meets_deep_sleep = deep_sleep_hours >= rules['deep_sleep_hours']
        meets_rem_sleep = rem_sleep_hours >= rules['rem_sleep_hours']
        
        if meets_deep_sleep and meets_rem_sleep:
            logger.info(f"深度睡眠和REM睡眠都达标，获得{rules['base_points']}分")
            return rules['base_points']
        elif meets_deep_sleep:
            # 只满足深度睡眠，获得一半分数
            score = rules['base_points'] // 2
            logger.info(f"仅深度睡眠达标，获得{score}分")
            return score
        elif meets_rem_sleep:
            # 只满足REM睡眠，获得一半分数
            score = rules['base_points'] // 2
            logger.info(f"仅REM睡眠达标，获得{score}分")
            return score
        else:
            logger.info("深度睡眠和REM睡眠都未达标，中级别积分为0")
            return 0
    
    def _calculate_hard_with_time_limits(self) -> int:
        """
        计算难难度积分（入睡和起床时间限制）
        """
        if not self.user_id or not self.current_date:
            logger.info("缺少用户ID或日期，无法计算时间限制积分")
            return 0
        
        # 获取睡眠时间详情
        time_details = self.sleep_service.get_sleep_time_details(
            self.user_id,
            self.current_date,
            source_filter='Oura'  # 可以改为None来使用所有数据源
        )
        
        if not time_details['has_data']:
            logger.info("没有睡眠时间数据，难级别积分为0")
            return 0
        
        rules = self.rules['hard']
        
        # 检查是否满足时间要求
        meets_sleep_time = time_details['meets_sleep_target']  # 23:30前入睡
        meets_wake_time = time_details['meets_wake_target']    # 7:30前起床
        
        if time_details['sleep_time']:
            sleep_time_str = time_details['sleep_time'].strftime('%H:%M')
            logger.info(f"入睡时间: {sleep_time_str}, 目标: 23:30前")
        
        if time_details['wake_time']:
            wake_time_str = time_details['wake_time'].strftime('%H:%M')
            logger.info(f"起床时间: {wake_time_str}, 目标: 07:30前")
        
        if meets_sleep_time and meets_wake_time:
            logger.info(f"入睡和起床时间都达标，获得{rules['base_points']}分")
            return rules['base_points']
        elif meets_sleep_time:
            # 只满足入睡时间，获得一半分数
            score = rules['base_points'] // 2
            logger.info(f"仅入睡时间达标，获得{score}分")
            return score
        elif meets_wake_time:
            # 只满足起床时间，获得一半分数
            score = rules['base_points'] // 2
            logger.info(f"仅起床时间达标，获得{score}分")
            return score
        else:
            logger.info("入睡和起床时间都未达标，难级别积分为0")
            return 0
    
    def _calculate_medium(self, health_data: DailyHealthSummary) -> int:
        """
        旧的中难度积分计算（保留兼容性）
        如果没有user_id和date，使用此方法
        """
        # 尝试使用新方法
        if self.user_id and self.current_date:
            return self._calculate_medium_with_stages()
        
        # 回退到旧方法
        logger.info("深度睡眠和REM睡眠数据暂不可用（旧方法）")
        return 0
    
    def _calculate_hard(self, health_data: DailyHealthSummary) -> int:
        """
        旧的难难度积分计算（保留兼容性）
        如果没有user_id和date，使用此方法
        """
        # 尝试使用新方法
        if self.user_id and self.current_date:
            return self._calculate_hard_with_time_limits()
        
        # 回退到旧方法
        logger.info("入睡和起床时间数据暂不可用（旧方法）")
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