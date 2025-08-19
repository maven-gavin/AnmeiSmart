"""
待办任务相关的Pydantic模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    """待办任务基础模型"""
    title: str = Field(..., min_length=1, max_length=500, description="任务标题")
    description: Optional[str] = Field(None, max_length=2000, description="任务描述")
    task_type: str = Field(..., description="任务类型")
    priority: str = Field("medium", description="任务优先级：low, medium, high, urgent")
    due_date: Optional[datetime] = Field(None, description="截止时间")


class CreateTaskRequest(TaskBase):
    """创建待办任务请求"""
    related_object_type: Optional[str] = Field(None, description="关联对象类型")
    related_object_id: Optional[str] = Field(None, description="关联对象ID")
    task_data: Optional[Dict[str, Any]] = Field(None, description="任务相关数据")
    assigned_to: Optional[str] = Field(None, description="分配给用户ID")


class UpdateTaskRequest(BaseModel):
    """更新待办任务请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="任务标题")
    description: Optional[str] = Field(None, max_length=2000, description="任务描述")
    status: Optional[str] = Field(None, description="任务状态")
    priority: Optional[str] = Field(None, description="任务优先级")
    notes: Optional[str] = Field(None, description="处理备注")
    result: Optional[Dict[str, Any]] = Field(None, description="处理结果")


class UserInfo(BaseModel):
    """用户信息"""
    id: str
    username: str
    email: str


class TaskResponse(TaskBase):
    """待办任务响应模型"""
    id: str
    status: str
    created_by: Optional[UserInfo] = None
    assigned_to: Optional[UserInfo] = None
    assigned_at: Optional[datetime] = None
    related_object_type: Optional[str] = None
    related_object_id: Optional[str] = None
    task_data: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_model(task) -> "TaskResponse":
        """从待办任务模型转换为响应模型"""
        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            task_type=task.task_type,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date,
            created_by=UserInfo(
                id=task.created_by_user.id,
                username=task.created_by_user.username,
                email=task.created_by_user.email
            ) if task.created_by_user else None,
            assigned_to=UserInfo(
                id=task.assigned_to_user.id,
                username=task.assigned_to_user.username,
                email=task.assigned_to_user.email
            ) if task.assigned_to_user else None,
            assigned_at=task.assigned_at,
            related_object_type=task.related_object_type,
            related_object_id=task.related_object_id,
            task_data=task.task_data,
            completed_at=task.completed_at,
            result=task.result,
            notes=task.notes,
            created_at=task.created_at,
            updated_at=task.updated_at
        )


class ClaimTaskRequest(BaseModel):
    """认领任务请求"""
    pass  # 不需要额外参数，用户ID从认证中获取
