"""
健康数据服务层
负责从数据库提取和处理健康数据
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from ..models.health_data import (
    HealthDataRecord, 
    DailyHealthSummary, 
    HealthDataQuery,
    HealthDataType
)
from ..db.postgresql import POSTGRES_POOL
from ..utils.logger import logger


class HealthDataService:
    """健康数据服务类"""
    
    def __init__(self):
        self.db_pool = POSTGRES_POOL
    
    def get_health_data(self, query: HealthDataQuery) -> List[HealthDataRecord]:
        """
        获取健康数据记录
        
        Args:
            query: 查询参数
            
        Returns:
            健康数据记录列表
        """
        conditions = ["user_id = %s", "start_date >= %s", "end_date <= %s"]
        params = [query.user_id, query.start_date, query.end_date]
        
        # 如果指定了数据类型
        if query.data_types:
            type_list = [dt.value for dt in query.data_types]
            placeholders = ','.join(['%s'] * len(type_list))
            conditions.append(f"type IN ({placeholders})")
            params.extend(type_list)
        
        where_clause = " AND ".join(conditions)
        
        results = self.db_pool.select_data(
            table_name="apple_healthkit",
            conditions=where_clause,
            params=params
        )
        
        if not results:
            return []
        
        # 转换为模型对象
        records = []
        for row in results:
            record = HealthDataRecord(
                id=row[0],
                user_id=row[11],  # user_id在最后
                type=row[1],
                source_name=row[2],
                source_version=row[3],
                unit=row[4],
                creation_date=row[5],
                start_date=row[6],
                end_date=row[7],
                value=row[8],
                device=row[9],
                created_at=row[10]
            )
            records.append(record)
        
        return records
    
    def get_daily_summary(self, user_id: str, date: datetime) -> DailyHealthSummary:
        """
        获取指定日期的健康数据汇总
        
        Args:
            user_id: 用户ID
            date: 日期
            
        Returns:
            每日健康数据汇总
        """
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        summary = DailyHealthSummary(date=date)
        
        # 获取睡眠数据
        sleep_data = self._get_sleep_data(user_id, start_date, end_date)
        if sleep_data:
            summary.sleep_hours = sleep_data.get('total_hours', 0)
            # TODO: 深度睡眠和REM睡眠需要更详细的数据
        
        # 获取步数
        steps = self._get_aggregated_value(
            user_id,
            HealthDataType.STEP_COUNT,
            start_date,
            end_date,
            'sum'
        )
        summary.steps = int(steps) if steps else None
        
        # 获取活动能量
        active_energy = self._get_aggregated_value(
            user_id,
            HealthDataType.ACTIVE_ENERGY_BURNED,
            start_date,
            end_date,
            'sum'
        )
        summary.active_energy = active_energy
        
        # 获取运动时间
        exercise_time = self._get_aggregated_value(
            user_id,
            HealthDataType.EXERCISE_TIME,
            start_date,
            end_date,
            'sum'
        )
        summary.exercise_minutes = int(exercise_time) if exercise_time else None
        
        # 获取站立小时数
        stand_hours = self._get_stand_hours(user_id, start_date, end_date)
        summary.stand_hours = stand_hours
        
        # 获取心率数据
        avg_hr = self._get_aggregated_value(
            user_id,
            HealthDataType.HEART_RATE,
            start_date,
            end_date,
            'avg'
        )
        summary.avg_heart_rate = avg_hr
        
        resting_hr = self._get_aggregated_value(
            user_id,
            HealthDataType.RESTING_HEART_RATE,
            start_date,
            end_date,
            'avg'
        )
        summary.resting_heart_rate = resting_hr
        
        # 获取HRV
        hrv = self._get_aggregated_value(
            user_id,
            HealthDataType.HEART_RATE_VARIABILITY,
            start_date,
            end_date,
            'avg'
        )
        summary.hrv = hrv
        
        # 获取饮水量
        water = self._get_aggregated_value(
            user_id,
            HealthDataType.DIETARY_WATER,
            start_date,
            end_date,
            'sum'
        )
        summary.water_ml = water
        
        return summary
    
    def get_date_range_summary(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, DailyHealthSummary]:
        """
        获取日期范围内的每日汇总
        
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            日期到汇总的字典
        """
        summaries = {}
        current_date = start_date
        
        while current_date <= end_date:
            summary = self.get_daily_summary(user_id, current_date)
            summaries[current_date.strftime('%Y-%m-%d')] = summary
            current_date += timedelta(days=1)
        
        return summaries
    
    def _get_sleep_data(self, user_id: str, start_date: datetime, end_date: datetime) -> Optional[Dict]:
        """获取睡眠数据"""
        # 注意：睡眠数据可能跨越日期边界
        # 我们需要获取在指定日期内结束的睡眠记录
        query = f"""
        SELECT 
            MIN(start_date) as sleep_start,
            MAX(end_date) as sleep_end,
            SUM(EXTRACT(EPOCH FROM (end_date - start_date)) / 3600) as total_hours
        FROM apple_healthkit
        WHERE type = %s
        AND user_id = %s
        AND end_date > %s
        AND start_date < %s
        """
        
        result = self.db_pool._execute_query(
            query,
            (HealthDataType.SLEEP_ANALYSIS.value, user_id, start_date, end_date),
            fetch_one=True
        )
        
        if result and result[2]:
            return {
                'sleep_start': result[0],
                'sleep_end': result[1],
                'total_hours': float(result[2])
            }
        return None
    
    def _get_aggregated_value(
        self,
        user_id: str,
        data_type: HealthDataType, 
        start_date: datetime, 
        end_date: datetime,
        aggregation: str = 'sum'
    ) -> Optional[float]:
        """获取聚合值"""
        query = f"""
        SELECT {aggregation}(CAST(value AS FLOAT))
        FROM apple_healthkit
        WHERE type = %s
        AND user_id = %s
        AND start_date >= %s
        AND end_date <= %s
        AND value IS NOT NULL
        AND value != ''
        """
        
        try:
            result = self.db_pool._execute_query(
                query,
                (data_type.value, user_id, start_date, end_date),
                fetch_one=True
            )
            
            if result and result[0] is not None:
                return float(result[0])
        except Exception as e:
            logger.error(f"获取聚合数据失败 {data_type.value}: {e}")
        
        return None
    
    def _get_stand_hours(self, user_id: str, start_date: datetime, end_date: datetime) -> Optional[int]:
        """获取站立小时数"""
        query = """
        SELECT COUNT(DISTINCT DATE_TRUNC('hour', start_date))
        FROM apple_healthkit
        WHERE type = %s
        AND user_id = %s
        AND start_date >= %s
        AND end_date <= %s
        """
        
        result = self.db_pool._execute_query(
            query,
            (HealthDataType.STAND_HOUR.value, user_id, start_date, end_date),
            fetch_one=True
        )
        
        if result and result[0]:
            return int(result[0])
        
        # 如果没有STAND_HOUR数据，尝试从STAND_TIME计算
        query = """
        SELECT COUNT(DISTINCT DATE_TRUNC('hour', start_date))
        FROM apple_healthkit
        WHERE type = %s
        AND user_id = %s
        AND start_date >= %s
        AND end_date <= %s
        AND CAST(value AS FLOAT) > 0
        """
        
        result = self.db_pool._execute_query(
            query,
            (HealthDataType.STAND_TIME.value, user_id, start_date, end_date),
            fetch_one=True
        )
        
        if result and result[0]:
            return int(result[0])
        
        return None