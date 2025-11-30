"""
统一的API响应模型定义
"""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    标准API响应模型

    Attributes:
        code: 业务状态码，0表示成功
        message: 业务提示信息
        data: 业务数据
        timestamp: 响应时间戳（UTC）
    """

    code: int = Field(..., description="业务状态码，0表示成功")
    message: str = Field(..., description="业务提示信息")
    data: Optional[T] = Field(default=None, description="业务数据")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="响应时间戳（UTC时间）",
    )

    @classmethod
    def success(cls, data: Optional[T] = None, message: str = "success") -> "ApiResponse[T]":
        """生成成功的响应"""
        return cls(code=0, message=message, data=data)

    @classmethod
    def failure(cls, code: int, message: str, data: Optional[T] = None) -> "ApiResponse[T]":
        """生成失败的响应"""
        return cls(code=code, message=message, data=data)

class PaginatedRecords(BaseModel, Generic[T]):
    """分页响应基础模型"""
    items: List[T] = Field(..., description="数据项列表")
    total: int = Field(..., description="总数量")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")