"""
Dify连接管理服务
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from app.db.models.system import DifyConnection, AIModelConfig, AgentType, SyncStatus
from app.services.ai.dify_client import DifyAPIClient
from app.schemas.system import DifyConnectionInfo

logger = logging.getLogger(__name__)

class DifyConnectionService:
    """Dify连接管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_connection(self, name: str, api_base_url: str, api_key: str, 
                         description: Optional[str] = None, is_default: bool = False) -> DifyConnection:
        """创建Dify连接"""
        try:
            # 如果设为默认，取消其他默认连接
            if is_default:
                self.db.query(DifyConnection).update({"is_default": False})
            
            connection = DifyConnection(
                name=name,
                api_base_url=api_base_url,
                api_key=api_key,
                description=description,
                is_default=is_default,
                sync_status=SyncStatus.NOT_SYNCED
            )
            
            self.db.add(connection)
            self.db.commit()
            self.db.refresh(connection)
            
            logger.info(f"创建Dify连接成功: {name}")
            return connection
            
        except Exception as e:
            logger.error(f"创建Dify连接失败: {e}")
            self.db.rollback()
            raise
    
    def get_connections(self) -> List[DifyConnection]:
        """获取所有Dify连接"""
        return self.db.query(DifyConnection).filter(DifyConnection.is_active == True).all()
    
    def get_default_connection(self) -> Optional[DifyConnection]:
        """获取默认Dify连接"""
        return self.db.query(DifyConnection).filter(
            and_(DifyConnection.is_active == True, DifyConnection.is_default == True)
        ).first()
    
    def get_connection_by_id(self, connection_id: str) -> Optional[DifyConnection]:
        """根据ID获取连接"""
        return self.db.query(DifyConnection).filter(
            and_(DifyConnection.id == connection_id, DifyConnection.is_active == True)
        ).first()
    
    async def test_connection(self, connection_id: str) -> Dict[str, Any]:
        """测试Dify连接"""
        connection = self.get_connection_by_id(connection_id)
        if not connection:
            return {"success": False, "message": "连接不存在"}
        
        client = DifyAPIClient(connection.api_base_url, connection.api_key)
        return await client.test_connection()
    
    async def sync_apps(self, connection_id: str) -> Dict[str, Any]:
        """同步Dify应用"""
        connection = self.get_connection_by_id(connection_id)
        if not connection:
            return {"success": False, "message": "连接不存在"}
        
        try:
            client = DifyAPIClient(connection.api_base_url, connection.api_key)
            apps = await client.get_apps()
            
            # 更新同步状态
            connection.last_sync_at = datetime.now()
            connection.sync_status = SyncStatus.SUCCESS
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"同步成功，发现 {len(apps)} 个应用",
                "apps": apps
            }
            
        except Exception as e:
            logger.error(f"同步Dify应用失败: {e}")
            connection.sync_status = SyncStatus.FAILED
            self.db.commit()
            return {"success": False, "message": f"同步失败: {str(e)}"}
    
    async def get_available_apps(self, connection_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取可用的Dify应用"""
        if not connection_id:
            connection = self.get_default_connection()
        else:
            connection = self.get_connection_by_id(connection_id)
        
        if not connection:
            return []
        
        client = DifyAPIClient(connection.api_base_url, connection.api_key)
        return await client.get_apps()
    
    def configure_app_to_agent_type(self, connection_id: str, app_id: str, app_name: str, 
                                   app_mode: str, agent_type: str, description: Optional[str] = None,
                                   is_default_for_type: bool = False) -> AIModelConfig:
        """将Dify应用配置为特定Agent类型"""
        try:
            connection = self.get_connection_by_id(connection_id)
            if not connection:
                raise ValueError("Dify连接不存在")
            
            # 验证agent_type是否有效
            try:
                agent_type_enum = AgentType(agent_type)
            except ValueError:
                raise ValueError(f"无效的Agent类型: {agent_type}")
            
            # 如果设为该类型默认，取消其他默认配置
            if is_default_for_type:
                self.db.query(AIModelConfig).filter(
                    and_(
                        AIModelConfig.agent_type == agent_type_enum,
                        AIModelConfig.is_default_for_type == True
                    )
                ).update({"is_default_for_type": False})
            
            # 检查是否已存在相同配置
            existing = self.db.query(AIModelConfig).filter(
                and_(
                    AIModelConfig.dify_connection_id == connection_id,
                    AIModelConfig.dify_app_id == app_id,
                    AIModelConfig.agent_type == agent_type_enum
                )
            ).first()
            
            if existing:
                # 更新现有配置
                existing.model_name = app_name
                existing.dify_app_name = app_name
                existing.dify_app_mode = app_mode
                existing.description = description
                existing.is_default_for_type = is_default_for_type
                existing.enabled = True
                
                self.db.commit()
                return existing
            else:
                # 创建新配置
                config = AIModelConfig(
                    model_name=app_name,
                    provider="dify",
                    dify_connection_id=connection_id,
                    dify_app_id=app_id,
                    dify_app_name=app_name,
                    dify_app_mode=app_mode,
                    agent_type=agent_type_enum,
                    description=description,
                    is_default_for_type=is_default_for_type,
                    enabled=True
                )
                
                self.db.add(config)
                self.db.commit()
                self.db.refresh(config)
                
                logger.info(f"配置Dify应用成功: {app_name} -> {agent_type}")
                return config
                
        except Exception as e:
            logger.error(f"配置Dify应用失败: {e}")
            self.db.rollback()
            raise
    
    def delete_connection(self, connection_id: str) -> bool:
        """删除Dify连接"""
        try:
            connection = self.get_connection_by_id(connection_id)
            if not connection:
                return False
            
            # 软删除：设置为非活跃状态
            connection.is_active = False
            self.db.commit()
            
            logger.info(f"删除Dify连接成功: {connection.name}")
            return True
            
        except Exception as e:
            logger.error(f"删除Dify连接失败: {e}")
            self.db.rollback()
            return False
    
    def set_default_connection(self, connection_id: str) -> bool:
        """设置默认连接"""
        try:
            # 取消所有默认连接
            self.db.query(DifyConnection).update({"is_default": False})
            
            # 设置新的默认连接
            connection = self.get_connection_by_id(connection_id)
            if not connection:
                return False
            
            connection.is_default = True
            self.db.commit()
            
            logger.info(f"设置默认Dify连接成功: {connection.name}")
            return True
            
        except Exception as e:
            logger.error(f"设置默认Dify连接失败: {e}")
            self.db.rollback()
            return False 