"""
用户相关数据模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from enum import Enum


class UserLevel(str, Enum):
    """用户等级枚举"""
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"
    DIAMOND = "DIAMOND"
    AMBASSADOR = "AMBASSADOR"


class User(BaseModel):
    """用户模型"""
    user_id: str
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    level: UserLevel = UserLevel.BRONZE
    total_points: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserScoreRecord(BaseModel):
    """用户积分记录"""
    id: Optional[int] = None
    user_id: str
    score_date: datetime
    dimension: str
    difficulty: str
    score: int
    details: Optional[dict] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CreateUserRequest(BaseModel):
    """创建用户请求"""
    user_id: str
    username: Optional[str] = None
    email: Optional[EmailStr] = None


class UserScoreSummary(BaseModel):
    """用户积分汇总"""
    user_id: str
    date: str
    dimension_scores: dict
    total_score: int
    user_level: UserLevel
    timestamp: datetime