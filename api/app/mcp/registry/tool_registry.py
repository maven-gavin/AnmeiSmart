"""
MCP工具注册中心

提供工具的注册、发现和管理功能，支持：
- 装饰器自动注册
- 按模块自动发现
- 工具元数据管理
- 分组和分类管理
"""

import inspect
import importlib
import pkgutil
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class MCPToolMetadata:
    """MCP工具元数据"""
    name: str
    description: str
    category: str
    func: Callable
    signature: inspect.Signature
    module: str
    registered_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "module": self.module,
            "registered_at": self.registered_at.isoformat(),
            "parameters": self._get_parameters_info()
        }
    
    def _get_parameters_info(self) -> Dict[str, Any]:
        """获取参数信息"""
        params = {}
        for name, param in self.signature.parameters.items():
            if name == 'self':
                continue
            
            param_info = {
                "type": self._get_type_name(param.annotation),
                "required": param.default == inspect.Parameter.empty,
            }
            
            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default
                
            params[name] = param_info
        
        return params
    
    def _get_type_name(self, annotation) -> str:
        """获取类型名称"""
        if annotation == inspect.Parameter.empty:
            return "any"
        elif annotation == str:
            return "string"
        elif annotation == int:
            return "integer"
        elif annotation == bool:
            return "boolean"
        elif annotation == float:
            return "number"
        elif annotation == list:
            return "array"
        elif annotation == dict:
            return "object"
        else:
            return str(annotation).replace("<class '", "").replace("'>", "")


class MCPToolRegistry:
    """MCP工具注册中心 - 负责工具的注册和管理"""
    
    def __init__(self):
        self.tools: Dict[str, MCPToolMetadata] = {}
        self.categories: Dict[str, List[str]] = {}
        
    def register_tool(
        self, 
        name: str, 
        func: Callable, 
        description: str = "",
        category: str = "general"
    ) -> None:
        """注册工具函数"""
        if name in self.tools:
            logger.warning(f"工具 '{name}' 已存在，将被覆盖")
        
        metadata = MCPToolMetadata(
            name=name,
            description=description or func.__doc__ or f"工具: {name}",
            category=category,
            func=func,
            signature=inspect.signature(func),
            module=func.__module__,
            registered_at=datetime.now()
        )
        
        self.tools[name] = metadata
        
        # 更新分类
        if category not in self.categories:
            self.categories[category] = []
        if name not in self.categories[category]:
            self.categories[category].append(name)
        
        logger.info(f"注册MCP工具: {name} (分类: {category})")
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """获取工具函数"""
        metadata = self.tools.get(name)
        return metadata.func if metadata else None
    
    def get_tool_metadata(self, name: str) -> Optional[MCPToolMetadata]:
        """获取工具元数据"""
        return self.tools.get(name)
    
    def get_tool_description(self, name: str) -> str:
        """获取工具描述"""
        metadata = self.tools.get(name)
        return metadata.description if metadata else f"工具: {name}"
    
    def get_all_tools(self) -> List[str]:
        """获取所有注册的工具名称"""
        return list(self.tools.keys())
    
    def get_tools_by_category(self, category: str) -> List[str]:
        """按分类获取工具列表"""
        return self.categories.get(category, [])
    
    def get_all_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self.categories.keys())
    
    def is_tool_registered(self, name: str) -> bool:
        """检查工具是否已注册"""
        return name in self.tools
    
    def get_tools_info(self) -> List[Dict[str, Any]]:
        """获取所有工具的详细信息"""
        return [metadata.to_dict() for metadata in self.tools.values()]
    
    def auto_discover_tools(self, package_name: str) -> int:
        """自动发现并注册指定包下的所有工具"""
        discovered_count = 0
        
        try:
            package = importlib.import_module(package_name)
            
            # 遍历包中的所有模块
            if hasattr(package, '__path__'):
                for importer, modname, ispkg in pkgutil.walk_packages(
                    package.__path__, 
                    package.__name__ + "."
                ):
                    try:
                        module = importlib.import_module(modname)
                        
                        # 查找模块中标记为MCP工具的函数
                        for name, obj in inspect.getmembers(module):
                            if (inspect.isfunction(obj) and 
                                hasattr(obj, '_mcp_tool_metadata')):
                                
                                metadata = obj._mcp_tool_metadata
                                self.register_tool(
                                    metadata['name'],
                                    obj,
                                    metadata['description'],
                                    metadata['category']
                                )
                                discovered_count += 1
                                
                    except Exception as e:
                        logger.warning(f"加载模块 {modname} 失败: {e}")
                        
        except Exception as e:
            logger.error(f"自动发现工具失败: {e}")
        
        logger.info(f"自动发现完成，注册了 {discovered_count} 个工具")
        return discovered_count


# 全局工具注册中心实例
_global_registry = MCPToolRegistry()


def mcp_tool(name: str = None, description: str = "", category: str = "general"):
    """
    MCP工具装饰器
    
    Args:
        name: 工具名称（可选，默认使用函数名）
        description: 工具描述（可选，默认使用函数文档字符串）
        category: 工具分类（可选，默认为general）
    
    Example:
        @mcp_tool(name="get_user_info", description="获取用户信息", category="user")
        async def get_user_profile(user_id: str) -> dict:
            return {"user_id": user_id}
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"工具: {tool_name}"
        
        # 在函数上添加元数据标记
        func._mcp_tool_metadata = {
            'name': tool_name,
            'description': tool_description,
            'category': category
        }
        
        # 立即注册到全局注册中心
        _global_registry.register_tool(tool_name, func, tool_description, category)
        
        return func
    
    return decorator


def get_global_registry() -> MCPToolRegistry:
    """获取全局工具注册中心"""
    return _global_registry 