"""
数字人模块数据库模型导出

导出该领域的所有数据库模型，确保SQLAlchemy可以正确建立关系映射。
"""

from .digital_human import DigitalHuman

__all__ = [
    "DigitalHuman"
]
