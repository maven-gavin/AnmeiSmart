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

from app.mcp.models.mcp import MCPToolGroup, MCPTool, MCPCallLog
from app.mcp.schemas.mcp import (
    MCPGroupCreate, MCPGroupUpdate, MCPGroupInfo,
    MCPToolInfo, MCPCallLogInfo
)
from app.core.encryption import get_encryption
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def transaction_handler(func):
    """事务处理装饰器 - 自动处理数据库事务"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 获取数据库session - 检查所有参数
        db = None
        
        # 首先检查kwargs中的db参数
        if 'db' in kwargs:
            db = kwargs['db']
        else:
            # 检查位置参数，通常db是第二个参数（第一个是self或cls）
            for arg in args:
                if hasattr(arg, 'commit') and hasattr(arg, 'rollback'):
                    db = arg
                    break
        
        if not db or not hasattr(db, 'commit'):
            logger.error(f"数据库session未找到或无效: {type(db)}")
            raise ValueError("数据库session未找到或无效")
        
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
    """MCP工具分组服务 - 所有方法返回Schema"""

    @staticmethod
    def _generate_api_key() -> str:
        """生成安全的API Key"""
        return f"mcp_key_{secrets.token_urlsafe(32)}"

    @staticmethod
    def _generate_server_code() -> str:
        """生成唯一的服务器代码"""
        return secrets.token_urlsafe(12)  # 生成16字符的URL安全字符串

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
    def _hash_api_key(api_key: str) -> str:
        """计算API密钥哈希（SHA-256）"""
        import hashlib
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    @staticmethod
    def build_mcp_server_url(server_code: str) -> str:
        """构建完整的MCP Server URL"""
        base_url = get_settings().MCP_SERVER_BASE_URL
        
        # 确保base_url不以斜杠结尾
        base_url = base_url.rstrip('/')
        
        # 构建MCP服务器URL
        return f"{base_url}/mcp/server/{server_code}/mcp"

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
                # 使用模型的hybrid_property自动处理解密
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

            # 生成唯一的server_code
            server_code = MCPGroupService._generate_server_code()
            
            # 确保server_code唯一性
            while True:
                existing_server_code = db.query(MCPToolGroup).filter(
                    MCPToolGroup.server_code == server_code
                ).first()
                
                if not existing_server_code:
                    break
                server_code = MCPGroupService._generate_server_code()

            # 创建分组
            group_data = {
                "id": str(uuid.uuid4()),
                "name": group_create.name,
                "description": group_create.description,
                "api_key": MCPGroupService._encrypt_api_key(api_key),
                "hashed_api_key": MCPGroupService._hash_api_key(api_key),
                "server_code": server_code,
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
    async def get_group_server_url(db: Session, group_id: str) -> str:
        """获取分组的完整MCP Server URL（管理员专用）"""
        try:
            group = db.query(MCPToolGroup).filter(MCPToolGroup.id == group_id).first()
            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="分组不存在"
                )

            if not group.server_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="分组尚未生成服务器代码"
                )

            # 构建并返回完整的MCP Server URL
            return MCPGroupService.build_mcp_server_url(group.server_code)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取分组MCP Server URL失败: group_id={group_id}, error={e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取MCP Server URL失败"
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
            if hasattr(group, 'hashed_api_key'):
                group.hashed_api_key = MCPGroupService._hash_api_key(new_api_key)
            group.updated_at = datetime.utcnow()
            db.flush()

            logger.warning(f"重新生成API Key: group_id={group_id}, admin={admin_user_id}")
            return new_api_key

        except HTTPException:
            raise

    @staticmethod
    @transaction_handler
    async def ensure_server_code(db: Session, group_id: str) -> str:
        """确保分组有server_code，如果没有则生成一个"""
        try:
            group = db.query(MCPToolGroup).filter(MCPToolGroup.id == group_id).first()
            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="分组不存在"
                )

            # 如果已经有server_code，直接返回
            if group.server_code:
                return group.server_code

            # 生成唯一的server_code
            server_code = MCPGroupService._generate_server_code()
            
            # 确保server_code唯一性
            while True:
                existing_server_code = db.query(MCPToolGroup).filter(
                    MCPToolGroup.server_code == server_code
                ).first()
                
                if not existing_server_code:
                    break
                server_code = MCPGroupService._generate_server_code()

            # 更新分组
            group.server_code = server_code
            group.updated_at = datetime.utcnow()
            db.flush()

            logger.info(f"为分组生成server_code: group_id={group_id}, server_code={server_code}")
            return server_code

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"生成server_code失败: group_id={group_id}, error={e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="生成服务器代码失败"
            )

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

    # =============== MCP工具管理方法 ===============

    @staticmethod
    async def get_tools(db: Session, group_id: Optional[str] = None) -> List[MCPToolInfo]:
        """获取MCP工具列表 - 返回Schema"""
        try:
            query = db.query(MCPTool).join(MCPToolGroup)
            
            if group_id:
                query = query.filter(MCPTool.group_id == group_id)
            
            tools = query.all()
            
            result = []
            for tool in tools:
                # 获取分组名称
                group = db.query(MCPToolGroup).filter(MCPToolGroup.id == tool.group_id).first()
                tool_info = MCPToolInfo.from_model(tool)
                tool_info.group_name = group.name if group else "未知分组"
                result.append(tool_info)
            
            logger.info(f"获取MCP工具列表成功: 共{len(result)}个工具")
            return result

        except Exception as e:
            logger.error(f"获取MCP工具列表失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取工具列表失败"
            )

    @staticmethod
    @transaction_handler  
    async def update_tool(db: Session, tool_id: str, tool_update: "MCPToolUpdate") -> MCPToolInfo:
        """更新MCP工具配置 - 返回Schema"""
        from app.mcp.schemas.mcp import MCPToolUpdate
        
        try:
            tool = db.query(MCPTool).filter(MCPTool.id == tool_id).first()
            if not tool:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="工具不存在"
                )

            # 更新字段
            update_data = tool_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(tool, field):
                    setattr(tool, field, value)
            
            tool.updated_at = datetime.utcnow()
            db.flush()

            result = MCPToolInfo.from_model(tool)
            logger.info(f"更新MCP工具成功: {tool.tool_name}")
            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新MCP工具失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新工具失败"
            )

    @staticmethod
    async def get_group_tools(db: Session, group_id: str) -> List[str]:
        """获取分组内的工具名称列表"""
        try:
            tools = db.query(MCPTool).filter(
                MCPTool.group_id == group_id,
                MCPTool.enabled == True
            ).all()
            
            return [tool.tool_name for tool in tools]

        except Exception as e:
            logger.error(f"获取分组工具列表失败: {e}")
            return []

    @staticmethod
    async def is_tool_in_group(db: Session, tool_name: str, group_id: str) -> bool:
        """检查工具是否在指定分组内且启用"""
        try:
            tool = db.query(MCPTool).filter(
                MCPTool.tool_name == tool_name,
                MCPTool.group_id == group_id,
                MCPTool.enabled == True
            ).first()
            
            return tool is not None

        except Exception as e:
            logger.error(f"检查工具分组权限失败: {e}")
            return False

    @staticmethod
    @transaction_handler
    async def sync_tools_from_mcp_server(db: Session, mcp_tools_info: List[dict]) -> int:
        """从MCP服务器同步工具信息 - 返回更新数量"""
        try:
            updated_count = 0
            
            for tool_info in mcp_tools_info:
                # 查找现有工具
                existing_tool = db.query(MCPTool).filter(
                    MCPTool.tool_name == tool_info.get("name")
                ).first()
                
                if existing_tool:
                    # 更新现有工具
                    existing_tool.description = tool_info.get("description", "")
                    existing_tool.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # 创建新工具（需要分配到默认分组）
                    default_group = db.query(MCPToolGroup).filter(
                        MCPToolGroup.name == "默认分组"
                    ).first()
                    
                    if not default_group:
                        # 创建默认分组
                        default_group = MCPToolGroup(
                            id=str(uuid.uuid4()),
                            name="默认分组",
                            description="系统自动创建的默认工具分组",
                            api_key=MCPGroupService._encrypt_api_key(MCPGroupService._generate_api_key()),
                            enabled=True,
                            created_by="system",
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        db.add(default_group)
                        db.flush()
                    
                    new_tool = MCPTool(
                        id=str(uuid.uuid4()),
                        tool_name=tool_info.get("name"),
                        group_id=default_group.id,
                        version="1.0.0",
                        description=tool_info.get("description", ""),
                        enabled=True,
                        timeout_seconds=30,
                        config_data={},
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(new_tool)
                    updated_count += 1
            
            db.flush()
            logger.info(f"从MCP服务器同步工具成功: 更新{updated_count}个工具")
            return updated_count

        except Exception as e:
            logger.error(f"同步MCP工具失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="同步工具失败"
            )

    @staticmethod
    async def validate_api_key(db: Session, api_key: str) -> Optional[Dict[str, Any]]:
        """验证API Key并返回分组信息（安全版：哈希匹配，兼容解密对比）"""
        try:
            import hashlib
            api_key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()

            # 优先使用哈希匹配（需要DB新增 hashed_api_key 字段后生效）
            if hasattr(MCPToolGroup, 'hashed_api_key'):
                group = db.query(MCPToolGroup).filter(
                    MCPToolGroup.enabled == True,
                    MCPToolGroup.hashed_api_key == api_key_hash
                ).first()
                if group:
                    return {
                        "id": group.id,
                        "name": group.name,
                        "description": group.description,
                        "user_tier_access": group.user_tier_access,
                        "allowed_roles": group.allowed_roles
                    }

            # 兼容路径：解密遍历（待迁移数据期间保留）
            groups = db.query(MCPToolGroup).filter(MCPToolGroup.enabled == True).all()
            for group in groups:
                decrypted_key = MCPGroupService._decrypt_api_key(group.api_key)
                if decrypted_key == api_key:
                    return {
                        "id": group.id,
                        "name": group.name,
                        "description": group.description,
                        "user_tier_access": group.user_tier_access,
                        "allowed_roles": group.allowed_roles
                    }
            return None

        except Exception as e:
            logger.error(f"验证API Key失败: {e}")
            return None
