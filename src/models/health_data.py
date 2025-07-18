"""
健康数据模型定义
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class HealthDataType(str, Enum):
    """健康数据类型枚举"""
    # 睡眠相关
    SLEEP_ANALYSIS = "HKCategoryTypeIdentifierSleepAnalysis"
    
    # 运动相关
    STEP_COUNT = "HKQuantityTypeIdentifierStepCount"
    ACTIVE_ENERGY_BURNED = "HKQuantityTypeIdentifierActiveEnergyBurned"
    BASAL_ENERGY_BURNED = "HKQuantityTypeIdentifierBasalEnergyBurned"
    EXERCISE_TIME = "HKQuantityTypeIdentifierAppleExerciseTime"
    STAND_TIME = "HKQuantityTypeIdentifierAppleStandTime"
    STAND_HOUR = "HKCategoryTypeIdentifierAppleStandHour"
    DISTANCE_WALKING_RUNNING = "HKQuantityTypeIdentifierDistanceWalkingRunning"
    
    # 生理指标
    HEART_RATE = "HKQuantityTypeIdentifierHeartRate"
    RESTING_HEART_RATE = "HKQuantityTypeIdentifierRestingHeartRate"
    HEART_RATE_VARIABILITY = "HKQuantityTypeIdentifierHeartRateVariabilitySDNN"
    RESPIRATORY_RATE = "HKQuantityTypeIdentifierRespiratoryRate"
    BODY_TEMPERATURE = "HKQuantityTypeIdentifierBodyTemperature"
    OXYGEN_SATURATION = "HKQuantityTypeIdentifierOxygenSaturation"
    
    # 饮食相关
    DIETARY_WATER = "HKQuantityTypeIdentifierDietaryWater"
    
    # 环境相关
    ENVIRONMENTAL_AUDIO_EXPOSURE = "HKQuantityTypeIdentifierEnvironmentalAudioExposure"
    UV_EXPOSURE = "HKQuantityTypeIdentifierUVExposure"
    
    # 其他
    PHYSICAL_EFFORT = "HKQuantityTypeIdentifierPhysicalEffort"
    MINDFUL_SESSION = "HKCategoryTypeIdentifierMindfulSession"


class HealthDataRecord(BaseModel):
    """健康数据记录模型"""
    id: int
    type: str
    source_name: Optional[str] = None
    source_version: Optional[str] = None
    unit: Optional[str] = None
    creation_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    value: Optional[str] = None
    device: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DailyHealthSummary(BaseModel):
    """每日健康数据汇总"""
    date: datetime
    sleep_hours: Optional[float] = None
    deep_sleep_hours: Optional[float] = None
    rem_sleep_hours: Optional[float] = None
    steps: Optional[int] = None
    active_energy: Optional[float] = None
    exercise_minutes: Optional[int] = None
    stand_hours: Optional[int] = None
    avg_heart_rate: Optional[float] = None
    resting_heart_rate: Optional[float] = None
    hrv: Optional[float] = None
    water_ml: Optional[float] = None
    
    
class HealthDataQuery(BaseModel):
    """健康数据查询参数"""
    user_id: Optional[str] = None  # 预留用户ID
    start_date: datetime
    end_date: datetime
    data_types: Optional[List[HealthDataType]] = None
    
    
class ScoreDimension(str, Enum):
    """积分维度枚举"""
    SLEEP = "sleep"
    EXERCISE = "exercise"
    DIET = "diet"
    ENVIRONMENT = "environment"
    MENTAL = "mental"
    SOCIAL = "social"
    COGNITION = "cognition"
    PREVENTION = "prevention"