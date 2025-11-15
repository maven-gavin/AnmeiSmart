"""
MCP工具模块

按功能领域组织的MCP工具实现，支持：
- 模块化组织，易于维护
- 自动工具发现和注册
- 清晰的功能分类
"""

# 导入所有工具模块，触发装饰器注册
from . import user
from . import customer  
from . import consultation
from . import projects

__all__ = [
    "user",
    "customer", 
    "consultation",
    "projects"
] 