"""
统一业务异常定义
"""

from typing import Any, Dict, Optional

from fastapi import status

from .errors import ErrorCode


class AppException(Exception):
    """应用统一异常基类"""

    def __init__(
        self,
        message: str,
        *,
        code: int,
        status_code: int,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class BusinessException(AppException):
    """业务异常"""

    def __init__(
        self,
        message: str,
        *,
        code: int = ErrorCode.BUSINESS_ERROR,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            code=code,
            status_code=status_code,
            details=details,
        )


class NetworkException(AppException):
    """网络异常"""

    def __init__(
        self,
        message: str = "网络异常，请稍后重试",
        *,
        code: int = ErrorCode.NETWORK_ERROR,
        status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            code=code,
            status_code=status_code,
            details=details,
        )


class SystemException(AppException):
    """系统异常"""

    def __init__(
        self,
        message: str = "系统异常，请联系管理员",
        *,
        code: int = ErrorCode.SYSTEM_ERROR,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            code=code,
            status_code=status_code,
            details=details,
        )

