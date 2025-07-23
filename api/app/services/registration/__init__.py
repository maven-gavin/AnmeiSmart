"""
注册自动化服务包

处理用户注册后的自动化流程，包括：
- 创建默认会话
- 触发Dify Agent生成欢迎消息
- 通知顾问团队
"""

from .automation_service import RegistrationAutomationService
from .consultant_notifier import ConsultantNotifier

__all__ = [
    "RegistrationAutomationService",
    "ConsultantNotifier"
] 