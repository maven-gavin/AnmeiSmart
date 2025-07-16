"""
Dify配置管理服务
提供Dify配置的CRUD操作和动态重载功能
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import requests

from app.db.models.system import DifyConfig
from app.schemas.system import DifyConfigCreate, DifyConfigUpdate
from app.services.ai.ai_gateway_service import reload_ai_gateway_service

logger = logging.getLogger(__name__)


def get_dify_configs(db: Session) -> List[DifyConfig]:
    """获取所有Dify配置"""
    return db.query(DifyConfig).order_by(DifyConfig.created_at.desc()).all()


def get_dify_config(db: Session, config_id: str) -> Optional[DifyConfig]:
    """根据ID获取Dify配置"""
    return db.query(DifyConfig).filter(DifyConfig.id == config_id).first()


def get_active_dify_config(db: Session) -> Optional[DifyConfig]:
    """获取当前启用的Dify配置"""
    return db.query(DifyConfig).filter(DifyConfig.enabled == True).first()


def create_dify_config(db: Session, config_data: DifyConfigCreate) -> DifyConfig:
    """创建Dify配置"""
    # 创建新配置实例
    new_config = DifyConfig(
        config_name=config_data.configName,
        base_url=config_data.baseUrl,
        description=config_data.description,
        chat_app_id=config_data.chatAppId,
        beauty_app_id=config_data.beautyAppId,
        summary_app_id=config_data.summaryAppId,
        timeout_seconds=config_data.timeoutSeconds,
        max_retries=config_data.maxRetries,
        enabled=config_data.enabled
    )
    
    # 设置API密钥（会自动加密）
    if config_data.chatApiKey:
        new_config.chat_api_key = config_data.chatApiKey
    if config_data.beautyApiKey:
        new_config.beauty_api_key = config_data.beautyApiKey
    if config_data.summaryApiKey:
        new_config.summary_api_key = config_data.summaryApiKey
    
    # 如果这是第一个启用的配置，禁用其他配置
    if config_data.enabled:
        db.query(DifyConfig).filter(DifyConfig.enabled == True).update({"enabled": False})
    
    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    
    return new_config


def update_dify_config(db: Session, config_id: str, config_data: DifyConfigUpdate) -> DifyConfig:
    """更新Dify配置"""
    config = db.query(DifyConfig).filter(DifyConfig.id == config_id).first()
    if not config:
        raise ValueError("配置不存在")
    
    # 更新字段
    update_data = config_data.model_dump(exclude_unset=True)
    
    if "configName" in update_data:
        config.config_name = update_data["configName"]
    if "baseUrl" in update_data:
        config.base_url = update_data["baseUrl"]
    if "description" in update_data:
        config.description = update_data["description"]
    if "chatAppId" in update_data:
        config.chat_app_id = update_data["chatAppId"]
    if "beautyAppId" in update_data:
        config.beauty_app_id = update_data["beautyAppId"]
    if "summaryAppId" in update_data:
        config.summary_app_id = update_data["summaryAppId"]
    if "timeoutSeconds" in update_data:
        config.timeout_seconds = update_data["timeoutSeconds"]
    if "maxRetries" in update_data:
        config.max_retries = update_data["maxRetries"]
    
    # 更新API密钥
    if "chatApiKey" in update_data and update_data["chatApiKey"]:
        config.chat_api_key = update_data["chatApiKey"]
    if "beautyApiKey" in update_data and update_data["beautyApiKey"]:
        config.beauty_api_key = update_data["beautyApiKey"]
    if "summaryApiKey" in update_data and update_data["summaryApiKey"]:
        config.summary_api_key = update_data["summaryApiKey"]
    
    # 处理启用状态
    if "enabled" in update_data:
        if update_data["enabled"]:
            # 启用当前配置，禁用其他配置
            db.query(DifyConfig).filter(DifyConfig.id != config_id).update({"enabled": False})
        config.enabled = update_data["enabled"]
    
    db.commit()
    db.refresh(config)
    
    return config


def delete_dify_config(db: Session, config_id: str) -> bool:
    """删除Dify配置"""
    config = db.query(DifyConfig).filter(DifyConfig.id == config_id).first()
    if not config:
        return False
    
    db.delete(config)
    db.commit()
    
    return True


def test_dify_connection(base_url: str, api_key: str, app_type: str) -> Dict[str, Any]:
    """测试Dify连接"""
    # 根据应用类型设置不同的超时时间
    timeout_seconds = 60 if app_type == "workflow" else 20  # workflow需要更长时间
    
    try:
        # 验证基础URL格式
        if not base_url.startswith(('http://', 'https://')):
            return {
                "success": False,
                "message": "基础URL格式错误，必须以http://或https://开头",
                "details": {"error_type": "invalid_url", "url": base_url}
            }
        
        # 构建测试URL和参数（针对不同应用类型使用不同配置）
        if app_type == "chat":
            test_url = f"{base_url}/chat-messages"
            test_data = {
                "inputs": {},
                "query": "Hello, this is a connection test.",
                "response_mode": "blocking",
                "conversation_id": "",
                "user": "test_user"
            }
        elif app_type == "agent":
            # Agent应用不支持blocking模式，使用streaming模式
            test_url = f"{base_url}/chat-messages"
            test_data = {
                "inputs": {},
                "query": "Hello, this is a connection test.",
                "response_mode": "streaming",
                "conversation_id": "",
                "user": "test_user"
            }
        elif app_type == "workflow":
            test_url = f"{base_url}/workflows/run"
            test_data = {
                "inputs": {
                    # 简化测试输入，只提供最基本的必需字段
                    "conversation_text": "测试对话内容",
                    "user_id": "test_user_123"
                },
                "response_mode": "blocking",
                "user": "test_user"
            }
        else:
            return {
                "success": False,
                "message": "不支持的应用类型"
            }
        
        # 发送测试请求
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Testing Dify connection: {test_url} (timeout: {timeout_seconds}s)")
        
        response = requests.post(
            test_url,
            json=test_data,
            headers=headers,
            timeout=timeout_seconds,
            stream=(app_type == "agent")  # Agent类型使用流式响应
        )
        
        if response.status_code == 200:
            # 对于streaming响应，简单验证是否有数据返回
            if app_type == "agent":
                # 读取第一行来验证streaming响应
                try:
                    first_line = next(response.iter_lines(decode_unicode=True))
                    if first_line and 'event' in first_line:
                        success_msg = "连接测试成功 (Streaming模式)"
                    else:
                        success_msg = "连接测试成功"
                except:
                    success_msg = "连接测试成功"
            else:
                success_msg = "连接测试成功"
                
            return {
                "success": True,
                "message": success_msg,
                "details": {
                    "status_code": response.status_code,
                    "app_type": app_type,
                    "response_mode": test_data.get("response_mode", "unknown"),
                    "response_time": f"{response.elapsed.total_seconds():.2f}s"
                }
            }
        else:
            return {
                "success": False,
                "message": f"连接测试失败: HTTP {response.status_code}",
                "details": {
                    "status_code": response.status_code,
                    "response_text": response.text[:200]  # 限制响应长度
                }
            }
            
    except requests.exceptions.Timeout:
        timeout_msg = "连接超时"
        if app_type == "workflow":
            timeout_msg += f"，工作流应用处理时间较长（{timeout_seconds}秒内未完成），请稍后重试"
        else:
            timeout_msg += "，请检查基础URL是否正确（如：http://localhost/v1）"
            
        return {
            "success": False,
            "message": timeout_msg,
            "details": {
                "error_type": "timeout", 
                "url": base_url,
                "app_type": app_type,
                "timeout_seconds": timeout_seconds
            }
        }
    except requests.exceptions.ConnectionError as e:
        error_msg = "无法连接到Dify服务"
        if "localhost:v1" in base_url:
            error_msg += "，URL格式错误：请使用 http://localhost/v1 而不是 http://localhost:v1"
        elif "localhost" in base_url and "/v1" not in base_url:
            error_msg += "，URL可能缺少 /v1 路径"
        
        return {
            "success": False,
            "message": error_msg,
            "details": {"error_type": "connection_error", "url": base_url, "error": str(e)}
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"连接测试异常: {str(e)}",
            "details": {"error_type": "unknown", "error": str(e)}
        }


def reload_ai_gateway_with_new_config():
    """重载AI Gateway配置以应用新的Dify配置"""
    try:
        reload_ai_gateway_service()
        logger.info("AI Gateway配置重载成功")
    except Exception as e:
        logger.error(f"AI Gateway配置重载失败: {e}")
        raise


def get_current_dify_settings() -> Dict[str, Any]:
    """获取当前Dify设置（用于AI Gateway）"""
    from app.db.base import get_db
    
    try:
        db = next(get_db())
        active_config = get_active_dify_config(db)
        
        if not active_config:
            return {
                "enabled": False,
                "base_url": "",
                "apps": {}
            }
        
        return {
            "enabled": True,
            "base_url": active_config.base_url,
            "timeout_seconds": active_config.timeout_seconds,
            "max_retries": active_config.max_retries,
            "apps": {
                "chat": {
                    "app_id": active_config.chat_app_id,
                    "api_key": active_config.chat_api_key
                } if active_config.chat_api_key else None,
                "beauty": {
                    "app_id": active_config.beauty_app_id,
                    "api_key": active_config.beauty_api_key
                } if active_config.beauty_api_key else None,
                "summary": {
                    "app_id": active_config.summary_app_id,
                    "api_key": active_config.summary_api_key
                } if active_config.summary_api_key else None
            }
        }
    except Exception as e:
        logger.error(f"获取Dify设置失败: {e}")
        return {
            "enabled": False,
            "base_url": "",
            "apps": {}
        }
    finally:
        try:
            db.close()
        except:
            pass 