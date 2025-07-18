from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models.system import SystemSettings as ORMSystemSettings, AIModelConfig as ORMAIModelConfig
from app.schemas.system import (
    SystemSettingsUpdate, SystemSettings, SystemSettingsResponse, 
    AIModelConfigInfo, AIModelConfigListResponse, AIModelConfigCreate, AIModelConfigUpdate
)


def get_system_settings(db: Session) -> SystemSettingsResponse:
    """
    获取系统设置及所有AI模型配置
    :param db: 数据库会话
    :return: SystemSettingsResponse
    """
    orm_settings = db.query(ORMSystemSettings).first()
    if not orm_settings:
        raise RuntimeError("系统核心设置未找到或未正确初始化，请检查应用启动流程。")
    
    # 获取所有AI模型配置（不再通过system_settings_id关联）
    ai_models = db.query(ORMAIModelConfig).all()
    ai_model_schemas = [AIModelConfigInfo.from_model(m) for m in ai_models]
    
    settings_schema = SystemSettings(
        siteName=orm_settings.site_name,
        logoUrl=orm_settings.logo_url,
        aiModels=ai_model_schemas,
        defaultModelId=orm_settings.default_model_id,
        maintenanceMode=orm_settings.maintenance_mode,
        userRegistrationEnabled=orm_settings.user_registration_enabled
    )
    return SystemSettingsResponse(success=True, data=settings_schema, message="获取系统设置成功")


def update_system_settings(db: Session, settings_update: SystemSettingsUpdate) -> SystemSettingsResponse:
    """
    更新系统设置
    :param db: 数据库会话
    :param settings_update: 系统设置更新数据
    :return: SystemSettingsResponse
    """
    orm_settings = db.query(ORMSystemSettings).first()
    if not orm_settings:
        raise RuntimeError("系统核心设置未找到或未正确初始化，请检查应用启动流程。")
    
    update_data = settings_update.model_dump(exclude_unset=True)
    # 映射camelCase到snake_case字段名
    field_mapping = {
        'siteName': 'site_name',
        'logoUrl': 'logo_url',
        'defaultModelId': 'default_model_id',
        'maintenanceMode': 'maintenance_mode',
        'userRegistrationEnabled': 'user_registration_enabled'
    }
    
    for key, value in update_data.items():
        if value is not None:
            # 使用映射的字段名
            db_field = field_mapping.get(key, key)
            if isinstance(db_field, str) and hasattr(orm_settings, db_field):
                setattr(orm_settings, db_field, value)
    
    db.commit()
    db.refresh(orm_settings)
    return get_system_settings(db)


def get_ai_model_configs(db: Session) -> AIModelConfigListResponse:
    """
    获取所有AI模型配置列表
    :param db: 数据库会话
    :return: AIModelConfigListResponse
    """
    ai_models = db.query(ORMAIModelConfig).all()
    ai_model_schemas = [AIModelConfigInfo.from_model(m) for m in ai_models]
    return AIModelConfigListResponse(success=True, data=ai_model_schemas, message="获取AI模型配置成功")


def get_active_ai_configs(db: Session) -> List[Dict[str, Any]]:
    """
    获取所有启用的AI模型配置（用于AI服务内部调用）
    :param db: 数据库会话
    :return: List[Dict] - 启用的AI配置列表
    """
    ai_models = db.query(ORMAIModelConfig).filter(ORMAIModelConfig.enabled == True).all()
    
    return [
        {
            "id": model.id,
            "name": model.model_name,
            "provider": model.provider,
            "api_key": model.api_key,  # 内部调用，返回真实密钥
            "api_base_url": model.base_url,
            "model": model.model_name,
            "temperature": model.temperature,
            "max_tokens": model.max_tokens,

            "is_enabled": model.enabled
        }
        for model in ai_models
    ]


def get_default_ai_config(db: Session) -> Optional[Dict[str, Any]]:
    """
    获取默认AI配置（用于AI服务内部调用）
    :param db: 数据库会话
    :return: Dict - 默认AI配置
    """
    orm_settings = db.query(ORMSystemSettings).first()
    
    # 如果没有设置默认模型，返回第一个启用的模型
    if not orm_settings or not orm_settings.default_model_id:
        active_configs = get_active_ai_configs(db)
        return active_configs[0] if active_configs else None
    
    # 查找指定的默认模型
    default_model = db.query(ORMAIModelConfig).filter(
        ORMAIModelConfig.model_name == orm_settings.default_model_id,
        ORMAIModelConfig.enabled == True
    ).first()
    
    if not default_model:
        # 如果默认模型不存在或未启用，返回第一个启用的模型
        active_configs = get_active_ai_configs(db)
        return active_configs[0] if active_configs else None
    
    return {
        "id": default_model.id,
        "name": default_model.model_name,
        "provider": default_model.provider,
        "api_key": default_model.api_key,
        "api_base_url": default_model.base_url,
        "model": default_model.model_name,
        "temperature": default_model.temperature,
        "max_tokens": default_model.max_tokens,

        "is_enabled": default_model.enabled
    } 


def create_ai_model_config(db: Session, model_create: AIModelConfigCreate) -> AIModelConfigInfo:
    """
    创建AI模型配置
    :param db: 数据库会话
    :param model_create: AI模型配置创建数据
    :return: AIModelConfigInfo
    """
    # 检查模型名称是否已存在
    existing_model = db.query(ORMAIModelConfig).filter(ORMAIModelConfig.model_name == model_create.modelName).first()
    if existing_model:
        raise ValueError(f"模型名称 '{model_create.modelName}' 已存在")
    
    # 创建新的AI模型配置
    new_model = ORMAIModelConfig(
        model_name=model_create.modelName,
        provider=model_create.provider,
        api_key=model_create.apiKey,
        base_url=model_create.baseUrl,
        max_tokens=model_create.maxTokens,
        temperature=model_create.temperature,
        enabled=model_create.enabled,
        description=model_create.description
    )
    
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    
    return AIModelConfigInfo.from_model(new_model)


def update_ai_model_config(db: Session, model_name: str, model_update: AIModelConfigUpdate) -> Optional[AIModelConfigInfo]:
    """
    更新AI模型配置
    :param db: 数据库会话
    :param model_name: 模型名称
    :param model_update: AI模型配置更新数据
    :return: AIModelConfigInfo or None
    """
    # 查找要更新的模型
    model = db.query(ORMAIModelConfig).filter(ORMAIModelConfig.model_name == model_name).first()
    if not model:
        return None
    
    # 更新字段
    update_data = model_update.model_dump(exclude_unset=True)
    
    # 映射camelCase到snake_case字段名
    field_mapping = {
        'modelName': 'model_name',
        'apiKey': 'api_key',
        'baseUrl': 'base_url',
        'maxTokens': 'max_tokens'
    }
    
    for key, value in update_data.items():
        if value is not None:
            # 使用映射的字段名
            db_field = field_mapping.get(key, key)
            if hasattr(model, db_field):
                setattr(model, db_field, value)
    
    db.commit()
    db.refresh(model)
    
    return AIModelConfigInfo.from_model(model)


def delete_ai_model_config(db: Session, model_name: str) -> bool:
    """
    删除AI模型配置
    :param db: 数据库会话
    :param model_name: 模型名称
    :return: bool - 是否成功删除
    """
    model = db.query(ORMAIModelConfig).filter(ORMAIModelConfig.model_name == model_name).first()
    if not model:
        return False
    
    db.delete(model)
    db.commit()
    
    return True


def toggle_ai_model_status(db: Session, model_name: str) -> Optional[AIModelConfigInfo]:
    """
    切换AI模型启用状态
    :param db: 数据库会话
    :param model_name: 模型名称
    :return: AIModelConfigInfo or None
    """
    model = db.query(ORMAIModelConfig).filter(ORMAIModelConfig.model_name == model_name).first()
    if not model:
        return None
    
    model.enabled = not model.enabled
    db.commit()
    db.refresh(model)
    
    return AIModelConfigInfo.from_model(model) 