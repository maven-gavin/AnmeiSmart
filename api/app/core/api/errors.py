"""
业务错误码定义
"""

from enum import IntEnum


class ErrorCode(IntEnum):
    """统一错误码定义"""

    SUCCESS = 0
    VALIDATION_ERROR = 40000
    BUSINESS_ERROR = 40001
    PERMISSION_DENIED = 40003
    NOT_FOUND = 40400
    NETWORK_ERROR = 50001
    SYSTEM_ERROR = 50000

