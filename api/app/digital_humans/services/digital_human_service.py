"""
数字人服务 - 处理数字人相关的业务逻辑
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from app.ai.models.agent_config import AgentConfig
from app.identity_access.models.user import User

from ..models.digital_human import (
    DigitalHuman, 
    DigitalHumanAgentConfig, 
)
from app.common.deps.uuid_utils import digital_human_id
from ..schemas.digital_human import (
    CreateDigitalHumanRequest,
    AdminCreateDigitalHumanRequest,
    UpdateDigitalHumanRequest,
    AdminUpdateDigitalHumanRequest,
    DigitalHumanResponse,
    AddAgentConfigRequest,
    DigitalHumanAgentConfigInfo,
    AgentConfigInfo,
    UpdateAgentConfigRequest,
)

logger = logging.getLogger(__name__)


class DigitalHumanService:
    """数字人服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_digital_humans(self, user_id: str) -> List[DigitalHumanResponse]:
        """获取用户的数字人列表"""
        try:
            digital_humans = (
                self.db.query(DigitalHuman)
                .filter(or_(DigitalHuman.user_id == user_id, DigitalHuman.user_id.is_(None)))
                .order_by(DigitalHuman.created_at.desc())
                .all()
            )
            
            return [DigitalHumanResponse.from_model(dh) for dh in digital_humans]
            
        except Exception as e:
            logger.error(f"获取用户数字人列表失败: {e}")
            raise
    
    def get_all_digital_humans(self, 
                              status: Optional[str] = None,
                              type: Optional[str] = None,
                              user_id: Optional[str] = None,
                              is_system_created: Optional[bool] = None,
                              search: Optional[str] = None) -> List[DigitalHumanResponse]:
        """获取所有数字人列表（管理员用）"""
        try:
            query = self.db.query(DigitalHuman)
            
            # 应用筛选条件
            if status:
                query = query.filter(DigitalHuman.status == status)
            
            if type:
                query = query.filter(DigitalHuman.type == type)
            
            if user_id:
                query = query.filter(DigitalHuman.user_id == user_id)
            
            if is_system_created is not None:
                query = query.filter(DigitalHuman.is_system_created == is_system_created)
            
            if search:
                query = query.filter(
                    or_(
                        DigitalHuman.name.contains(search),
                        DigitalHuman.description.contains(search)
                    )
                )
            
            digital_humans = query.order_by(DigitalHuman.created_at.desc()).all()
            
            return [DigitalHumanResponse.from_model(dh) for dh in digital_humans]
            
        except Exception as e:
            logger.error(f"获取所有数字人列表失败: {e}")
            raise
    
    def get_digital_human_by_id(self, digital_human_id: str, user_id: Optional[str] = None) -> Optional[DigitalHumanResponse]:
        """根据ID获取数字人详情"""
        try:
            query = self.db.query(DigitalHuman).filter(DigitalHuman.id == digital_human_id)
            
            # 如果指定了用户ID，则只能获取该用户的数字人
            if user_id:
                query = query.filter(or_(DigitalHuman.user_id == user_id, DigitalHuman.user_id.is_(None)))
            
            digital_human = query.first()
            
            if not digital_human:
                return None
            
            return DigitalHumanResponse.from_model(digital_human)
            
        except Exception as e:
            logger.error(f"获取数字人详情失败: {e}")
            raise
    
    def create_digital_human(self, user_id: str, data: CreateDigitalHumanRequest) -> DigitalHumanResponse:
        """创建数字人"""
        try:
            # 创建数字人实例
            digital_human = DigitalHuman(
                id=digital_human_id(),
                name=data.name,
                avatar=data.avatar,
                description=data.description,
                type=data.type,
                status=data.status,
                is_system_created=False,  # 用户创建的数字人
                personality=data.personality,
                greeting_message=data.greeting_message,
                welcome_message=data.welcome_message,
                user_id=user_id,
            )
            
            self.db.add(digital_human)
            self.db.commit()
            self.db.refresh(digital_human)
            
            logger.info(f"用户 {user_id} 创建数字人成功: {digital_human.name}")
            return DigitalHumanResponse.from_model(digital_human)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建数字人失败: {e}")
            raise

    def create_digital_human_admin(self, data: AdminCreateDigitalHumanRequest) -> DigitalHumanResponse:
        """管理员创建数字人（可指定所属用户，支持创建系统助手类型）"""
        try:
            if data.user_id:
                user = self.db.query(User).filter(User.id == data.user_id).first()
                if not user:
                    raise ValueError("所属用户不存在")

            is_system_created = True if data.type == "system" else False

            digital_human = DigitalHuman(
                id=digital_human_id(),
                name=data.name,
                avatar=data.avatar,
                description=data.description,
                type=data.type,
                status=data.status,
                is_system_created=is_system_created,
                personality=data.personality,
                greeting_message=data.greeting_message,
                welcome_message=data.welcome_message,
                user_id=data.user_id,
            )

            self.db.add(digital_human)
            self.db.commit()
            self.db.refresh(digital_human)

            logger.info(
                f"管理员创建数字人成功: name={digital_human.name}, user_id={digital_human.user_id}, "
                f"type={digital_human.type}, is_system_created={digital_human.is_system_created}"
            )
            return DigitalHumanResponse.from_model(digital_human)
        except Exception as e:
            self.db.rollback()
            logger.error(f"管理员创建数字人失败: {e}")
            raise
    
    def update_digital_human(self, digital_human_id: str, user_id: str, data: UpdateDigitalHumanRequest) -> Optional[DigitalHumanResponse]:
        """更新数字人信息"""
        try:
            digital_human = (
                self.db.query(DigitalHuman)
                .filter(and_(
                    DigitalHuman.id == digital_human_id,
                    DigitalHuman.user_id == user_id
                ))
                .first()
            )
            
            if not digital_human:
                return None
            
            # 更新字段
            update_data = data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(digital_human, field):
                    setattr(digital_human, field, value)
            
            digital_human.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(digital_human)
            
            logger.info(f"更新数字人成功: {digital_human.name}")
            return DigitalHumanResponse.from_model(digital_human)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新数字人失败: {e}")
            raise

    def update_digital_human_admin(
        self, digital_human_id: str, data: AdminUpdateDigitalHumanRequest
    ) -> Optional[DigitalHumanResponse]:
        """管理员更新数字人信息（可调整所属用户）"""
        try:
            digital_human = self.db.query(DigitalHuman).filter(DigitalHuman.id == digital_human_id).first()
            if not digital_human:
                return None

            update_data = data.dict(exclude_unset=True)

            # 调整所属用户
            if "user_id" in update_data:
                new_user_id = update_data["user_id"]
                if new_user_id:
                    user = self.db.query(User).filter(User.id == new_user_id).first()
                    if not user:
                        raise ValueError("所属用户不存在")
                    digital_human.user_id = new_user_id
                else:
                    digital_human.user_id = None

            # 更新其他字段（不允许在此接口修改 type / is_system_created）
            for field in ("name", "avatar", "description", "status", "personality", "greeting_message", "welcome_message"):
                if field in update_data:
                    setattr(digital_human, field, update_data[field])

            digital_human.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(digital_human)

            logger.info(f"管理员更新数字人成功: id={digital_human.id}, name={digital_human.name}")
            return DigitalHumanResponse.from_model(digital_human)
        except Exception as e:
            self.db.rollback()
            logger.error(f"管理员更新数字人失败: {e}")
            raise
    
    def delete_digital_human(self, digital_human_id: str, user_id: str) -> bool:
        """删除数字人（系统创建的不可删除）"""
        try:
            digital_human = (
                self.db.query(DigitalHuman)
                .filter(and_(
                    DigitalHuman.id == digital_human_id,
                    DigitalHuman.user_id == user_id,
                    DigitalHuman.is_system_created == False  # 只能删除非系统创建的
                ))
                .first()
            )
            
            if not digital_human:
                return False
            
            self.db.delete(digital_human)
            self.db.commit()
            
            logger.info(f"删除数字人成功: {digital_human.name}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除数字人失败: {e}")
            raise

    def delete_digital_human_admin(self, digital_human_id: str) -> bool:
        """管理员删除数字人（允许删除系统创建的数字人）"""
        try:
            digital_human = self.db.query(DigitalHuman).filter(DigitalHuman.id == digital_human_id).first()
            if not digital_human:
                return False

            self.db.delete(digital_human)
            self.db.commit()
            logger.info(f"管理员删除数字人成功: id={digital_human_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"管理员删除数字人失败: {e}")
            raise
    
    def update_digital_human_status(self, digital_human_id: str, new_status: str) -> Optional[DigitalHumanResponse]:
        """更新数字人状态（管理员功能）"""
        try:
            digital_human = self.db.query(DigitalHuman).filter(DigitalHuman.id == digital_human_id).first()
            
            if not digital_human:
                return None
            
            digital_human.status = new_status
            digital_human.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(digital_human)
            
            logger.info(f"管理员更新数字人状态: {digital_human.name} -> {new_status}")
            return DigitalHumanResponse.from_model(digital_human)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新数字人状态失败: {e}")
            raise
    
    def get_digital_human_agents(self, digital_human_id: str, user_id: Optional[str] = None) -> List[DigitalHumanAgentConfigInfo]:
        """获取数字人的智能体配置列表"""
        try:
            query = self.db.query(DigitalHumanAgentConfig).filter(
                DigitalHumanAgentConfig.digital_human_id == digital_human_id
            )
            
            # 如果指定了用户ID，验证权限
            if user_id:
                query = query.join(DigitalHuman).filter(DigitalHuman.user_id == user_id)
            
            agent_configs = query.order_by(DigitalHumanAgentConfig.priority).all()
            
            return [
                DigitalHumanAgentConfigInfo(
                    id=config.id,
                    priority=config.priority,
                    is_active=config.is_active,
                    scenarios=config.scenarios,
                    context_prompt=config.context_prompt,
                    agent_config=AgentConfigInfo(
                        id=config.agent_config.id,
                        app_name=config.agent_config.app_name,
                        app_id=config.agent_config.app_id,
                        environment=config.agent_config.environment,
                        description=config.agent_config.description,
                        enabled=config.agent_config.enabled,
                        agent_type=config.agent_config.agent_type,
                        capabilities=config.agent_config.capabilities
                    )
                ) for config in agent_configs
            ]
            
        except Exception as e:
            logger.error(f"获取数字人智能体配置失败: {e}")
            raise
    
    def add_agent_to_digital_human(self, digital_human_id: str, user_id: str, data: AddAgentConfigRequest) -> DigitalHumanAgentConfigInfo:
        """为数字人添加智能体配置"""
        try:
            # 验证数字人所有权
            digital_human = (
                self.db.query(DigitalHuman)
                .filter(and_(
                    DigitalHuman.id == digital_human_id,
                    DigitalHuman.user_id == user_id
                ))
                .first()
            )
            
            if not digital_human:
                raise ValueError("数字人不存在或无权限")
            
            # 验证智能体配置存在
            agent_config = self.db.query(AgentConfig).filter(AgentConfig.id == data.agent_config_id).first()
            if not agent_config:
                raise ValueError("智能体配置不存在")
            
            # 检查是否已经配置
            existing = (
                self.db.query(DigitalHumanAgentConfig)
                .filter(and_(
                    DigitalHumanAgentConfig.digital_human_id == digital_human_id,
                    DigitalHumanAgentConfig.agent_config_id == data.agent_config_id
                ))
                .first()
            )
            
            if existing:
                raise ValueError("该智能体已经配置过了")
            
            # 创建关联配置
            dh_agent_config = DigitalHumanAgentConfig(
                digital_human_id=digital_human_id,
                agent_config_id=data.agent_config_id,
                priority=data.priority,
                is_active=data.is_active,
                scenarios=data.scenarios,
                context_prompt=data.context_prompt
            )
            
            self.db.add(dh_agent_config)
            self.db.commit()
            self.db.refresh(dh_agent_config)
            
            logger.info(f"为数字人 {digital_human.name} 添加智能体配置: {agent_config.app_name}")
            
            return DigitalHumanAgentConfigInfo(
                id=dh_agent_config.id,
                priority=dh_agent_config.priority,
                is_active=dh_agent_config.is_active,
                scenarios=dh_agent_config.scenarios,
                context_prompt=dh_agent_config.context_prompt,
                agent_config=AgentConfigInfo(
                    id=agent_config.id,
                    app_name=agent_config.app_name,
                    app_id=agent_config.app_id,
                    environment=agent_config.environment,
                    description=agent_config.description,
                    enabled=agent_config.enabled,
                    agent_type=agent_config.agent_type,
                    capabilities=agent_config.capabilities
                )
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"添加智能体配置失败: {e}")
            raise
    
    def remove_agent_from_digital_human(self, digital_human_id: str, config_id: str, user_id: str) -> bool:
        """从数字人移除智能体配置"""
        try:
            # 验证权限并删除
            config = (
                self.db.query(DigitalHumanAgentConfig)
                .join(DigitalHuman)
                .filter(and_(
                    DigitalHumanAgentConfig.id == config_id,
                    DigitalHumanAgentConfig.digital_human_id == digital_human_id,
                    DigitalHuman.user_id == user_id
                ))
                .first()
            )
            
            if not config:
                return False
            
            self.db.delete(config)
            self.db.commit()
            
            logger.info(f"从数字人移除智能体配置: {config_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"移除智能体配置失败: {e}")
            raise
    
    def update_digital_human_agent(
        self,
        digital_human_id: str,
        config_id: str,
        user_id: str,
        data: UpdateAgentConfigRequest,
    ) -> Optional[DigitalHumanAgentConfigInfo]:
        """更新数字人的智能体配置"""
        try:
            config = (
                self.db.query(DigitalHumanAgentConfig)
                .join(DigitalHuman)
                .filter(
                    and_(
                        DigitalHumanAgentConfig.id == config_id,
                        DigitalHumanAgentConfig.digital_human_id == digital_human_id,
                        DigitalHuman.user_id == user_id,
                    )
                )
                .first()
            )

            if not config:
                return None

            update_data = data.model_dump(exclude_unset=True)

            if "priority" in update_data:
                config.priority = update_data["priority"]
            if "is_active" in update_data:
                config.is_active = update_data["is_active"]
            if "scenarios" in update_data:
                config.scenarios = update_data["scenarios"]
            if "context_prompt" in update_data:
                config.context_prompt = update_data["context_prompt"]

            self.db.commit()
            self.db.refresh(config)

            agent_config = config.agent_config

            return DigitalHumanAgentConfigInfo(
                id=config.id,
                priority=config.priority,
                is_active=config.is_active,
                scenarios=config.scenarios,
                context_prompt=config.context_prompt,
                agent_config=AgentConfigInfo(
                    id=agent_config.id,
                    app_name=agent_config.app_name,
                    app_id=agent_config.app_id,
                    environment=agent_config.environment,
                    description=agent_config.description,
                    enabled=agent_config.enabled,
                    agent_type=agent_config.agent_type,
                    capabilities=agent_config.capabilities,
                ),
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新数字人智能体配置失败: {e}")
            raise

    # -------------------------
    # 管理员专用：数字人智能体配置（不做所属用户校验）
    # -------------------------

    def add_agent_to_digital_human_admin(
        self, digital_human_id: str, data: AddAgentConfigRequest
    ) -> DigitalHumanAgentConfigInfo:
        """管理员为数字人添加智能体配置（不校验归属用户）"""
        try:
            digital_human = self.db.query(DigitalHuman).filter(DigitalHuman.id == digital_human_id).first()
            if not digital_human:
                raise ValueError("数字人不存在")

            agent_config = self.db.query(AgentConfig).filter(AgentConfig.id == data.agent_config_id).first()
            if not agent_config:
                raise ValueError("智能体配置不存在")

            existing = (
                self.db.query(DigitalHumanAgentConfig)
                .filter(
                    and_(
                        DigitalHumanAgentConfig.digital_human_id == digital_human_id,
                        DigitalHumanAgentConfig.agent_config_id == data.agent_config_id,
                    )
                )
                .first()
            )
            if existing:
                raise ValueError("该智能体已经配置过了")

            dh_agent_config = DigitalHumanAgentConfig(
                digital_human_id=digital_human_id,
                agent_config_id=data.agent_config_id,
                priority=data.priority,
                is_active=data.is_active,
                scenarios=data.scenarios,
                context_prompt=data.context_prompt,
            )

            self.db.add(dh_agent_config)
            self.db.commit()
            self.db.refresh(dh_agent_config)

            return DigitalHumanAgentConfigInfo(
                id=dh_agent_config.id,
                priority=dh_agent_config.priority,
                is_active=dh_agent_config.is_active,
                scenarios=dh_agent_config.scenarios,
                context_prompt=dh_agent_config.context_prompt,
                agent_config=AgentConfigInfo(
                    id=agent_config.id,
                    app_name=agent_config.app_name,
                    app_id=agent_config.app_id,
                    environment=agent_config.environment,
                    description=agent_config.description,
                    enabled=agent_config.enabled,
                    agent_type=agent_config.agent_type,
                    capabilities=agent_config.capabilities,
                ),
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"管理员添加智能体配置失败: {e}")
            raise

    def remove_agent_from_digital_human_admin(self, digital_human_id: str, config_id: str) -> bool:
        """管理员从数字人移除智能体配置（不校验归属用户）"""
        try:
            config = (
                self.db.query(DigitalHumanAgentConfig)
                .filter(
                    and_(
                        DigitalHumanAgentConfig.id == config_id,
                        DigitalHumanAgentConfig.digital_human_id == digital_human_id,
                    )
                )
                .first()
            )
            if not config:
                return False

            self.db.delete(config)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"管理员移除智能体配置失败: {e}")
            raise

    def update_digital_human_agent_admin(
        self,
        digital_human_id: str,
        config_id: str,
        data: UpdateAgentConfigRequest,
    ) -> Optional[DigitalHumanAgentConfigInfo]:
        """管理员更新数字人的智能体配置（不校验归属用户）"""
        try:
            config = (
                self.db.query(DigitalHumanAgentConfig)
                .filter(
                    and_(
                        DigitalHumanAgentConfig.id == config_id,
                        DigitalHumanAgentConfig.digital_human_id == digital_human_id,
                    )
                )
                .first()
            )
            if not config:
                return None

            update_data = data.model_dump(exclude_unset=True)
            if "priority" in update_data:
                config.priority = update_data["priority"]
            if "is_active" in update_data:
                config.is_active = update_data["is_active"]
            if "scenarios" in update_data:
                config.scenarios = update_data["scenarios"]
            if "context_prompt" in update_data:
                config.context_prompt = update_data["context_prompt"]

            self.db.commit()
            self.db.refresh(config)

            agent_config = config.agent_config

            return DigitalHumanAgentConfigInfo(
                id=config.id,
                priority=config.priority,
                is_active=config.is_active,
                scenarios=config.scenarios,
                context_prompt=config.context_prompt,
                agent_config=AgentConfigInfo(
                    id=agent_config.id,
                    app_name=agent_config.app_name,
                    app_id=agent_config.app_id,
                    environment=agent_config.environment,
                    description=agent_config.description,
                    enabled=agent_config.enabled,
                    agent_type=agent_config.agent_type,
                    capabilities=agent_config.capabilities,
                ),
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"管理员更新数字人智能体配置失败: {e}")
            raise
    
    def create_system_digital_human(self, user_id: str, username: str) -> DigitalHumanResponse:
        """为新注册用户创建系统默认数字人"""
        try:
            # 检查是否已有系统数字人
            existing = (
                self.db.query(DigitalHuman)
                .filter(and_(
                    DigitalHuman.user_id == user_id,
                    DigitalHuman.is_system_created == True
                ))
                .first()
            )
            
            if existing:
                return DigitalHumanResponse.from_model(existing)
            
            # 创建系统数字人
            digital_human = DigitalHuman(
                id=digital_human_id(),
                name=f'{username}的智能助手',
                description=f'为{username}自动创建的专属数字助手，提供个性化服务',
                type='system',
                status='active',
                is_system_created=True,
                personality={
                    'tone': 'friendly',
                    'style': 'professional',
                    'specialization': 'medical_beauty'
                },
                greeting_message=f'您好{username}！我是您的专属数字助手，很高兴为您服务！有什么可以帮助您的吗？',
                welcome_message=f'欢迎{username}！我会为您提供专业的咨询服务，请随时告诉我您的需求。',
                user_id=user_id,
            )
            
            self.db.add(digital_human)
            self.db.flush()  # 获取ID
            
            # 为数字人配置默认智能体
            default_agent = (
                self.db.query(AgentConfig)
                .filter(and_(
                    AgentConfig.app_id == 'medical_beauty_consultant',
                    AgentConfig.enabled == True
                ))
                .first()
            )
            
            if default_agent:
                dh_agent_config = DigitalHumanAgentConfig(
                    digital_human_id=digital_human.id,
                    agent_config_id=default_agent.id,
                    priority=1,
                    is_active=True,
                    scenarios=['greeting', 'general_qa'],
                    context_prompt=f'你是{username}的专属数字助手，请提供专业、友好的咨询服务。'
                )
                self.db.add(dh_agent_config)
            
            self.db.commit()
            self.db.refresh(digital_human)
            
            logger.info(f"为用户 {username} 创建系统数字人: {digital_human.name}")
            return DigitalHumanResponse.from_model(digital_human)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建系统数字人失败: {e}")
            raise
