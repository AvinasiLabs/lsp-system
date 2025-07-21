"""
健康数据API接口
提供健康数据查询和积分计算的HTTP接口
"""
from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from ..services.health_data_service import HealthDataService
from ..core.score_engine import ScoreEngine
from ..models.health_data import HealthDataQuery, DailyHealthSummary
from ..utils.logger import logger
from ..db.configs.global_config import API_CONFIG
from .auth_middleware import get_current_user, security, get_user_id


router = APIRouter(prefix="/api/v1", tags=["health-data"])

# 初始化服务
health_service = HealthDataService()
score_engine = ScoreEngine()


# get_user_id函数已移至auth_middleware.py


class ScoreResponse(BaseModel):
    """积分响应模型"""
    user_id: str
    date: str
    health_summary: dict
    dimension_scores: dict
    total_score: int
    user_level: str
    timestamp: str


class HealthSummaryResponse(BaseModel):
    """健康数据汇总响应"""
    date: str
    sleep_hours: Optional[float]
    steps: Optional[int]
    active_energy: Optional[float]
    exercise_minutes: Optional[int]
    stand_hours: Optional[int]
    avg_heart_rate: Optional[float]
    resting_heart_rate: Optional[float]
    hrv: Optional[float]
    water_ml: Optional[float]


@router.get("/health/daily-summary", response_model=HealthSummaryResponse)
async def get_daily_health_summary(
    date: date = Query(default=None, description="查询日期，默认为今天"),
    user_id: str = Depends(get_user_id)
):
    """
    获取指定日期的健康数据汇总
    """
    try:
        query_date = datetime.combine(date or datetime.now().date(), datetime.min.time())
        summary = health_service.get_daily_summary(user_id, query_date)
        
        return HealthSummaryResponse(
            date=query_date.strftime('%Y-%m-%d'),
            sleep_hours=summary.sleep_hours,
            steps=summary.steps,
            active_energy=summary.active_energy,
            exercise_minutes=summary.exercise_minutes,
            stand_hours=summary.stand_hours,
            avg_heart_rate=summary.avg_heart_rate,
            resting_heart_rate=summary.resting_heart_rate,
            hrv=summary.hrv,
            water_ml=summary.water_ml
        )
    except Exception as e:
        logger.error(f"获取健康数据汇总失败: {e}")
        raise HTTPException(status_code=500, detail="获取健康数据失败")


@router.get("/score/daily", response_model=ScoreResponse)
async def calculate_daily_score(
    date: date = Query(default=None, description="计算日期，默认为今天"),
    user_id: str = Depends(get_user_id)
):
    """
    计算指定日期的积分
    """
    try:
        query_date = datetime.combine(date or datetime.now().date(), datetime.min.time())
        score_result = score_engine.calculate_daily_score(user_id, query_date)
        
        return ScoreResponse(**score_result)
    except Exception as e:
        import traceback
        logger.error(f"计算积分失败: {e}")
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(f"堆栈跟踪: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"计算积分失败: {str(e)}")


@router.get("/score/range", response_model=List[ScoreResponse])
async def calculate_score_range(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    user_id: str = Depends(get_user_id)
):
    """
    计算日期范围内的积分
    """
    try:
        # 验证日期范围
        if end_date < start_date:
            raise HTTPException(status_code=400, detail="结束日期不能早于开始日期")
        
        if (end_date - start_date).days > 90:
            raise HTTPException(status_code=400, detail="查询范围不能超过90天")
        
        start = datetime.combine(start_date, datetime.min.time())
        end = datetime.combine(end_date, datetime.min.time())
        
        scores = score_engine.calculate_date_range_scores(user_id, start, end)
        
        return [ScoreResponse(**score) for score in scores]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算积分范围失败: {e}")
        raise HTTPException(status_code=500, detail="计算积分失败")


@router.get("/score/available-dimensions")
async def get_available_dimensions(
    user_id: str = Depends(get_user_id)
):
    """
    获取可用的积分维度
    """
    try:
        available = score_engine.get_available_dimensions(user_id)
        return {
            "dimensions": available,
            "message": "基于当前HealthKit数据的可用维度"
        }
    except Exception as e:
        logger.error(f"获取可用维度失败: {e}")
        raise HTTPException(status_code=500, detail="获取可用维度失败")