"""
任务数据转换器
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.tasks.domain.entities.task import TaskEntity
from app.tasks.schemas.task import TaskResponse, UserInfo


class TaskConverter:
    """任务数据转换器"""
    
    @staticmethod
    def to_response(task: TaskEntity, db: Optional[Session] = None) -> TaskResponse:
        """转换任务实体为响应格式"""
        # 获取用户信息
        created_by_info = None
        assigned_to_info = None
        
        if db:
            try:
                if task.createdBy:
                    created_by_info = TaskConverter._get_user_info(db, task.createdBy)
                if task.assignedTo:
                    assigned_to_info = TaskConverter._get_user_info(db, task.assignedTo)
            except Exception:
                # 如果获取用户信息失败，使用默认值
                pass
        
        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            task_type=task.taskType,
            status=task.status,
            priority=task.priority,
            due_date=task.dueDate,
            created_by=created_by_info,
            assigned_to=assigned_to_info,
            assigned_at=task.assignedAt,
            related_object_type=task.relatedObjectType,
            related_object_id=task.relatedObjectId,
            task_data=task.taskData,
            completed_at=task.completedAt,
            result=task.result,
            notes=task.notes,
            created_at=task.createdAt,
            updated_at=task.updatedAt
        )
    
    @staticmethod
    def to_list_response(tasks: List[TaskEntity], db: Optional[Session] = None) -> List[TaskResponse]:
        """转换任务列表为响应格式"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"TaskConverter开始转换 {len(tasks)} 个任务为响应格式")
        response_tasks = []
        
        for i, task in enumerate(tasks):
            try:
                logger.debug(f"转换第 {i+1} 个任务响应: ID={task.id}")
                response_task = TaskConverter.to_response(task, db)
                response_tasks.append(response_task)
                logger.debug(f"成功转换第 {i+1} 个任务响应")
            except Exception as convert_error:
                logger.error(f"转换第 {i+1} 个任务响应失败: {convert_error}")
                import traceback
                logger.error(f"转换响应错误详细堆栈: {traceback.format_exc()}")
                raise
        
        logger.info(f"TaskConverter成功转换 {len(response_tasks)} 个任务响应")
        return response_tasks
    
    @staticmethod
    def _get_user_info(db: Session, user_id: str) -> Optional[UserInfo]:
        """获取用户信息"""
        try:
            from app.identity_access.models.user import User
            
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return UserInfo(
                    id=user.id,
                    username=user.username,
                    email=user.email
                )
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def from_create_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """从创建请求转换为领域对象参数"""
        return {
            "title": request_data.get("title"),
            "taskType": request_data.get("task_type"),
            "description": request_data.get("description"),
            "priority": request_data.get("priority"),
            "dueDate": request_data.get("due_date"),
            "relatedObjectType": request_data.get("related_object_type"),
            "relatedObjectId": request_data.get("related_object_id"),
            "taskData": request_data.get("task_data"),
            "assignedTo": request_data.get("assigned_to")
        }
    
    @staticmethod
    def from_update_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """从更新请求转换为领域对象参数"""
        return {
            "title": request_data.get("title"),
            "description": request_data.get("description"),
            "status": request_data.get("status"),
            "priority": request_data.get("priority"),
            "notes": request_data.get("notes"),
            "result": request_data.get("result")
        }
    
    @staticmethod
    def from_model(model) -> TaskEntity:
        """从ORM模型转换为领域实体"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.debug(f"TaskConverter.from_model开始转换模型: ID={model.id}, type={model.task_type}, status={model.status}, priority={model.priority}")
            
            # 检查关键字段
            logger.debug(f"模型字段检查 - title: {model.title}, task_type: {model.task_type}, status: {model.status}, priority: {model.priority}")
            
            task = TaskEntity(
                id=model.id,
                title=model.title,
                taskType=model.task_type,
                description=model.description,
                status=model.status,
                priority=model.priority,
                createdBy=model.created_by,
                assignedTo=model.assigned_to,
                assignedAt=model.assigned_at,
                relatedObjectType=model.related_object_type,
                relatedObjectId=model.related_object_id,
                taskData=model.task_data,
                dueDate=model.due_date,
                completedAt=model.completed_at,
                result=model.result,
                notes=model.notes,
                createdAt=model.created_at,
                updatedAt=model.updated_at
            )
            
            logger.debug(f"TaskConverter.from_model成功转换模型: ID={model.id}")
            return task
            
        except Exception as e:
            logger.error(f"TaskConverter.from_model转换失败: {e}")
            logger.error(f"模型数据: ID={getattr(model, 'id', 'N/A')}, type={getattr(model, 'task_type', 'N/A')}, status={getattr(model, 'status', 'N/A')}, priority={getattr(model, 'priority', 'N/A')}")
            import traceback
            logger.error(f"from_model错误详细堆栈: {traceback.format_exc()}")
            raise
    
    @staticmethod
    def to_model_dict(task: TaskEntity) -> Dict[str, Any]:
        """转换领域实体为ORM模型字典"""
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "task_type": task.taskType,
            "status": task.status,
            "priority": task.priority,
            "created_by": task.createdBy,
            "assigned_to": task.assignedTo,
            "assigned_at": task.assignedAt,
            "related_object_type": task.relatedObjectType,
            "related_object_id": task.relatedObjectId,
            "task_data": task.taskData,
            "due_date": task.dueDate,
            "completed_at": task.completedAt,
            "result": task.result,
            "notes": task.notes,
            "created_at": task.createdAt,
            "updated_at": task.updatedAt
        }
