"""
通讯录模块数据库模型导出

导出该领域的所有数据库模型，确保SQLAlchemy可以正确建立关系映射。
"""

from .contacts import ContactTag, ContactGroup, ContactPrivacySetting, Friendship

__all__ = [
    "ContactTag", "ContactGroup", "ContactPrivacySetting", "Friendship"
]
