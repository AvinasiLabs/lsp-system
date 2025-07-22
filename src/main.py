"""
LSP积分系统 - FastAPI主应用程序
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .api.health_data_api import router as health_data_router
from .api.auth_api import router as auth_router
from .api.score_api import router as score_router
from .api.auth_middleware import AuthMiddleware
from .utils.logger import logger
from .db.postgresql import POSTGRES_POOL
from .db.configs.global_config import API_CONFIG


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("LSP积分系统启动中...")
    logger.info(f"认证系统: {'已启用' if API_CONFIG.auth_enabled else '已禁用'}")
    
    # 测试数据库连接
    try:
        result = POSTGRES_POOL.select_data(
            table_name="apple_healthkit",
            conditions="1=1 LIMIT 1"
        )
        logger.info(f"数据库连接成功，healthkit表中有 {len(result) if result else 0} 条测试数据")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
    
    yield
    
    # 关闭时
    logger.info("LSP积分系统正在关闭...")
    # 这里可以添加清理代码


# 创建FastAPI应用
app = FastAPI(
    title="LSP积分系统",
    description="基于健康数据的长寿积分计算系统",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/lsp/docs",
    redoc_url="/lsp/redoc",
    openapi_url="/lsp/openapi.json"
)

# 添加认证中间件
app.add_middleware(AuthMiddleware)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CONFIG.cors_origins,
    allow_credentials=API_CONFIG.cors_allow_credentials,
    allow_methods=API_CONFIG.cors_allow_methods,
    allow_headers=API_CONFIG.cors_allow_headers,
)

# 注册路由
app.include_router(health_data_router)
app.include_router(auth_router)
app.include_router(score_router)


@app.get("/lsp")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用LSP积分系统",
        "version": "1.0.0",
        "docs": "/lsp/docs",
        "redoc": "/lsp/redoc",
        "auth_enabled": API_CONFIG.auth_enabled
    }


@app.get("/lsp/health")
async def health_check():
    """健康检查端点"""
    try:
        # 检查数据库连接
        result = POSTGRES_POOL.select_data(
            table_name="apple_healthkit",
            conditions="1=1 LIMIT 1"
        )
        db_status = "healthy" if result is not None else "unhealthy"
    except:
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "services": {
            "api": "healthy",
            "database": db_status
        }
    }


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """404错误处理"""
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "message": f"路径 {request.url.path} 不存在"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """500错误处理"""
    logger.error(f"内部服务器错误: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": "服务器内部错误，请稍后重试"}
    )


def main():
    """启动函数"""
    # 使用配置中的值
    host = API_CONFIG.host
    port = API_CONFIG.port
    reload = API_CONFIG.reload
    
    logger.info(f"启动服务器: {host}:{port}")
    logger.info(f"认证系统: {'已启用' if API_CONFIG.auth_enabled else '已禁用'}")
    
    # 启动服务器
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()