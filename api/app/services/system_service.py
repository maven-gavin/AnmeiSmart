from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from app.db.models.system import SystemSettings as ORMSystemSettings, AIModelConfig as ORMAIModelConfig
from app.schemas.system import SystemSettingsUpdate, AIModelConfigCreate, AIModelConfigUpdate, SystemSettings, SystemSettingsResponse, AIModelConfigInfo, AIModelConfigResponse, AIModelConfigListResponse


def get_system_settings(db: Session) -> SystemSettingsResponse:
    """
    获取系统设置及所有AI模型配置
    :param db: 数据库会话
    :return: SystemSettingsResponse
    """
    orm_settings = db.query(ORMSystemSettings).first()
    if not orm_settings:
        raise RuntimeError("系统核心设置未找到或未正确初始化，请检查应用启动流程。")
    ai_models = db.query(ORMAIModelConfig).filter(ORMAIModelConfig.system_settings_id == orm_settings.id).all()
    ai_model_schemas = [AIModelConfigInfo(
        modelName=m.modelName,
        apiKey="••••••••••••••••••••",
        baseUrl=m.baseUrl,
        maxTokens=m.maxTokens,
        temperature=m.temperature,
        enabled=m.enabled,
        provider=m.provider,
        appId=m.appId
    ) for m in ai_models]
    settings_schema = SystemSettings(
        siteName=orm_settings.siteName,
        logoUrl=orm_settings.logoUrl,
        aiModels=ai_model_schemas,
        defaultModelId=orm_settings.defaultModelId,
        maintenanceMode=orm_settings.maintenanceMode,
        userRegistrationEnabled=orm_settings.userRegistrationEnabled
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
    for key, value in update_data.items():
        if value is not None:
            setattr(orm_settings, key, value)
    db.commit()
    db.refresh(orm_settings)
    return get_system_settings(db)

def create_ai_model_config(db: Session, model_create: AIModelConfigCreate) -> AIModelConfigInfo:
    """
    创建AI模型配置
    :param db: 数据库会话
    :param model_create: AI模型配置创建数据
    :return: AIModelConfig
    """
    orm_settings = db.query(ORMSystemSettings).first()
    if not orm_settings:
        raise RuntimeError("系统核心设置未找到或未正确初始化，请检查应用启动流程。")
    
    # Check for existing model with the same name for these settings
    existing_model = db.query(ORMAIModelConfig).filter(
        ORMAIModelConfig.system_settings_id == orm_settings.id,
        ORMAIModelConfig.modelName == model_create.modelName
    ).first()
    if existing_model:
        raise ValueError(f"名为 '{model_create.modelName}' 的AI模型配置已存在")
        
    db_model = ORMAIModelConfig(
        system_settings_id=orm_settings.id,
        modelName=model_create.modelName,
        apiKey=model_create.apiKey,
        baseUrl=model_create.baseUrl,
        maxTokens=model_create.maxTokens,
        temperature=model_create.temperature,
        enabled=model_create.enabled,
        provider=model_create.provider,
        appId=model_create.appId
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return AIModelConfigInfo(
        modelName=db_model.modelName,
        apiKey="••••••••••••••••••••",
        baseUrl=db_model.baseUrl,
        maxTokens=db_model.maxTokens,
        temperature=db_model.temperature,
        enabled=db_model.enabled,
        provider=db_model.provider,
        appId=db_model.appId
    )

def update_ai_model_config(db: Session, model_name: str, model_update: AIModelConfigUpdate) -> Optional[AIModelConfigInfo]:
    """
    更新AI模型配置
    :param db: 数据库会话
    :param model_name: 模型名称
    :param model_update: AI模型配置更新数据
    :return: AIModelConfig 或 None
    """
    orm_settings = db.query(ORMSystemSettings).first()
    if not orm_settings:
        raise RuntimeError("系统核心设置未找到或未正确初始化，请检查应用启动流程。")
    db_model = db.query(ORMAIModelConfig).filter(
        ORMAIModelConfig.system_settings_id == orm_settings.id,
        ORMAIModelConfig.modelName == model_name
    ).first()
    if not db_model:
        return None
    update_data = model_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(db_model, key, value)
    db.commit()
    db.refresh(db_model)
    return AIModelConfigInfo(
        modelName=db_model.modelName,
        apiKey="••••••••••••••••••••",
        baseUrl=db_model.baseUrl,
        maxTokens=db_model.maxTokens,
        temperature=db_model.temperature,
        enabled=db_model.enabled,
        provider=db_model.provider,
        appId=db_model.appId
    )

def get_ai_model_configs(db: Session) -> AIModelConfigListResponse:
    """
    获取所有AI模型配置列表
    :param db: 数据库会话
    :return: AIModelConfigListResponse
    """
    orm_settings = db.query(ORMSystemSettings).first()
    if not orm_settings:
        raise RuntimeError("系统核心设置未找到或未正确初始化，请检查应用启动流程。")
    ai_models = db.query(ORMAIModelConfig).filter(ORMAIModelConfig.system_settings_id == orm_settings.id).all()
    ai_model_schemas = [AIModelConfigInfo(
        modelName=m.modelName,
        apiKey="••••••••••••••••••••",
        baseUrl=m.baseUrl,
        maxTokens=m.maxTokens,
        temperature=m.temperature,
        enabled=m.enabled,
        provider=m.provider,
        appId=m.appId
    ) for m in ai_models]
    return AIModelConfigListResponse(success=True, data=ai_model_schemas, message="获取AI模型配置成功")

def get_ai_model_config_by_name(db: Session, model_name: str) -> Optional[AIModelConfigResponse]:
    """
    根据模型名称获取AI模型配置
    :param db: 数据库会话
    :param model_name: 模型名称
    :return: AIModelConfigResponse 或 None
    """
    orm_settings = db.query(ORMSystemSettings).first()
    if not orm_settings:
        raise RuntimeError("系统核心设置未找到或未正确初始化，请检查应用启动流程。")
    model = db.query(ORMAIModelConfig).filter(
        ORMAIModelConfig.system_settings_id == orm_settings.id,
        ORMAIModelConfig.modelName == model_name
    ).first()
    if not model:
        return None
    ai_model_schema = AIModelConfigInfo(
        modelName=model.modelName,
        apiKey="••••••••••••••••••••",
        baseUrl=model.baseUrl,
        maxTokens=model.maxTokens,
        temperature=model.temperature,
        enabled=model.enabled,
        provider=model.provider,
        appId=model.appId
    )
    return AIModelConfigResponse(success=True, data=ai_model_schema, message="获取AI模型配置成功")

def delete_ai_model_config(db: Session, model_name: str) -> bool:
    """
    删除AI模型配置
    :param db: 数据库会话
    :param model_name: 模型名称
    :return: 删除成功返回True，否则False
    """
    orm_settings = db.query(ORMSystemSettings).first()
    if not orm_settings:
        raise RuntimeError("系统核心设置未找到或未正确初始化，请检查应用启动流程。")
    db_model = db.query(ORMAIModelConfig).filter(
        ORMAIModelConfig.system_settings_id == orm_settings.id,
        ORMAIModelConfig.modelName == model_name
    ).first()
    if not db_model:
        return False
    db.delete(db_model)
    db.commit()
    return True

def toggle_ai_model_status(db: Session, model_name: str) -> Optional[AIModelConfigResponse]:
    """
    切换AI模型启用状态
    :param db: 数据库会话
    :param model_name: 模型名称
    :return: AIModelConfigResponse 或 None
    """
    orm_settings = db.query(ORMSystemSettings).first()
    if not orm_settings:
        raise RuntimeError("系统核心设置未找到或未正确初始化，请检查应用启动流程。")
    db_model = db.query(ORMAIModelConfig).filter(
        ORMAIModelConfig.system_settings_id == orm_settings.id,
        ORMAIModelConfig.modelName == model_name
    ).first()
    if not db_model:
        return None
    db_model.enabled = not db_model.enabled
    db.commit()
    db.refresh(db_model)
    ai_model_schema = AIModelConfigInfo(
        modelName=db_model.modelName,
        apiKey="••••••••••••••••••••",
        baseUrl=db_model.baseUrl,
        maxTokens=db_model.maxTokens,
        temperature=db_model.temperature,
        enabled=db_model.enabled,
        provider=db_model.provider,
        appId=db_model.appId
    )
    return AIModelConfigResponse(success=True, data=ai_model_schema, message=f"AI模型 '{model_name}' 状态已切换")

# 其余方法可按需补充，均返回schema 