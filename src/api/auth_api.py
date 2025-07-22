"""
认证API接口
提供用户登录和token生成功能
"""
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from ..db.configs.global_config import API_CONFIG
from .auth_middleware import create_access_token
from ..utils.logger import logger


router = APIRouter(prefix="/lsp/api/v1/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    """登录请求模型"""
    user_id: str
    password: str  # 简化版本，实际应该进行密码验证


class TokenResponse(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒数
    user_id: str


class AuthStatusResponse(BaseModel):
    """认证状态响应"""
    auth_enabled: bool
    message: str


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status():
    """
    获取认证系统状态
    """
    if API_CONFIG.auth_enabled:
        message = "认证系统已启用，请使用/lsp/api/v1/auth/login获取访问令牌"
    else:
        message = "认证系统已禁用，可直接使用API，通过user_id参数指定用户"
    
    return AuthStatusResponse(
        auth_enabled=API_CONFIG.auth_enabled,
        message=message
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    用户登录
    注意：这是一个简化的示例，实际应该验证密码
    """
    if not API_CONFIG.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="认证系统未启用"
        )
    
    # 简化的密码验证（实际应该查询数据库）
    # 这里只是演示，任何密码都接受
    if not request.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户ID不能为空"
        )
    
    # 创建访问令牌
    access_token = create_access_token(
        data={"sub": request.user_id},
        expires_delta=timedelta(minutes=API_CONFIG.jwt_expire_minutes)
    )
    
    logger.info(f"用户 {request.user_id} 登录成功")
    
    return TokenResponse(
        access_token=access_token,
        expires_in=API_CONFIG.jwt_expire_minutes * 60,
        user_id=request.user_id
    )


@router.post("/demo-token/{user_id}", response_model=TokenResponse)
async def create_demo_token(user_id: str):
    """
    创建演示用的访问令牌（仅用于测试）
    生产环境应该删除此端点
    """
    if not API_CONFIG.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="认证系统未启用"
        )
    
    # 创建访问令牌
    access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=timedelta(minutes=API_CONFIG.jwt_expire_minutes)
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=API_CONFIG.jwt_expire_minutes * 60,
        user_id=user_id
    )