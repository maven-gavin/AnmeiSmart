#!/usr/bin/env python3
"""
数字人系统初始化脚本
为现有用户创建默认数字人，并创建基础的智能体配置
"""

import sys
import os
import asyncio
from datetime import datetime
import uuid

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.core.config import Settings
from app.identity_access.models.user import User
from app.digital_humans.models.digital_human import DigitalHuman
from app.ai.infrastructure.db.agent_config import AgentConfig
from app.common.deps.uuid_utils import digital_human_id, generate_agent_id


def create_default_agent_configs(session):
    """创建默认的智能体配置"""
    print("Creating default agent configurations...")
    
    default_agents = [
        {
            'id': generate_agent_id(),
            'environment': 'production',
            'app_id': 'medical_beauty_consultant',
            'app_name': '咨询助手',
            'api_key': 'default_encrypted_key_1',  # 需要实际的加密密钥
            'base_url': 'http://localhost:5001/v1',
            'timeout_seconds': 30,
            'max_retries': 3,
            'enabled': True,
            'description': '专业的咨询智能助手，提供个性化咨询服务',

        },
        {
            'id': generate_agent_id(),
            'environment': 'production',
            'app_id': 'prescription_safety_checker',
            'app_name': '处方安全检查助手',
            'api_key': 'default_encrypted_key_2',
            'base_url': 'http://localhost:5001/v1',
            'timeout_seconds': 30,
            'max_retries': 3,
            'enabled': True,
            'description': '医生专用的处方安全检查智能助手',

        },
        {
            'id': generate_agent_id(),
            'environment': 'production',
            'app_id': 'customer_service_bot',
            'app_name': '客服助手',
            'api_key': 'default_encrypted_key_3',
            'base_url': 'http://localhost:5001/v1',
            'timeout_seconds': 30,
            'max_retries': 3,
            'enabled': True,
            'description': '通用客户服务智能助手',

        }
    ]
    
    created_agents = []
    for agent_data in default_agents:
        # 检查是否已存在
        existing = session.query(AgentConfig).filter_by(app_id=agent_data['app_id']).first()
        if not existing:
            agent = AgentConfig(**agent_data)
            session.add(agent)
            created_agents.append(agent)
            print(f"  Created agent: {agent_data['app_name']}")
        else:
            print(f"  Agent already exists: {agent_data['app_name']}")
            created_agents.append(existing)
    
    session.commit()
    return created_agents


def create_digital_humans_for_users(session, default_agent):
    """为现有用户创建默认数字人"""
    print("Creating digital humans for existing users...")
    
    # 获取所有活跃用户
    users = session.query(User).filter_by(is_active=True).all()
    
    created_count = 0
    for user in users:
        # 检查用户是否已有数字人
        existing_dh = session.query(DigitalHuman).filter_by(user_id=user.id).first()
        if existing_dh:
            print(f"  User {user.username} already has digital human: {existing_dh.name}")
            continue
        
        # 创建默认数字人
        digital_human = DigitalHuman(
            id=digital_human_id(),
            name=f'{user.username}的智能助手',
            description=f'为{user.username}自动创建的专属数字助手，提供个性化服务',
            type='system',
            status='active',
            is_system_created=True,
            personality={
                'tone': 'friendly',
                'style': 'professional',
                'specialization': 'medical_beauty'
            },
            greeting_message=f'您好{user.username}！我是您的专属数字助手，很高兴为您服务！有什么可以帮助您的吗？',
            welcome_message=f'欢迎{user.username}！我会为您提供专业的咨询服务，请随时告诉我您的需求。',
            user_id=user.id,
            conversation_count=0,
            message_count=0
        )
        
        session.add(digital_human)
        session.flush()  # 获取数字人ID
        
        # 为数字人配置默认智能体
        if default_agent:
            agent_config = DigitalHumanAgentConfig(
                digital_human_id=digital_human.id,
                agent_config_id=default_agent.id,
                priority=1,
                is_active=True,
                scenarios=['consultation', 'greeting', 'general_qa'],
                context_prompt=f'你是{user.username}的专属数字助手，请提供专业、友好的咨询服务。'
            )
            session.add(agent_config)
        
        created_count += 1
        print(f"  Created digital human for user: {user.username}")
    
    session.commit()
    print(f"Created {created_count} digital humans")


def main():
    """主函数"""
    print("Initializing Digital Human System...")
    print("=" * 50)
    
    # 创建数据库连接
    settings = Settings()
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = SessionLocal()
    
    try:
        # 1. 创建默认智能体配置
        default_agents = create_default_agent_configs(session)
        
        # 2. 为现有用户创建数字人
        default_agent = default_agents[0] if default_agents else None
        create_digital_humans_for_users(session, default_agent)
        
        print("=" * 50)
        print("Digital Human System initialization completed successfully!")
        
        # 输出统计信息
        total_users = session.query(User).filter_by(is_active=True).count()
        total_digital_humans = session.query(DigitalHuman).count()
        total_agents = session.query(AgentConfig).count()
        
        print(f"Statistics:")
        print(f"  - Total active users: {total_users}")
        print(f"  - Total digital humans: {total_digital_humans}")
        print(f"  - Total agent configs: {total_agents}")
        
    except Exception as e:
        print(f"Error during initialization: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
