"""
数字人模块数据库模型导出

导出该模块的所有数据库模型，确保SQLAlchemy可以正确建立关系映射。
"""

from .digital_human import DigitalHuman, DigitalHumanAgentConfig

__all__ = [
    "DigitalHuman",
    "DigitalHumanAgentConfig",
]

