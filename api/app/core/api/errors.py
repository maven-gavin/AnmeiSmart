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
    INVALID_CREDENTIALS = 40002  # 无效的凭证（用户名/密码错误）
    INVALID_TOKEN = 40004  # 无效的令牌
    USER_DISABLED = 40005  # 用户已被禁用
    NOT_FOUND = 40400
    RESOURCE_NOT_FOUND = 40400  # 资源不存在（与 NOT_FOUND 相同，保持兼容性）
    NETWORK_ERROR = 50001
    SYSTEM_ERROR = 50000

