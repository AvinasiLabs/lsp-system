"""
LSP积分系统 - FastAPI主应用程序
"""

import os
import json
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

from .api.health_data_api import router as health_data_router
from .api.auth_api import router as auth_router
from .api.score_api import router as score_router
from .api.auth_middleware import AuthMiddleware
from .utils.logger import logger
from .db.postgresql import POSTGRES_POOL
from .db.configs.global_config import API_CONFIG


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件 - 打印所有请求参数和响应"""

    async def dispatch(self, request: Request, call_next):
        # 记录开始时间
        start_time = time.time()

        # 获取请求信息
        method = request.method
        url = str(request.url)

        # 获取查询参数
        query_params = dict(request.query_params)

        # 获取请求体（如果是POST/PUT等）
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    body = body_bytes.decode('utf-8')
                    try:
                        body = json.loads(body)
                    except:
                        pass  # 保持原始字符串格式

                # 重新构造request，因为body已被读取
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                request._receive = receive
            except:
                body = "无法读取请求体"

        # 打印请求信息
        print(f"\n{'='*80}")
        print(f"📥 请求: {method} {url}")
        print(f"⏰ 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        if query_params:
            print(f"🔍 查询参数:")
            for key, value in query_params.items():
                print(f"   {key}: {value}")

        if body:
            print(f"📦 请求体:")
            if isinstance(body, dict):
                for key, value in body.items():
                    print(f"   {key}: {value}")
            else:
                print(f"   {body}")

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 尝试获取响应体
        response_body = None
        try:
            # 读取响应体
            body_bytes = b""
            async for chunk in response.body_iterator:
                body_bytes += chunk

            if body_bytes:
                response_text = body_bytes.decode('utf-8')
                try:
                    response_body = json.loads(response_text)
                except:
                    response_body = response_text

            # 重新构造响应
            from fastapi.responses import Response
            new_response = Response(
                content=body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            response = new_response
        except Exception as e:
            response_body = f"无法读取响应体: {e}"

        # 打印响应信息
        print(f"📤 响应状态: {response.status_code}")
        print(f"⏱️  处理时间: {process_time:.3f}秒")

        if response_body:
            print(f"📋 响应体:")
            if isinstance(response_body, dict):
                # 格式化打印JSON响应
                print(json.dumps(response_body, ensure_ascii=False, indent=2))
            else:
                print(f"   {response_body}")

        print(f"{'='*80}\n")

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("LSP积分系统启动中...")
    logger.info(f"认证系统: {'已启用' if API_CONFIG.auth_enabled else '已禁用'}")

    # 测试数据库连接
    try:
        result = POSTGRES_POOL.select_data(table_name="health_metric", conditions="1=1 LIMIT 1")
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
    openapi_url="/lsp/openapi.json",
)

# 添加请求日志中间件（最先添加，确保能捕获所有请求）
app.add_middleware(RequestLoggingMiddleware)

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
        "auth_enabled": API_CONFIG.auth_enabled,
    }


@app.get("/lsp/health")
async def health_check():
    """健康检查端点"""
    try:
        # 检查数据库连接
        result = POSTGRES_POOL.select_data(table_name="health_metric", conditions="1=1 LIMIT 1")
        db_status = "healthy" if result is not None else "unhealthy"
    except:
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "services": {"api": "healthy", "database": db_status},
    }


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """404错误处理"""
    return JSONResponse(status_code=404, content={"error": "Not found", "message": f"路径 {request.url.path} 不存在"})


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """500错误处理"""
    logger.error(f"内部服务器错误: {exc}")
    return JSONResponse(
        status_code=200, content={"error": "Internal server error", "message": "服务器内部错误，请稍后重试"}
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
    uvicorn.run("src.main:app", host=host, port=port, reload=reload, log_level="info")


if __name__ == "__main__":
    main()
