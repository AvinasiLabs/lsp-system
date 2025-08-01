"""
积分持久化服务
负责保存、查询和管理用户积分
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from ..db.postgresql import POSTGRES_POOL
from ..models.health_data import DifficultyLevel
from ..utils.logger import logger
import json


class ScorePersistenceService:
    """积分持久化服务"""
    
    # Tier等级的过期时间配置（月）
    TIER_EXPIRATION_MONTHS = {
        "Bronze": 6,       # 6个月
        "Silver": 8,       # 8个月  
        "Gold": 12,        # 12个月
        "Platinum": None,  # 永不过期
        "Diamond": None,   # 永不过期
        "Ambassador": None # 永不过期
    }
    
    # user_scores表的字段顺序（用于元组到字典的转换）
    USER_SCORES_COLUMNS = [
        'id', 'user_id', 'score_date', 'dimension', 'difficulty', 
        'score', 'details', 'created_at', 'expire_date', 'is_expired',
        'tier_level', 'sub_category'
    ]
    
    @staticmethod
    def _get_field_value(record, field_name, field_index=None):
        """
        安全地从记录中获取字段值，支持字典和元组格式
        
        Args:
            record: 数据记录（字典或元组）
            field_name: 字段名（用于字典访问）
            field_index: 字段索引（用于元组访问）
            
        Returns:
            字段值
        """
        if isinstance(record, dict):
            return record.get(field_name)
        elif isinstance(record, (tuple, list)) and field_index is not None:
            return record[field_index] if len(record) > field_index else None
        return None
    
    def __init__(self):
        """初始化服务"""
        pass
    
    def calculate_expire_date(self, score_date: datetime, tier_level: str = "Bronze") -> Optional[datetime]:
        """
        根据tier等级计算过期时间
        
        Args:
            score_date: 积分获得日期
            tier_level: 用户等级
            
        Returns:
            过期时间，如果永不过期则返回None
        """
        months = self.TIER_EXPIRATION_MONTHS.get(tier_level, 6)
        if months is None:
            return None  # 永不过期
        
        # 使用30天作为一个月的近似值
        return score_date + timedelta(days=months * 30)
    
    def save_daily_scores(self, user_id: str, date: datetime, 
                         dimension_scores: Dict[str, Dict], 
                         total_score: int, tier_level: str = "Bronze") -> bool:
        """
        保存每日积分汇总和明细
        
        Args:
            user_id: 用户ID
            date: 积分日期
            dimension_scores: 各维度积分详情
            total_score: 总积分
            tier_level: 用户等级
            
        Returns:
            是否保存成功
        """
        try:
            # 开始事务
            conn = POSTGRES_POOL.get_connection()
            cursor = conn.cursor()
            
            # 计算过期时间
            expire_date = self.calculate_expire_date(date, tier_level)
            
            # 保存总积分记录
            cursor.execute("""
                INSERT INTO user_scores 
                (user_id, score_date, dimension, sub_category, difficulty, score, 
                 expire_date, tier_level, details, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, score_date, dimension, difficulty) 
                DO UPDATE SET 
                    score = EXCLUDED.score,
                    expire_date = EXCLUDED.expire_date,
                    tier_level = EXCLUDED.tier_level,
                    details = EXCLUDED.details,
                    created_at = EXCLUDED.created_at
            """, (
                user_id, date.date(), 'total', 'daily_total', 'all',
                total_score, expire_date, tier_level,
                json.dumps({"dimension_scores": dimension_scores}),
                datetime.now()
            ))
            
            # 保存各维度积分明细
            for dimension, scores in dimension_scores.items():
                if scores['total'] > 0:
                    # 保存每个难度级别的积分
                    for difficulty in ['easy', 'medium', 'hard', 'super_hard']:
                        if scores.get(difficulty, 0) > 0:
                            self._save_dimension_score(
                                cursor, user_id, date, dimension, 
                                difficulty, scores[difficulty], 
                                expire_date, tier_level, scores.get('details', {})
                            )
            
            # 提交事务
            conn.commit()
            logger.info(f"成功保存用户 {user_id} 在 {date.date()} 的积分")
            return True
            
        except Exception as e:
            logger.error(f"保存积分失败: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                POSTGRES_POOL.put_connection(conn)
    
    def _save_dimension_score(self, cursor, user_id: str, date: datetime,
                             dimension: str, difficulty: str, score: int,
                             expire_date: Optional[datetime], tier_level: str,
                             details: Dict) -> None:
        """保存维度积分明细"""
        # 根据维度确定子类别
        sub_category_map = {
            'sleep': 'duration',
            'exercise': 'activity',
            'diet': 'nutrition',
            'mental': 'wellbeing'
        }
        sub_category = sub_category_map.get(dimension, 'general')
        
        cursor.execute("""
            INSERT INTO user_scores 
            (user_id, score_date, dimension, sub_category, difficulty, score, 
             expire_date, tier_level, details, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, score_date, dimension, difficulty) 
            DO UPDATE SET 
                score = EXCLUDED.score,
                sub_category = EXCLUDED.sub_category,
                expire_date = EXCLUDED.expire_date,
                tier_level = EXCLUDED.tier_level,
                details = EXCLUDED.details,
                created_at = EXCLUDED.created_at
        """, (
            user_id, date.date(), dimension, sub_category, difficulty,
            score, expire_date, tier_level, json.dumps(details), datetime.now()
        ))
    
    def get_user_valid_scores(self, user_id: str, as_of_date: Optional[datetime] = None) -> Dict:
        """
        获取用户当前有效积分
        
        Args:
            user_id: 用户ID
            as_of_date: 计算日期，默认为当前时间
            
        Returns:
            有效积分汇总
        """
        if as_of_date is None:
            as_of_date = datetime.now()
        
        try:
            # 查询未过期的积分
            data = POSTGRES_POOL.select_data(
                table_name="user_scores",
                conditions="""
                    user_id = %s 
                    AND is_expired = FALSE 
                    AND (expire_date IS NULL OR expire_date > %s)
                    AND dimension != 'total'
                """,
                params=(user_id, as_of_date)
            )
            
            # 检查数据是否为空或查询失败
            if data is None:
                # 数据库查询失败
                logger.error("数据库查询返回None，可能是连接池问题")
                return {
                    'user_id': user_id,
                    'total_valid_score': 0,
                    'dimension_scores': {},
                    'as_of_date': as_of_date.isoformat(),
                    'record_count': 0,
                    'error': '数据库连接失败'
                }
            
            if len(data) == 0:
                # 用户没有积分数据，返回0分
                return {
                    'user_id': user_id,
                    'total_valid_score': 0,
                    'dimension_scores': {},
                    'as_of_date': as_of_date.isoformat(),
                    'record_count': 0
                }
            
            # 汇总积分
            total_score = 0
            dimension_scores = {}
            
            for record in data:
                # 处理字典或元组格式的数据
                if isinstance(record, dict):
                    dimension = record['dimension']
                    score = record['score']
                elif isinstance(record, (tuple, list)):
                    # 假设字段顺序：id, user_id, score_date, dimension, difficulty, score, ...
                    # dimension是第4个字段（索引3），score是第6个字段（索引5）
                    dimension = record[3]
                    score = record[5]
                else:
                    logger.warning(f"未知的记录格式: {type(record)}")
                    continue
                
                if dimension not in dimension_scores:
                    dimension_scores[dimension] = 0
                dimension_scores[dimension] += score
                total_score += score
            
            return {
                'user_id': user_id,
                'total_valid_score': total_score,
                'dimension_scores': dimension_scores,
                'as_of_date': as_of_date.isoformat(),
                'record_count': len(data)
            }
            
        except Exception as e:
            logger.error(f"获取有效积分失败: {e}")
            return {
                'user_id': user_id,
                'total_valid_score': 0,
                'dimension_scores': {},
                'error': str(e)
            }
    
    def get_user_score_history(self, user_id: str, start_date: datetime, 
                              end_date: datetime, include_expired: bool = False) -> List[Dict]:
        """
        获取用户积分历史
        
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            include_expired: 是否包含过期积分
            
        Returns:
            积分历史记录列表
        """
        try:
            conditions = "user_id = %s AND score_date >= %s AND score_date <= %s"
            params = [user_id, start_date.date(), end_date.date()]
            
            if not include_expired:
                conditions += " AND is_expired = FALSE"
            
            data = POSTGRES_POOL.select_data(
                table_name="user_scores",
                conditions=conditions + " ORDER BY score_date DESC, created_at DESC",
                params=params
            )
            
            # 检查查询结果
            if data is None:
                logger.error("数据库查询返回None，可能是连接池问题")
                return []
            
            # 转换数据格式
            history = []
            for record in data:
                # 安全地获取字段值
                score_date = self._get_field_value(record, 'score_date', 2)
                expire_date = self._get_field_value(record, 'expire_date', 8)
                created_at = self._get_field_value(record, 'created_at', 7)
                
                history.append({
                    'id': self._get_field_value(record, 'id', 0),
                    'date': score_date.isoformat() if score_date else None,
                    'dimension': self._get_field_value(record, 'dimension', 3),
                    'sub_category': self._get_field_value(record, 'sub_category', 11),
                    'difficulty': self._get_field_value(record, 'difficulty', 4),
                    'score': self._get_field_value(record, 'score', 5),
                    'expire_date': expire_date.isoformat() if expire_date else None,
                    'is_expired': self._get_field_value(record, 'is_expired', 9),
                    'tier_level': self._get_field_value(record, 'tier_level', 10) or 'Bronze',
                    'details': self._get_field_value(record, 'details', 6) or {},
                    'created_at': created_at.isoformat() if created_at else None
                })
            
            return history
            
        except Exception as e:
            logger.error(f"获取积分历史失败: {e}")
            return []
    
    def get_expiring_scores(self, user_id: str, days_ahead: int = 30) -> List[Dict]:
        """
        获取即将过期的积分
        
        Args:
            user_id: 用户ID
            days_ahead: 查询未来多少天内将过期的积分
            
        Returns:
            即将过期的积分列表
        """
        try:
            future_date = datetime.now() + timedelta(days=days_ahead)
            
            data = POSTGRES_POOL.select_data(
                table_name="user_scores",
                conditions="""
                    user_id = %s 
                    AND is_expired = FALSE 
                    AND expire_date IS NOT NULL 
                    AND expire_date <= %s
                    AND expire_date > %s
                    ORDER BY expire_date ASC
                """,
                params=(user_id, future_date, datetime.now())
            )
            
            # 检查查询结果
            if data is None:
                logger.error("数据库查询返回None，可能是连接池问题")
                return {
                    'user_id': user_id,
                    'days_ahead': days_ahead,
                    'total_expiring_score': 0,
                    'expiring_by_date': [],
                    'error': '数据库连接失败'
                }
            
            # 按过期日期分组
            expiring_by_date = {}
            total_expiring = 0
            
            for record in data:
                # 安全地获取字段值
                expire_date_val = self._get_field_value(record, 'expire_date', 8)
                if not expire_date_val:
                    continue
                    
                expire_date = expire_date_val.date()
                if expire_date not in expiring_by_date:
                    expiring_by_date[expire_date] = {
                        'date': expire_date.isoformat(),
                        'scores': [],
                        'total': 0
                    }
                
                dimension = self._get_field_value(record, 'dimension', 3)
                score = self._get_field_value(record, 'score', 5)
                score_date = self._get_field_value(record, 'score_date', 2)
                
                expiring_by_date[expire_date]['scores'].append({
                    'dimension': dimension,
                    'score': score,
                    'earned_date': score_date.isoformat() if score_date else None
                })
                expiring_by_date[expire_date]['total'] += score
                total_expiring += score
            
            return {
                'user_id': user_id,
                'days_ahead': days_ahead,
                'total_expiring_score': total_expiring,
                'expiring_by_date': list(expiring_by_date.values())
            }
            
        except Exception as e:
            logger.error(f"获取即将过期积分失败: {e}")
            return {
                'user_id': user_id,
                'error': str(e)
            }
    
    def mark_expired_scores(self, as_of_date: Optional[datetime] = None) -> Tuple[int, int]:
        """
        标记过期的积分
        
        Args:
            as_of_date: 判断日期，默认为当前时间
            
        Returns:
            (检查的记录数, 标记为过期的记录数)
        """
        if as_of_date is None:
            as_of_date = datetime.now()
        
        try:
            conn = POSTGRES_POOL.get_connection()
            cursor = conn.cursor()
            
            # 查询需要标记为过期的记录数
            cursor.execute("""
                SELECT COUNT(*) FROM user_scores 
                WHERE is_expired = FALSE 
                AND expire_date IS NOT NULL 
                AND expire_date <= %s
            """, (as_of_date,))
            to_expire_count = cursor.fetchone()[0]
            
            # 标记过期记录
            cursor.execute("""
                UPDATE user_scores 
                SET is_expired = TRUE 
                WHERE is_expired = FALSE 
                AND expire_date IS NOT NULL 
                AND expire_date <= %s
            """, (as_of_date,))
            
            expired_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"标记了 {expired_count} 条积分记录为过期")
            return to_expire_count, expired_count
            
        except Exception as e:
            logger.error(f"标记过期积分失败: {e}")
            if conn:
                conn.rollback()
            return 0, 0
        finally:
            if cursor:
                cursor.close()
            if conn:
                POSTGRES_POOL.put_connection(conn)
    
    def get_user_tier_stats(self, user_id: str) -> Dict:
        """
        获取用户等级相关统计
        
        Args:
            user_id: 用户ID
            
        Returns:
            等级统计信息
        """
        try:
            # 获取用户当前等级（从最新记录）
            latest_record = POSTGRES_POOL.select_data(
                table_name="user_scores",
                conditions="user_id = %s ORDER BY created_at DESC LIMIT 1",
                params=(user_id,)
            )
            
            # 检查查询结果
            if latest_record is None:
                logger.error("数据库查询返回None，可能是连接池问题")
                return {
                    'user_id': user_id,
                    'error': '数据库连接失败'
                }
            
            current_tier = latest_record[0]['tier_level'] if latest_record and len(latest_record) > 0 else 'Bronze'
            
            # 获取累计总积分（包括过期的）
            all_scores = POSTGRES_POOL.select_data(
                table_name="user_scores",
                conditions="user_id = %s AND dimension != 'total'",
                params=(user_id,)
            )
            
            # 检查查询结果
            if all_scores is None:
                logger.error("数据库查询返回None，可能是连接池问题")
                return {
                    'user_id': user_id,
                    'error': '数据库连接失败'
                }
            
            # 安全地计算总积分
            total_earned = 0
            if all_scores:
                for record in all_scores:
                    score = self._get_field_value(record, 'score', 5)
                    if score is not None:
                        total_earned += score
            
            # 获取当前有效积分
            valid_scores = self.get_user_valid_scores(user_id)
            
            return {
                'user_id': user_id,
                'current_tier': current_tier,
                'total_earned_score': total_earned,
                'total_valid_score': valid_scores['total_valid_score'],
                'expiration_months': self.TIER_EXPIRATION_MONTHS.get(current_tier, 6)
            }
            
        except Exception as e:
            logger.error(f"获取用户等级统计失败: {e}")
            return {
                'user_id': user_id,
                'error': str(e)
            }