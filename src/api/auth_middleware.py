"""
认证中间件
可通过配置开关控制是否启用认证
"""
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from ..db.configs.global_config import API_CONFIG
from ..utils.logger import logger


# Bearer token security scheme
security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=API_CONFIG.jwt_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        API_CONFIG.jwt_secret_key, 
        algorithm=API_CONFIG.jwt_algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> dict:
    """验证令牌"""
    try:
        payload = jwt.decode(
            token, 
            API_CONFIG.jwt_secret_key, 
            algorithms=[API_CONFIG.jwt_algorithm]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = None
) -> Optional[str]:
    """
    获取当前用户
    如果认证未启用，返回请求中的user_id参数或默认用户
    如果认证启用，从JWT token中解析用户ID
    """
    # 如果认证未启用，直接从请求参数获取user_id
    if not API_CONFIG.auth_enabled:
        # 尝试从查询参数获取
        user_id = request.query_params.get("user_id")
        if user_id:
            return user_id
        
        # 尝试从路径参数获取
        if hasattr(request, "path_params"):
            user_id = request.path_params.get("user_id")
            if user_id:
                return user_id
        
        # 返回默认用户
        return "default_user"
    
    # 认证启用时，需要验证token
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证token并获取用户信息
    payload = verify_token(credentials.credentials)
    user_id = payload.get("sub")  # JWT标准中，sub字段表示用户标识
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的用户令牌",
        )
    
    return user_id


def optional_auth(func: Callable) -> Callable:
    """
    可选认证装饰器
    根据配置决定是否需要认证
    """
    async def wrapper(*args, **kwargs):
        # 获取request对象
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            # 如果没有request对象，直接执行原函数
            return await func(*args, **kwargs)
        
        # 根据配置决定是否需要认证
        if API_CONFIG.auth_enabled:
            # 需要认证时，尝试获取credentials
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                credentials = HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials=token
                )
            else:
                credentials = None
            
            # 获取当前用户
            user_id = await get_current_user(request, credentials)
            
            # 将user_id注入到kwargs中
            kwargs["current_user_id"] = user_id
        
        return await func(*args, **kwargs)
    
    return wrapper


class AuthMiddleware:
    """认证中间件类"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # 记录请求信息
            path = scope["path"]
            method = scope["method"]
            
            # 如果认证启用，记录认证状态
            if API_CONFIG.auth_enabled:
                headers = dict(scope["headers"])
                auth_header = headers.get(b"authorization", b"").decode()
                has_auth = bool(auth_header)
                logger.debug(f"认证中间件: {method} {path}, 认证头: {has_auth}")
            else:
                logger.debug(f"认证中间件: {method} {path}, 认证已禁用")
        
        await self.app(scope, receive, send)