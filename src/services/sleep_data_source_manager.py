"""
睡眠数据源管理器
负责选择最佳的睡眠数据源并提供统一的数据访问接口
"""
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
from ..db.postgresql import POSTGRES_POOL
from ..utils.logger import logger


class SleepDataSourceManager:
    """睡眠数据源管理器"""
    
    # 数据源优先级（越小优先级越高）
    SOURCE_PRIORITY = {
        'Apple Watch': 1,  # 最高优先级（如果有数据）
        'Oura': 2,         # 次优先（完整睡眠阶段）
        'WHOOP': 3,        # 第三优先
        'OffScreen': 4,    # 最低优先级
    }
    
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
        """初始化数据源管理器"""
        self.available_sources = {}
        self._scan_available_sources()
    
    def _scan_available_sources(self):
        """扫描数据库中可用的睡眠数据源"""
        try:
            query = """
                SELECT DISTINCT source_name, COUNT(*) as record_count
                FROM health_metric
                WHERE type = 'HKCategoryTypeIdentifierSleepAnalysis'
                GROUP BY source_name
            """
            result = POSTGRES_POOL._execute_query(query)
            
            if result:
                for row in result:
                    source_name = row[0]
                    count = row[1]
                    self.available_sources[source_name] = count
                    logger.info(f"发现睡眠数据源: {source_name} ({count}条记录)")
            
            # 特别检查是否有包含"Apple Watch"的数据源
            query_apple = """
                SELECT DISTINCT source_name, COUNT(*) as record_count
                FROM health_metric
                WHERE type = 'HKCategoryTypeIdentifierSleepAnalysis'
                AND source_name LIKE '%Apple Watch%'
                GROUP BY source_name
            """
            result_apple = POSTGRES_POOL._execute_query(query_apple)
            
            if result_apple:
                for row in result_apple:
                    logger.info(f"发现Apple Watch睡眠数据: {row[0]} ({row[1]}条记录)")
            else:
                logger.info("未发现Apple Watch的睡眠分析数据")
                
        except Exception as e:
            logger.error(f"扫描数据源失败: {e}")
    
    def get_best_source_for_user(self, user_id: str, date: datetime) -> Optional[str]:
        """
        为特定用户和日期选择最佳数据源
        
        Args:
            user_id: 用户ID
            date: 日期
            
        Returns:
            最佳数据源名称，如果没有数据则返回None
        """
        # 计算查询的时间范围
        start_time = datetime.combine(date - timedelta(days=1), time(18, 0))
        end_time = datetime.combine(date, time(12, 0))
        
        # 查询该用户该日期有哪些数据源
        query = """
            SELECT DISTINCT source_name, COUNT(*) as count
            FROM health_metric
            WHERE type = 'HKCategoryTypeIdentifierSleepAnalysis'
            AND user_id = %s
            AND start_date >= %s
            AND end_date <= %s
            GROUP BY source_name
        """
        
        try:
            result = POSTGRES_POOL._execute_query(
                query, 
                (user_id, start_time, end_time)
            )
            
            if not result:
                logger.info(f"用户{user_id}在{date.date()}没有睡眠数据")
                return None
            
            # 根据优先级选择最佳数据源
            available = {}
            for row in result:
                source_name = row[0]
                count = row[1]
                available[source_name] = count
            
            # 按优先级选择
            best_source = None
            best_priority = float('inf')
            
            for source_name in available.keys():
                # 检查是否包含优先级关键词
                priority = float('inf')
                for key, pri in self.SOURCE_PRIORITY.items():
                    if key.lower() in source_name.lower():
                        priority = min(priority, pri)
                
                # 如果没有匹配的关键词，使用默认优先级
                if priority == float('inf'):
                    # 尝试直接匹配
                    priority = self.SOURCE_PRIORITY.get(source_name, 999)
                
                if priority < best_priority:
                    best_priority = priority
                    best_source = source_name
            
            logger.info(f"为用户{user_id}在{date.date()}选择数据源: {best_source}")
            return best_source
            
        except Exception as e:
            logger.error(f"选择数据源失败: {e}")
            return None
    
    def get_sleep_data_with_auto_source(self, user_id: str, date: datetime) -> Tuple[List[Dict], str]:
        """
        自动选择最佳数据源并获取睡眠数据
        
        Args:
            user_id: 用户ID
            date: 日期
            
        Returns:
            (睡眠数据列表, 使用的数据源名称)
        """
        # 自动选择最佳数据源
        best_source = self.get_best_source_for_user(user_id, date)
        
        if not best_source:
            return [], "none"
        
        # 获取该数据源的数据
        return self.get_sleep_data(user_id, date, best_source), best_source
    
    def get_sleep_data(self, user_id: str, date: datetime, source_name: str) -> List[Dict]:
        """
        获取指定数据源的睡眠数据
        
        Args:
            user_id: 用户ID
            date: 日期
            source_name: 数据源名称
            
        Returns:
            睡眠数据列表
        """
        try:
            # 计算睡眠时间范围
            start_time = datetime.combine(date - timedelta(days=1), time(18, 0))
            end_time = datetime.combine(date, time(12, 0))
            
            # 查询数据
            conditions = """
                type = %s 
                AND user_id = %s 
                AND source_name = %s
                AND start_date >= %s 
                AND end_date <= %s
                ORDER BY start_date
            """
            
            data = POSTGRES_POOL.select_data(
                table_name="health_metric",
                conditions=conditions,
                params=('HKCategoryTypeIdentifierSleepAnalysis', 
                       user_id, source_name, start_time, end_time)
            )
            
            return data if data else []
            
        except Exception as e:
            logger.error(f"获取睡眠数据失败: {e}")
            return []
    
    def evaluate_source_quality(self, source_name: str, data: List[Dict]) -> Dict:
        """
        评估数据源质量
        
        Args:
            source_name: 数据源名称
            data: 该数据源的数据
            
        Returns:
            质量评估结果
        """
        if not data:
            return {
                'source': source_name,
                'has_data': False,
                'quality_score': 0
            }
        
        # 统计睡眠阶段类型
        stage_types = set()
        for record in data:
            stage = self.SLEEP_STAGE_MAPPING.get(record.get('value', ''), 'unknown')
            stage_types.add(stage)
        
        # 评分标准
        quality_score = 0
        features = {
            'has_sleep_duration': False,
            'has_deep_sleep': False,
            'has_rem_sleep': False,
            'has_core_sleep': False,
            'has_awake_detection': False,
            'has_sleep_time': False,
            'has_wake_time': False
        }
        
        # 检查功能
        if 'unspecified' in stage_types or len(stage_types) > 0:
            features['has_sleep_duration'] = True
            quality_score += 20
        
        if 'deep' in stage_types:
            features['has_deep_sleep'] = True
            quality_score += 20
        
        if 'rem' in stage_types:
            features['has_rem_sleep'] = True
            quality_score += 20
        
        if 'core' in stage_types:
            features['has_core_sleep'] = True
            quality_score += 10
        
        if 'awake' in stage_types:
            features['has_awake_detection'] = True
            quality_score += 10
        
        if len(data) > 0:
            features['has_sleep_time'] = True
            features['has_wake_time'] = True
            quality_score += 20
        
        return {
            'source': source_name,
            'has_data': True,
            'quality_score': quality_score,
            'stage_types': list(stage_types),
            'features': features,
            'can_calculate_medium': features['has_deep_sleep'] and features['has_rem_sleep'],
            'can_calculate_hard': features['has_sleep_time'] and features['has_wake_time']
        }
    
    def get_available_sources_summary(self) -> Dict:
        """
        获取所有可用数据源的摘要
        
        Returns:
            数据源摘要信息
        """
        return {
            'sources': self.available_sources,
            'total_sources': len(self.available_sources),
            'has_apple_watch': any('apple watch' in s.lower() for s in self.available_sources.keys()),
            'has_oura': 'Oura' in self.available_sources,
            'has_whoop': 'WHOOP' in self.available_sources
        }