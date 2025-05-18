from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from app.db.models.system import SystemSettings, AIModelConfig
from app.schemas.system import SystemSettingsUpdate, AIModelConfigCreate, AIModelConfigUpdate


def get_system_settings(db: Session) -> Optional[SystemSettings]:
    """获取系统设置"""
    return db.query(SystemSettings).first()


def create_system_settings(db: Session) -> SystemSettings:
    """创建默认系统设置"""
    db_system_settings = SystemSettings(
        siteName="安美智能咨询系统",
        logoUrl="/logo.png",
        themeColor="#FF6B00",
        defaultModelId="GPT-4",
        maintenanceMode=False,
        userRegistrationEnabled=True
    )
    db.add(db_system_settings)
    db.commit()
    db.refresh(db_system_settings)
    
    # 添加默认AI模型配置
    default_model = AIModelConfig(
        modelName="GPT-4",
        apiKey="sk-••••••••••••••••••••••••",  # 实际部署时应使用环境变量或安全存储
        baseUrl="https://api.openai.com/v1",
        maxTokens=2000,
        temperature=0.7,
        enabled=True,
        system_settings_id=db_system_settings.id
    )
    db.add(default_model)
    db.commit()
    
    return db_system_settings


def get_or_create_system_settings(db: Session) -> SystemSettings:
    """获取或创建系统设置"""
    system_settings = get_system_settings(db)
    if not system_settings:
        system_settings = create_system_settings(db)
    return system_settings


def update_system_settings(
    db: Session, 
    settings_update: SystemSettingsUpdate
) -> SystemSettings:
    """更新系统设置"""
    system_settings = get_or_create_system_settings(db)
    
    # 更新非空字段
    update_data = settings_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:  # 只更新非None值
            setattr(system_settings, key, value)
    
    db.commit()
    db.refresh(system_settings)
    return system_settings


def get_ai_model_configs(db: Session) -> List[AIModelConfig]:
    """获取所有AI模型配置"""
    system_settings = get_or_create_system_settings(db)
    return db.query(AIModelConfig).filter(
        AIModelConfig.system_settings_id == system_settings.id
    ).all()


def get_ai_model_config_by_name(db: Session, model_name: str) -> Optional[AIModelConfig]:
    """根据模型名称获取AI模型配置"""
    system_settings = get_or_create_system_settings(db)
    return db.query(AIModelConfig).filter(
        AIModelConfig.system_settings_id == system_settings.id,
        AIModelConfig.modelName == model_name
    ).first()


def create_ai_model_config(
    db: Session, 
    model_config: AIModelConfigCreate
) -> AIModelConfig:
    """创建AI模型配置"""
    system_settings = get_or_create_system_settings(db)
    
    # 检查是否已存在同名模型
    existing_model = get_ai_model_config_by_name(db, model_config.modelName)
    if existing_model:
        raise ValueError(f"模型名称 '{model_config.modelName}' 已存在")
    
    db_model_config = AIModelConfig(
        **model_config.model_dump(),
        system_settings_id=system_settings.id
    )
    db.add(db_model_config)
    db.commit()
    db.refresh(db_model_config)
    return db_model_config


def update_ai_model_config(
    db: Session, 
    model_name: str, 
    model_update: AIModelConfigUpdate
) -> Optional[AIModelConfig]:
    """更新AI模型配置"""
    db_model = get_ai_model_config_by_name(db, model_name)
    if not db_model:
        return None
    
    # 更新非空字段
    update_data = model_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:  # 只更新非None值
            setattr(db_model, key, value)
    
    db.commit()
    db.refresh(db_model)
    return db_model


def delete_ai_model_config(db: Session, model_name: str) -> bool:
    """删除AI模型配置"""
    db_model = get_ai_model_config_by_name(db, model_name)
    if not db_model:
        return False
    
    db.delete(db_model)
    db.commit()
    return True


def toggle_ai_model_status(db: Session, model_name: str) -> Optional[AIModelConfig]:
    """切换AI模型启用状态"""
    db_model = get_ai_model_config_by_name(db, model_name)
    if not db_model:
        return None
    
    db_model.enabled = not db_model.enabled
    db.commit()
    db.refresh(db_model)
    return db_model 