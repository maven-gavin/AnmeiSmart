"""
咨询服务MCP工具模块

提供咨询历史、总结等功能
"""

from .history import *
from .summary import *

__all__ = ["get_consultation_history", "create_consultation_summary"] 