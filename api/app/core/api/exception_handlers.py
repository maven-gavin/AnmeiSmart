"""
全局异常处理逻辑
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .errors import ErrorCode
from .exceptions import AppException, BusinessException, SystemException
from .response import ApiResponse

logger = logging.getLogger(__name__)


def _build_response(code: int, message: str, data: Any = None, status_code: int = status.HTTP_200_OK) -> JSONResponse:
    """构建统一响应"""
    payload = ApiResponse.failure(code=code, message=message, data=data)
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(payload.model_dump(exclude_none=True, by_alias=True)),
    )


async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
    """处理 AppException 及其子类"""
    logger.warning(
        "业务异常: %s | details=%s | path=%s | method=%s | code=%s",
        exc.message, exc.details, request.url.path, request.method, exc.code
    )
    # 如果是系统错误，记录更详细的信息
    if exc.code == ErrorCode.SYSTEM_ERROR:
        logger.error(
            "系统异常详情: message=%s | path=%s | method=%s | code=%s | details=%s",
            exc.message, request.url.path, request.method, exc.code, exc.details,
            exc_info=True
        )
    return _build_response(
        code=exc.code,
        message=exc.message,
        data=exc.details or None,
        status_code=exc.status_code,
    )


async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """处理 FastAPI/Starlette 抛出的 HTTPException"""
    # 详细的调试信息
    logger.warning("=" * 80)
    logger.warning("HTTP异常详情:")
    logger.warning(f"  状态码: {exc.status_code}")
    logger.warning(f"  错误详情: {exc.detail}")
    logger.warning(f"  请求路径: {request.url.path}")
    logger.warning(f"  请求方法: {request.method}")
    logger.warning(f"  查询参数: {dict(request.query_params)}")
    logger.warning(f"  请求头:")
    for header, value in request.headers.items():
        if header.lower() not in ['authorization', 'cookie']:  # 不记录敏感信息
            logger.warning(f"    {header}: {value}")
    
    # 分析可能的错误原因
    path = request.url.path
    if path == "/api/v1/auth/roles":
        logger.warning("  分析: 前端请求了 /api/v1/auth/roles，但后端只有 /api/v1/auth/roles/details 端点")
        logger.warning("  建议: 检查前端代码，应该使用 /api/v1/auth/roles/details")
    elif path.startswith("/api/v1/profile/"):
        logger.warning("  分析: 前端请求了 /api/v1/profile/*，但 profile 路由已被注释掉")
        logger.warning("  建议: 检查前端代码，profile 相关功能已合并到 /api/v1/users/me")
    
    logger.warning("=" * 80)
    
    message = exc.detail if isinstance(exc.detail, str) else "请求处理失败"
    code = ErrorCode.BUSINESS_ERROR if exc.status_code < 500 else ErrorCode.SYSTEM_ERROR
    return _build_response(code=code, message=message, status_code=exc.status_code)


async def handle_validation_exception(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理请求体验证异常"""
    logger.warning("请求参数验证失败: errors=%s path=%s", exc.errors(), request.url.path)
    return _build_response(
        code=ErrorCode.VALIDATION_ERROR,
        message="请求参数验证失败",
        data={"errors": exc.errors()},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def handle_pydantic_validation_exception(request: Request, exc: ValidationError) -> JSONResponse:
    """处理Pydantic验证异常"""
    logger.warning("数据验证失败: errors=%s path=%s", exc.errors(), request.url.path)
    return _build_response(
        code=ErrorCode.VALIDATION_ERROR,
        message="数据验证失败",
        data={"errors": exc.errors()},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    """处理未捕获的异常"""
    logger.exception("系统异常: %s path=%s", exc, request.url.path)
    system_exc = SystemException()
    return _build_response(
        code=system_exc.code,
        message=system_exc.message,
        status_code=system_exc.status_code,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器"""
    app.add_exception_handler(AppException, handle_app_exception)
    app.add_exception_handler(BusinessException, handle_app_exception)
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(RequestValidationError, handle_validation_exception)
    app.add_exception_handler(ValidationError, handle_pydantic_validation_exception)
    app.add_exception_handler(Exception, handle_unexpected_exception)

