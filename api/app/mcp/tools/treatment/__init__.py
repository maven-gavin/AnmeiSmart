"""
治疗方案MCP工具模块

提供方案生成、优化等功能
"""

from .plan_generation import *
from .optimization import *

__all__ = ["generate_treatment_plan", "optimize_plan"] 