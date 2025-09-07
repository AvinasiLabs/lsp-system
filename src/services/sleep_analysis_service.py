"""
睡眠阶段分析服务
负责从数据库获取和分析睡眠阶段数据
"""
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
from ..db.postgresql import POSTGRES_POOL
from .sleep_data_source_manager import SleepDataSourceManager
from ..utils.logger import logger


class SleepAnalysisService:
    """睡眠阶段分析服务"""
    
    # 睡眠阶段映射
    SLEEP_STAGE_MAPPING = {
        'HKCategoryValueSleepAnalysisAwake': 'awake',
        'HKCategoryValueSleepAnalysisAsleepCore': 'core',
        'HKCategoryValueSleepAnalysisAsleepDeep': 'deep',
        'HKCategoryValueSleepAnalysisAsleepREM': 'rem',
        'HKCategoryValueSleepAnalysisInBed': 'in_bed',
        'HKCategoryValueSleepAnalysisAsleepUnspecified': 'unspecified'
    }
    
    def __init__(self):
        """初始化服务"""
        self.source_manager = SleepDataSourceManager()
    
    def get_sleep_stages_data(self, user_id: str, date: datetime, 
                             source_filter: Optional[str] = None) -> List[Dict]:
        """
        获取指定日期的睡眠阶段数据
        
        Args:
            user_id: 用户ID
            date: 日期
            source_filter: 数据源过滤器（如 'Oura', 'WHOOP'）
        
        Returns:
            睡眠阶段记录列表
        """
        try:
            # 计算睡眠时间范围（前一天晚上到当天早上）
            start_time = datetime.combine(date - timedelta(days=1), time(18, 0))  # 前一天18:00
            end_time = datetime.combine(date, time(12, 0))  # 当天12:00
            
            # 构建查询条件
            conditions = """
                type = %s 
                AND user_id = %s 
                AND start_date >= %s 
                AND end_date <= %s
            """
            params = ['HKCategoryTypeIdentifierSleepAnalysis', user_id, start_time, end_time]
            
            # 添加数据源过滤
            if source_filter:
                conditions += " AND source_name = %s"
                params.append(source_filter)
            
            conditions += " ORDER BY start_date"
            
            # 查询数据
            data = POSTGRES_POOL.select_data(
                table_name="health_metric",
                conditions=conditions,
                params=tuple(params)
            )
            
            if not data:
                logger.info(f"未找到{date.date()}的睡眠阶段数据")
                return []
            
            return data
            
        except Exception as e:
            logger.error(f"获取睡眠阶段数据失败: {e}")
            return []
    
    def analyze_sleep_stages(self, user_id: str, date: datetime,
                            source_filter: Optional[str] = None) -> Dict:
        """
        分析一晚的睡眠阶段
        
        Args:
            user_id: 用户ID
            date: 日期
            source_filter: 数据源过滤器（可选，如果不指定则自动选择最佳数据源）
        
        Returns:
            包含各阶段时长和睡眠时间的分析结果
        """
        # 如果没有指定数据源，自动选择最佳数据源
        if source_filter is None:
            sleep_data, used_source = self.source_manager.get_sleep_data_with_auto_source(user_id, date)
            logger.info(f"自动选择数据源: {used_source}")
        else:
            # 使用指定的数据源
            sleep_data = self.get_sleep_stages_data(user_id, date, source_filter)
            used_source = source_filter
        
        if not sleep_data:
            return {
                'date': date.date().isoformat(),
                'has_data': False,
                'stages_duration': {},
                'sleep_time': None,
                'wake_time': None,
                'total_sleep_hours': 0
            }
        
        # 初始化结果
        stages_duration = {
            'awake': 0,      # 清醒时长（分钟）
            'rem': 0,        # REM睡眠时长（分钟）
            'core': 0,       # 核心睡眠时长（分钟）
            'deep': 0,       # 深度睡眠时长（分钟）
            'in_bed': 0,     # 在床时长（分钟）
            'unspecified': 0 # 未指定睡眠时长（分钟）
        }
        
        # 记录入睡和起床时间
        sleep_time = None  # 入睡时间
        wake_time = None   # 起床时间
        first_asleep = None  # 第一次进入睡眠的时间
        last_awake = None    # 最后一次醒来的时间
        
        # 分析每个睡眠片段
        for record in sleep_data:
            start = datetime.fromisoformat(record['start_date'].replace('+08:00', '+08:00'))
            end = datetime.fromisoformat(record['end_date'].replace('+08:00', '+08:00'))
            stage_value = record['value']
            
            # 计算持续时间（分钟）
            duration_minutes = (end - start).total_seconds() / 60
            
            # 映射睡眠阶段
            stage = self.SLEEP_STAGE_MAPPING.get(stage_value, 'unspecified')
            stages_duration[stage] += duration_minutes
            
            # 记录入睡时间（第一次非清醒状态）
            if stage != 'awake' and stage != 'in_bed' and first_asleep is None:
                first_asleep = start
            
            # 记录最后的清醒时间
            if stage == 'awake':
                last_awake = end
        
        # 确定实际的入睡和起床时间
        if sleep_data:
            # 入睡时间：第一个睡眠片段的开始时间
            sleep_time = datetime.fromisoformat(sleep_data[0]['start_date'].replace('+08:00', '+08:00'))
            # 起床时间：最后一个睡眠片段的结束时间
            wake_time = datetime.fromisoformat(sleep_data[-1]['end_date'].replace('+08:00', '+08:00'))
        
        # 计算总睡眠时长（不包括清醒时间）
        total_sleep_minutes = (stages_duration['rem'] + stages_duration['core'] + 
                              stages_duration['deep'] + stages_duration['unspecified'])
        total_sleep_hours = total_sleep_minutes / 60
        
        # 将分钟转换为小时
        stages_duration_hours = {
            stage: minutes / 60 for stage, minutes in stages_duration.items()
        }
        
        return {
            'date': date.date().isoformat(),
            'has_data': True,
            'stages_duration_minutes': stages_duration,
            'stages_duration_hours': stages_duration_hours,
            'sleep_time': sleep_time.isoformat() if sleep_time else None,
            'wake_time': wake_time.isoformat() if wake_time else None,
            'total_sleep_hours': total_sleep_hours,
            'deep_sleep_hours': stages_duration_hours['deep'],
            'rem_sleep_hours': stages_duration_hours['rem'],
            'core_sleep_hours': stages_duration_hours['core'],
            'awake_minutes': stages_duration['awake'],
            'source': used_source
        }
    
    def get_sleep_time_details(self, user_id: str, date: datetime,
                              source_filter: Optional[str] = None) -> Dict:
        """
        获取详细的入睡和起床时间信息
        
        Args:
            user_id: 用户ID
            date: 日期
            source_filter: 数据源过滤器
        
        Returns:
            包含入睡时间、起床时间和评分的详情
        """
        analysis = self.analyze_sleep_stages(user_id, date, source_filter)
        
        if not analysis['has_data']:
            return {
                'has_data': False,
                'message': '没有睡眠数据'
            }
        
        sleep_time = datetime.fromisoformat(analysis['sleep_time']) if analysis['sleep_time'] else None
        wake_time = datetime.fromisoformat(analysis['wake_time']) if analysis['wake_time'] else None
        
        result = {
            'has_data': True,
            'sleep_time': sleep_time,
            'wake_time': wake_time,
            'sleep_hour': sleep_time.hour if sleep_time else None,
            'sleep_minute': sleep_time.minute if sleep_time else None,
            'wake_hour': wake_time.hour if wake_time else None,
            'wake_minute': wake_time.minute if wake_time else None,
            'meets_sleep_target': False,  # 是否满足23:30前入睡
            'meets_wake_target': False,   # 是否满足7:30前起床
        }
        
        # 判断是否满足目标时间
        if sleep_time:
            # 23:30前入睡
            target_sleep_time = datetime.combine(sleep_time.date(), time(23, 30))
            # 如果是凌晨入睡，需要调整比较日期
            if sleep_time.hour < 12:  # 凌晨入睡
                target_sleep_time = target_sleep_time - timedelta(days=1)
            result['meets_sleep_target'] = sleep_time <= target_sleep_time
            
        if wake_time:
            # 7:30前起床
            target_wake_time = datetime.combine(wake_time.date(), time(7, 30))
            result['meets_wake_target'] = wake_time <= target_wake_time
        
        return result
    
    def get_monthly_sleep_analysis(self, user_id: str, year: int, month: int,
                                  source_filter: Optional[str] = None) -> List[Dict]:
        """
        获取整月的睡眠分析
        
        Args:
            user_id: 用户ID
            year: 年份
            month: 月份
            source_filter: 数据源过滤器
        
        Returns:
            每日睡眠分析列表
        """
        results = []
        
        # 计算月份的天数
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        
        current_date = datetime(year, month, 1)
        
        while current_date < next_month:
            analysis = self.analyze_sleep_stages(user_id, current_date, source_filter)
            if analysis['has_data']:
                results.append(analysis)
            current_date += timedelta(days=1)
        
        return results