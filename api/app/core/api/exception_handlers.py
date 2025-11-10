"""
全局异常处理逻辑
"""

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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
        content=payload.dict(exclude_none=True),
    )


async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
    """处理 AppException 及其子类"""
    logger.warning("业务异常: %s | details=%s | path=%s", exc.message, exc.details, request.url.path)
    return _build_response(
        code=exc.code,
        message=exc.message,
        data=exc.details or None,
        status_code=exc.status_code,
    )


async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """处理 FastAPI/Starlette 抛出的 HTTPException"""
    logger.warning("HTTP异常: status=%s detail=%s path=%s", exc.status_code, exc.detail, request.url.path)
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

