import secrets
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi import HTTPException, status
from functools import wraps
import logging

from app.db.models.mcp import MCPToolGroup, MCPTool, MCPCallLog
from app.schemas.mcp import (
    MCPGroupCreate, MCPGroupUpdate, MCPGroupInfo,
    MCPToolInfo, MCPCallLogInfo
)
from app.core.encryption import get_encryption

logger = logging.getLogger(__name__)


def transaction_handler(func):
    """事务处理装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 获取数据库session (假设是第一个参数)
        db = args[1] if len(args) > 1 else kwargs.get('db')
        if not db:
            raise ValueError("数据库session未找到")
        
        try:
            result = await func(*args, **kwargs)
            db.commit()
            return result
        except (SQLAlchemyError, HTTPException) as e:
            db.rollback()
            if isinstance(e, HTTPException):
                raise e
            logger.error(f"数据库操作失败: {func.__name__}, error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"数据库操作失败: {str(e)}"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"未知错误: {func.__name__}, error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"操作失败: {str(e)}"
            )
    return wrapper


class MCPGroupService:
    """MCP工具分组服务 - 遵循DDD原则，所有方法返回Schema"""

    @staticmethod
    def _generate_api_key() -> str:
        """生成安全的API Key"""
        return f"mcp_key_{secrets.token_urlsafe(32)}"

    @staticmethod
    def _encrypt_api_key(api_key: str) -> str:
        """加密API密钥"""
        try:
            encryption_manager = get_encryption()
            return encryption_manager.encrypt(api_key)
        except Exception as e:
            logger.error(f"API密钥加密失败: {e}")
            # 如果加密失败，返回原值（向后兼容）
            return api_key

    @staticmethod
    def _decrypt_api_key(encrypted_api_key: str) -> str:
        """解密API密钥"""
        try:
            encryption_manager = get_encryption()
            return encryption_manager.decrypt(encrypted_api_key)
        except Exception as e:
            logger.warning(f"API密钥解密失败，可能是未加密的密钥: {e}")
            # 如果解密失败，返回原值（向后兼容）
            return encrypted_api_key

    @staticmethod
    async def get_all_groups(db: Session) -> List[MCPGroupInfo]:
        """获取所有MCP分组列表 - 返回Schema"""
        try:
            # 查询分组并统计工具数量
            groups_with_count = db.query(
                MCPToolGroup,
                func.count(MCPTool.id).label('tools_count')
            ).outerjoin(
                MCPTool, and_(MCPTool.group_id == MCPToolGroup.id, MCPTool.enabled == True)
            ).group_by(MCPToolGroup.id).all()

            result = []
            for group, tools_count in groups_with_count:
                # 解密API密钥用于脱敏显示
                group.api_key = MCPGroupService._decrypt_api_key(group.api_key)
                group_info = MCPGroupInfo.from_model(group)
                group_info.tools_count = tools_count
                result.append(group_info)

            logger.info(f"获取MCP分组列表成功，共{len(result)}个分组")
            return result

        except Exception as e:
            logger.error(f"获取MCP分组列表失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取分组列表失败"
            )

    @staticmethod
    async def get_group_by_id(db: Session, group_id: str) -> Optional[MCPGroupInfo]:
        """根据ID获取MCP分组 - 返回Schema"""
        try:
            group = db.query(MCPToolGroup).filter(MCPToolGroup.id == group_id).first()
            if not group:
                return None

            # 解密API密钥用于脱敏显示
            group.api_key = MCPGroupService._decrypt_api_key(group.api_key)
            return MCPGroupInfo.from_model(group)

        except Exception as e:
            logger.error(f"获取MCP分组失败: group_id={group_id}, error={e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取分组信息失败"
            )

    @staticmethod
    @transaction_handler
    async def create_group(db: Session, group_create: MCPGroupCreate, created_by: str) -> MCPGroupInfo:
        """创建MCP工具分组并生成API Key - 返回Schema"""
        try:
            # 检查分组名称是否已存在
            existing_group = db.query(MCPToolGroup).filter(MCPToolGroup.name == group_create.name).first()
            if existing_group:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"分组名称 '{group_create.name}' 已存在"
                )

            # 生成唯一的API Key
            api_key = MCPGroupService._generate_api_key()
            
            # 确保API Key唯一性（检查加密和未加密的版本）
            while True:
                encrypted_key = MCPGroupService._encrypt_api_key(api_key)
                existing_encrypted = db.query(MCPToolGroup).filter(
                    MCPToolGroup.api_key == encrypted_key
                ).first()
                existing_plain = db.query(MCPToolGroup).filter(
                    MCPToolGroup.api_key == api_key
                ).first()
                
                if not existing_encrypted and not existing_plain:
                    break
                api_key = MCPGroupService._generate_api_key()

            # 创建分组
            group_data = {
                "id": str(uuid.uuid4()),
                "name": group_create.name,
                "description": group_create.description,
                "api_key": MCPGroupService._encrypt_api_key(api_key),
                "user_tier_access": group_create.user_tier_access,
                "allowed_roles": group_create.allowed_roles,
                "enabled": group_create.enabled,
                "created_by": created_by,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            group = MCPToolGroup(**group_data)
            db.add(group)
            db.flush()  # 获取ID但不提交事务

            # 准备返回数据（使用明文API密钥用于脱敏显示）
            group.api_key = api_key
            result = MCPGroupInfo.from_model(group)

            logger.info(f"创建MCP分组成功: name={group_create.name}, creator={created_by}")
            return result

        except HTTPException:
            raise
        except IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="分组名称已存在或数据约束冲突"
            )

    @staticmethod
    @transaction_handler
    async def update_group(db: Session, group_id: str, group_update: MCPGroupUpdate) -> MCPGroupInfo:
        """更新MCP分组信息 - 返回Schema"""
        try:
            group = db.query(MCPToolGroup).filter(MCPToolGroup.id == group_id).first()
            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="分组不存在"
                )

            # 检查名称唯一性（如果更新了名称）
            if group_update.name and group_update.name != group.name:
                existing_group = db.query(MCPToolGroup).filter(
                    and_(MCPToolGroup.name == group_update.name, MCPToolGroup.id != group_id)
                ).first()
                if existing_group:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"分组名称 '{group_update.name}' 已存在"
                    )

            # 更新字段
            update_data = group_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(group, field, value)

            group.updated_at = datetime.utcnow()
            db.flush()

            # 解密API密钥用于脱敏显示
            group.api_key = MCPGroupService._decrypt_api_key(group.api_key)
            result = MCPGroupInfo.from_model(group)

            logger.info(f"更新MCP分组成功: group_id={group_id}")
            return result

        except HTTPException:
            raise
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="数据约束冲突"
            )

    @staticmethod
    @transaction_handler
    async def delete_group(db: Session, group_id: str) -> bool:
        """删除MCP分组（级联删除关联工具）"""
        try:
            group = db.query(MCPToolGroup).filter(MCPToolGroup.id == group_id).first()
            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="分组不存在"
                )

            # 获取工具数量用于日志
            tools_count = db.query(MCPTool).filter(MCPTool.group_id == group_id).count()

            db.delete(group)
            db.flush()

            logger.warning(f"删除MCP分组成功: group_id={group_id}, tools_deleted={tools_count}")
            return True

        except HTTPException:
            raise

    @staticmethod
    async def get_group_api_key(db: Session, group_id: str) -> str:
        """获取分组API Key（管理员专用）- 返回明文密钥"""
        try:
            group = db.query(MCPToolGroup).filter(MCPToolGroup.id == group_id).first()
            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="分组不存在"
                )

            # 解密并返回明文API密钥
            return MCPGroupService._decrypt_api_key(group.api_key)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取分组API Key失败: group_id={group_id}, error={e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取API Key失败"
            )

    @staticmethod
    @transaction_handler
    async def regenerate_api_key(db: Session, group_id: str, admin_user_id: str) -> str:
        """重新生成分组API Key（安全操作）- 返回新的明文密钥"""
        try:
            group = db.query(MCPToolGroup).filter(MCPToolGroup.id == group_id).first()
            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="分组不存在"
                )

            # 生成新的API Key
            new_api_key = MCPGroupService._generate_api_key()
            
            # 确保API Key唯一性
            while True:
                encrypted_key = MCPGroupService._encrypt_api_key(new_api_key)
                existing_encrypted = db.query(MCPToolGroup).filter(
                    MCPToolGroup.api_key == encrypted_key
                ).first()
                existing_plain = db.query(MCPToolGroup).filter(
                    MCPToolGroup.api_key == new_api_key
                ).first()
                
                if not existing_encrypted and not existing_plain:
                    break
                new_api_key = MCPGroupService._generate_api_key()

            # 更新数据库
            group.api_key = MCPGroupService._encrypt_api_key(new_api_key)
            group.updated_at = datetime.utcnow()
            db.flush()

            logger.warning(f"重新生成API Key: group_id={group_id}, admin={admin_user_id}")
            return new_api_key

        except HTTPException:
            raise

    @staticmethod
    async def validate_api_key(db: Session, api_key: str) -> Optional[Dict[str, Any]]:
        """验证API Key并返回分组信息"""
        try:
            # 尝试匹配明文和加密的API密钥
            group = db.query(MCPToolGroup).filter(
                and_(
                    MCPToolGroup.enabled == True,
                    MCPToolGroup.api_key == api_key  # 先尝试明文匹配
                )
            ).first()

            if not group:
                # 尝试加密匹配
                groups = db.query(MCPToolGroup).filter(MCPToolGroup.enabled == True).all()
                for g in groups:
                    try:
                        decrypted_key = MCPGroupService._decrypt_api_key(g.api_key)
                        if decrypted_key == api_key:
                            group = g
                            break
                    except:
                        continue

            if not group:
                return None

            return {
                "id": group.id,
                "name": group.name,
                "user_tier_access": group.user_tier_access or ["internal"],
                "allowed_roles": group.allowed_roles or [],
                "enabled": group.enabled
            }

        except Exception as e:
            logger.error(f"验证API Key失败: error={e}")
            return None

    @staticmethod
    async def get_group_tools(db: Session, group_id: str) -> List[str]:
        """获取分组内的工具列表"""
        try:
            tools = db.query(MCPTool).filter(
                and_(MCPTool.group_id == group_id, MCPTool.enabled == True)
            ).all()

            return [tool.name for tool in tools]

        except Exception as e:
            logger.error(f"获取分组工具列表失败: group_id={group_id}, error={e}")
            return []

    @staticmethod
    async def is_tool_in_group(db: Session, tool_name: str, group_id: str) -> bool:
        """检查工具是否属于指定分组且已启用"""
        try:
            tool = db.query(MCPTool).filter(
                and_(
                    MCPTool.name == tool_name,
                    MCPTool.group_id == group_id,
                    MCPTool.enabled == True
                )
            ).first()

            return tool is not None

        except Exception as e:
            logger.error(f"检查工具分组归属失败: tool={tool_name}, group={group_id}, error={e}")
            return False

    @staticmethod
    @transaction_handler
    async def log_mcp_call(
        db: Session,
        tool_name: str,
        group_id: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        success: bool,
        duration_ms: int,
        error_message: str = None,
        caller_app_id: str = None
    ) -> MCPCallLogInfo:
        """记录MCP调用日志 - 返回Schema"""
        try:
            log_entry = MCPCallLog(
                id=f"call_{secrets.token_urlsafe(16)}",
                tool_name=tool_name,
                group_id=group_id,
                caller_app_id=caller_app_id,
                request_data=request_data,
                response_data=response_data,
                success=success,
                error_message=error_message,
                duration_ms=duration_ms,
                created_at=datetime.utcnow()
            )
            db.add(log_entry)
            db.flush()

            result = MCPCallLogInfo.from_model(log_entry)
            logger.info(f"记录MCP调用日志成功: tool={tool_name}, success={success}")
            return result

        except Exception as e:
            logger.error(f"记录MCP调用日志失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="记录调用日志失败"
            ) 