"""
Agent配置管理服务
提供Agent配置的CRUD操作和动态重载功能
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.ai.models.agent_config import AgentConfig
from app.ai.schemas.ai import AgentConfigCreate, AgentConfigUpdate, AgentConfigInfo
from app.ai.ai_gateway_service import reload_ai_gateway_service

logger = logging.getLogger(__name__)


class AgentConfigService:
    """Agent配置服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_agent_configs(self) -> List[AgentConfigInfo]:
        """获取所有Agent配置"""
        configs = self.db.query(AgentConfig).order_by(AgentConfig.created_at.desc()).all()
        return [AgentConfigInfo.model_validate(config) for config in configs]
    
    def get_agent_config(self, config_id: str) -> Optional[AgentConfigInfo]:
        """根据ID获取Agent配置"""
        config = self.db.query(AgentConfig).filter(AgentConfig.id == config_id).first()
        return AgentConfigInfo.model_validate(config) if config else None
    
    def get_agent_configs_by_environment(self, environment: str) -> List[AgentConfigInfo]:
        """根据环境获取Agent配置列表"""
        configs = self.db.query(AgentConfig).filter(
            AgentConfig.environment == environment
        ).order_by(AgentConfig.created_at.desc()).all()
        return [AgentConfigInfo.model_validate(config) for config in configs]
    
    def get_active_agent_configs(self) -> List[AgentConfigInfo]:
        """获取当前启用的Agent配置列表"""
        configs = self.db.query(AgentConfig).filter(AgentConfig.enabled == True).all()
        return [AgentConfigInfo.model_validate(config) for config in configs]
    
    def create_agent_config(self, config_data: AgentConfigCreate) -> AgentConfigInfo:
        """创建Agent配置"""
        # 检查同一环境下是否已存在相同应用ID的配置
        existing_config = self.db.query(AgentConfig).filter(
            AgentConfig.environment == config_data.environment,
            AgentConfig.app_id == config_data.appId
        ).first()
        
        if existing_config:
            raise ValueError(f"环境 '{config_data.environment}' 中已存在应用ID '{config_data.appId}' 的配置")
        
        # 创建新配置实例
        new_config = AgentConfig(
            environment=config_data.environment,
            app_id=config_data.appId,
            app_name=config_data.appName,
            agent_type=config_data.agentType,
            base_url=config_data.baseUrl,
            timeout_seconds=config_data.timeoutSeconds,
            max_retries=config_data.maxRetries,
            enabled=config_data.enabled,
            description=config_data.description
        )
        
        # 设置API密钥（会自动加密）
        new_config.api_key = config_data.apiKey
        
        self.db.add(new_config)
        self.db.commit()
        self.db.refresh(new_config)
        
        return AgentConfigInfo.model_validate(new_config)
    
    def update_agent_config(self, config_id: str, config_data: AgentConfigUpdate) -> AgentConfigInfo:
        """更新Agent配置"""
        config = self.db.query(AgentConfig).filter(AgentConfig.id == config_id).first()
        if not config:
            raise ValueError("配置不存在")
        
        # 检查环境和应用ID的唯一性
        if config_data.environment and config_data.appId:
            existing_config = self.db.query(AgentConfig).filter(
                AgentConfig.environment == config_data.environment,
                AgentConfig.app_id == config_data.appId,
                AgentConfig.id != config_id
            ).first()
            
            if existing_config:
                raise ValueError(f"环境 '{config_data.environment}' 中已存在应用ID '{config_data.appId}' 的配置")
        
        # 更新字段
        update_data = config_data.model_dump(exclude_unset=True)
        
        if "environment" in update_data:
            config.environment = update_data["environment"]
        if "appId" in update_data:
            config.app_id = update_data["appId"]
        if "appName" in update_data:
            config.app_name = update_data["appName"]
        if "agentType" in update_data:
            config.agent_type = update_data["agentType"]
        if "baseUrl" in update_data:
            config.base_url = update_data["baseUrl"]
        if "timeoutSeconds" in update_data:
            config.timeout_seconds = update_data["timeoutSeconds"]
        if "maxRetries" in update_data:
            config.max_retries = update_data["maxRetries"]
        if "enabled" in update_data:
            config.enabled = update_data["enabled"]
        if "description" in update_data:
            config.description = update_data["description"]
        
        # 更新API密钥
        if "apiKey" in update_data and update_data["apiKey"]:
            config.api_key = update_data["apiKey"]
        
        self.db.commit()
        self.db.refresh(config)
        
        return AgentConfigInfo.model_validate(config)
    
    def delete_agent_config(self, config_id: str) -> bool:
        """删除Agent配置"""
        config = self.db.query(AgentConfig).filter(AgentConfig.id == config_id).first()
        if not config:
            return False
        
        # 检查是否为启用状态（前端已经做了检查，这里再次确认）
        if config.enabled:
            raise ValueError("启用配置不可删除，请先禁用配置")
        
        self.db.delete(config)
        self.db.commit()
        
        return True
    
    def test_agent_connection(self, config: AgentConfigInfo) -> Dict[str, Any]:
        """测试Agent连接（通过配置ID查库解密api_key）"""
        logger.info("=" * 80)
        logger.info("开始测试Agent连接")
        logger.info(f"接收到的配置对象: {config}")
        logger.info(f"配置ID: {config.id}")
        logger.info(f"配置类型: {type(config)}")
        logger.info(f"配置属性: {dir(config)}")
        
        # 验证 appId
        app_id = config.appId or getattr(config, 'app_id', None)
        logger.info(f"提取的appId: {app_id}")
        logger.info(f"config.appId值: {config.appId}")
        
        if not app_id:
            logger.warning("appId为空或未找到")
            return {
                "success": False,
                "message": "未指定appId，无法测试连接",
                "details": {}
            }
        
        # 1. 通过 config.id 查询数据库，获取 AgentConfig ORM 实例
        db_config = self.db.query(AgentConfig).filter(AgentConfig.id == config.id).first()
        if not db_config:
            return {
                "success": False,
                "message": f"未找到ID为{config.id}的Agent配置",
                "details": {}
            }
        # 2. 解密 api_key
        api_key = db_config.api_key  # 通过 hybrid_property 自动解密
        if not api_key:
            return {
                "success": False,
                "message": "未配置API密钥，无法测试连接",
                "details": {}
            }
        base_url = config.baseUrl or getattr(config, 'base_url', '')
        timeout_seconds = config.timeoutSeconds or getattr(config, 'timeout_seconds', 30)
        try:
            # 验证基础URL格式
            if not base_url.startswith(('http://', 'https://')):
                return {
                    "success": False,
                    "message": "基础URL格式错误，必须以http://或https://开头",
                    "details": {"error_type": "invalid_url", "url": base_url}
                }
            
            # 统一使用 Dify 的 /info 接口测试连接
            # 该接口适用于所有类型的智能体，只需获取应用基本信息即可验证配置正确性
            # 确保 base_url 以 / 结尾，然后拼接 info
            base_url_normalized = base_url.rstrip('/')
            test_url = f"{base_url_normalized}/info"
            logger.info(f"使用 Dify /info 接口测试连接")
            logger.info(f"base_url: {base_url}")
            logger.info(f"测试URL: {test_url}")
            logger.info(f"appId: {app_id}")
            logger.info(f"timeout: {timeout_seconds}秒")

            # 发送测试请求（GET 请求）
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            import requests
            response = requests.get(
                test_url,
                headers=headers,
                timeout=timeout_seconds
            )
            if response.status_code == 200:
                # 尝试解析响应，获取应用信息
                try:
                    app_info = response.json()
                    app_name_from_api = app_info.get("name", "未知")
                    app_mode = app_info.get("mode", "未知")
                    logger.info(
                        f"✅ 连接测试成功: base_url={base_url}, test_url={test_url}, "
                        f"app_name={app_name_from_api}, mode={app_mode}, "
                        f"response_time={response.elapsed.total_seconds():.2f}s"
                    )
                except Exception as e:
                    logger.warning(f"解析应用信息失败: {e}")
                    app_name_from_api = "未知"
                    app_mode = "未知"
                    logger.info(
                        f"✅ 连接测试成功（但解析响应失败）: base_url={base_url}, "
                        f"test_url={test_url}, response_time={response.elapsed.total_seconds():.2f}s"
                    )
                
                return {
                    "success": True,
                    "message": "连接测试成功",
                    "details": {
                        "status_code": response.status_code,
                        "app_name": config.appName,
                        "app_name_from_api": app_name_from_api,
                        "app_mode": app_mode,
                        "environment": config.environment,
                        "base_url": base_url,
                        "test_url": test_url,
                        "response_time": f"{response.elapsed.total_seconds():.2f}s"
                    }
                }
            else:
                # 处理非 200 状态码
                error_detail = ""
                error_json = {}
                try:
                    error_response = response.json()
                    error_detail = error_response.get("message", response.text[:200])
                    error_json = error_response
                except:
                    error_detail = response.text[:200] if response.text else "无响应内容"
                
                # 根据状态码提供更详细的错误信息
                status_code = response.status_code
                if status_code == 502:
                    error_message = f"网关错误 (HTTP 502): Dify 服务可能不可用或网络配置有问题"
                    logger.error(
                        f"连接测试失败 - HTTP 502: base_url={base_url}, test_url={test_url}, "
                        f"error_detail={error_detail}, headers={dict(response.headers)}"
                    )
                elif status_code == 503:
                    error_message = f"服务不可用 (HTTP 503): Dify 服务暂时不可用"
                elif status_code == 404:
                    error_message = f"接口不存在 (HTTP 404): 请检查 base_url 是否正确，应为 http://host:port/v1"
                elif status_code == 401:
                    error_message = f"认证失败 (HTTP 401): API Key 可能无效或已过期"
                elif status_code == 403:
                    error_message = f"访问被拒绝 (HTTP 403): API Key 可能没有访问权限"
                else:
                    error_message = f"连接测试失败: HTTP {status_code}"
                
                logger.error(
                    f"连接测试失败: status_code={status_code}, base_url={base_url}, "
                    f"test_url={test_url}, error_detail={error_detail}"
                )
                
                return {
                    "success": False,
                    "message": error_message,
                    "details": {
                        "status_code": status_code,
                        "error_detail": error_detail,
                        "error_json": error_json,
                        "test_url": test_url,
                        "base_url": base_url
                    }
                }
        except requests.exceptions.Timeout as e:
            timeout_msg = f"连接超时（{timeout_seconds}秒内未完成），请检查基础URL是否正确或服务是否响应"
            logger.error(
                f"连接超时: base_url={base_url}, test_url={test_url}, "
                f"timeout_seconds={timeout_seconds}, error={str(e)}"
            )
            return {
                "success": False,
                "message": timeout_msg,
                "details": {
                    "error_type": "timeout",
                    "url": base_url,
                    "test_url": test_url,
                    "timeout_seconds": timeout_seconds,
                    "error": str(e)
                }
            }
        except requests.exceptions.ConnectionError as e:
            error_msg = "无法连接到Agent服务"
            if "localhost:v1" in base_url:
                error_msg += "，URL格式错误：请使用 http://localhost/v1 而不是 http://localhost:v1"
            elif "localhost" in base_url and "/v1" not in base_url:
                error_msg += "，URL可能缺少 /v1 路径"
            elif "host.docker.internal" in base_url:
                error_msg += f"，无法连接到 host.docker.internal，请检查：1) Docker 网络配置 2) Dify 服务是否运行 3) 端口是否正确"
            
            logger.error(
                f"连接错误: base_url={base_url}, test_url={test_url}, error={str(e)}",
                exc_info=True
            )
            
            return {
                "success": False,
                "message": error_msg,
                "details": {
                    "error_type": "connection_error",
                    "url": base_url,
                    "test_url": test_url,
                    "error": str(e)
                }
            }
        except Exception as e:
            logger.error(
                f"连接测试发生未知异常: base_url={base_url}, test_url={test_url}, error={str(e)}",
                exc_info=True
            )
            return {
                "success": False,
                "message": f"连接测试异常: {str(e)}",
                "details": {
                    "error_type": "unknown",
                    "url": base_url,
                    "test_url": test_url,
                    "error": str(e)
                }
            }
    
    def reload_ai_gateway(self):
        """重载AI Gateway配置以应用新的Agent配置"""
        try:
            reload_ai_gateway_service()
            logger.info("AI Gateway配置重载成功")
        except Exception as e:
            logger.error(f"AI Gateway配置重载失败: {e}")
            raise
    
    def get_current_agent_settings(self) -> Dict[str, Any]:
        """获取当前Agent设置（用于AI Gateway）"""
        active_configs = self.db.query(AgentConfig).filter(AgentConfig.enabled == True).all()
        
        if not active_configs:
            return {
                "enabled": False,
                "configs": {}
            }
        
        # 按环境分组配置
        settings = {
            "enabled": True,
            "configs": {}
        }
        
        for config in active_configs:
            env_key = config.environment
            if env_key not in settings["configs"]:
                settings["configs"][env_key] = {}
            
            settings["configs"][env_key][config.app_id] = {
                "app_name": config.app_name,
                "base_url": config.base_url,
                "api_key": config.api_key,
                "timeout_seconds": config.timeout_seconds,
                "max_retries": config.max_retries
            }
        
        return settings

