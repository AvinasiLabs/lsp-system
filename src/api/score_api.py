"""
积分查询API接口
提供积分历史、有效积分、过期积分等查询功能
"""

from datetime import datetime, date, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from pydantic import BaseModel
from ..services.score_persistence_service import ScorePersistenceService
from ..utils.logger import logger
from ..db.configs.global_config import API_CONFIG
from .auth_middleware import get_user_id


router = APIRouter(prefix="/lsp/api/v1/scores", tags=["scores"])

# 初始化服务
persistence_service = ScorePersistenceService()


class ScoreHistoryQuery(BaseModel):
    """积分历史查询参数"""

    start_date: date
    end_date: date
    include_expired: bool = False


class ValidScoreResponse(BaseModel):
    """有效积分响应"""

    user_id: str
    total_valid_score: int
    dimension_scores: dict
    as_of_date: str
    record_count: int


class ScoreHistoryItem(BaseModel):
    """积分历史项"""

    id: int
    date: str
    dimension: str
    sub_category: Optional[str]
    difficulty: str
    score: int
    expire_date: Optional[str]
    is_expired: bool
    tier_level: str
    details: dict
    created_at: str


class ExpiringScoreResponse(BaseModel):
    """即将过期积分响应"""

    user_id: str
    days_ahead: int
    total_expiring_score: int
    expiring_by_date: List[dict]


class TierStatsResponse(BaseModel):
    """用户等级统计响应"""

    user_id: str
    current_tier: str
    total_earned_score: int
    total_valid_score: int
    expiration_months: Optional[int]


class ExpirationCheckResponse(BaseModel):
    """过期检查响应"""

    checked_count: int
    expired_count: int
    message: str


@router.get("/valid", response_model=ValidScoreResponse)
async def get_valid_scores(
    as_of_date: Optional[date] = Query(default=None, description="计算日期，默认为今天"),
    user_id: str = Depends(get_user_id),
):
    """
    获取用户当前有效积分总额

    有效积分指：
    - 未过期的积分（expire_date > 当前日期）
    - 未被标记为过期的积分（is_expired = false）
    """
    try:
        as_of = datetime.combine(as_of_date, datetime.min.time()) if as_of_date else datetime.now()
        result = persistence_service.get_user_valid_scores(user_id, as_of)

        if "error" in result:
            raise HTTPException(status_code=200, detail=result["error"])

        return ValidScoreResponse(**result)
    except Exception as e:
        logger.error(f"获取有效积分失败: {e}")
        raise HTTPException(status_code=200, detail="获取有效积分失败")


@router.get("/history", response_model=List[ScoreHistoryItem])
async def get_score_history(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    include_expired: bool = Query(default=False, description="是否包含过期积分"),
    user_id: str = Depends(get_user_id),
):
    """
    获取用户积分历史记录

    可以查询指定日期范围内的所有积分记录，包括：
    - 每日积分明细
    - 各维度积分
    - 过期状态
    """
    try:
        # 验证日期范围
        if end_date < start_date:
            raise HTTPException(status_code=400, detail="结束日期不能早于开始日期")

        if (end_date - start_date).days > 365:
            raise HTTPException(status_code=400, detail="查询范围不能超过365天")

        start = datetime.combine(start_date, datetime.min.time())
        end = datetime.combine(end_date, datetime.max.time())

        history = persistence_service.get_user_score_history(user_id, start, end, include_expired)

        return [ScoreHistoryItem(**item) for item in history]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取积分历史失败: {e}")
        raise HTTPException(status_code=200, detail="获取积分历史失败")


@router.get("/expiring", response_model=ExpiringScoreResponse)
async def get_expiring_scores(
    days_ahead: int = Query(default=30, ge=1, le=180, description="查询未来多少天内将过期的积分"),
    user_id: str = Depends(get_user_id),
):
    """
    获取即将过期的积分

    查询未来N天内将要过期的积分，帮助用户及时使用积分
    """
    try:
        result = persistence_service.get_expiring_scores(user_id, days_ahead)

        if "error" in result:
            raise HTTPException(status_code=200, detail=result["error"])

        return ExpiringScoreResponse(**result)
    except Exception as e:
        logger.error(f"获取即将过期积分失败: {e}")
        raise HTTPException(status_code=200, detail="获取即将过期积分失败")


@router.get("/tier-stats", response_model=TierStatsResponse)
async def get_tier_statistics(user_id: str = Depends(get_user_id)):
    """
    获取用户等级相关统计

    包括：
    - 当前等级
    - 累计获得的总积分
    - 当前有效积分
    - 积分过期时间规则
    """
    try:
        result = persistence_service.get_user_tier_stats(user_id)

        if "error" in result:
            raise HTTPException(status_code=200, detail=result["error"])

        return TierStatsResponse(**result)
    except Exception as e:
        logger.error(f"获取等级统计失败: {e}")
        raise HTTPException(status_code=200, detail="获取等级统计失败")


@router.post("/check-expiration", response_model=ExpirationCheckResponse)
async def check_and_mark_expired():
    """
    检查并标记过期的积分

    这个端点应该定期调用（比如每天一次），用于：
    - 检查所有用户的积分过期状态
    - 将过期的积分标记为is_expired=true

    注意：需要管理员权限（当认证系统完善后）
    """
    try:
        checked, expired = persistence_service.mark_expired_scores()

        return ExpirationCheckResponse(
            checked_count=checked, expired_count=expired, message=f"检查了{checked}条记录，标记了{expired}条为过期"
        )
    except Exception as e:
        logger.error(f"检查过期积分失败: {e}")
        raise HTTPException(status_code=200, detail="检查过期积分失败")


@router.get("/summary/{year}/{month}")
async def get_monthly_summary(
    year: int = Path(..., ge=2020, le=2030), month: int = Path(..., ge=1, le=12), user_id: str = Depends(get_user_id)
):
    """
    获取月度积分汇总

    按维度统计指定月份的积分情况
    """
    try:
        # 计算月份的开始和结束日期
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)

        # 获取历史记录
        history = persistence_service.get_user_score_history(user_id, start_date, end_date, include_expired=False)

        # 按维度汇总
        dimension_summary = {}
        total_score = 0
        days_with_scores = set()

        for record in history:
            dimension = record["dimension"]
            if dimension == "total":
                continue

            if dimension not in dimension_summary:
                dimension_summary[dimension] = {
                    "total": 0,
                    "by_difficulty": {"easy": 0, "medium": 0, "hard": 0, "super_hard": 0},
                }

            score = record["score"]
            difficulty = record["difficulty"]

            dimension_summary[dimension]["total"] += score
            dimension_summary[dimension]["by_difficulty"][difficulty] += score
            total_score += score
            days_with_scores.add(record["date"])

        return {
            "user_id": user_id,
            "year": year,
            "month": month,
            "total_score": total_score,
            "active_days": len(days_with_scores),
            "dimension_summary": dimension_summary,
        }

    except Exception as e:
        logger.error(f"获取月度汇总失败: {e}")
        raise HTTPException(status_code=200, detail="获取月度汇总失败")
