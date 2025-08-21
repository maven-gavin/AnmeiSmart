"""
顾问通知服务

负责在新用户注册后通知顾问团队，
支持多种通知方式：WebSocket推送、邮件通知等。
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models.user import User
from app.db.models.chat import Conversation
from app.services.broadcasting_factory import create_broadcasting_service
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class ConsultantNotifier:
    """顾问通知服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
    
    async def notify_new_customer(self, user_id: str, conversation_id: str, user_info: Dict[str, Any]):
        """
        通知顾问团队有新客户注册
        
        Args:
            user_id: 新用户ID
            conversation_id: 会话ID
            user_info: 用户信息
        """
        try:
            logger.info(f"开始通知顾问团队: user_id={user_id}")
            
            # 获取在线顾问列表
            online_consultants = await self._get_online_consultants()
            
            if not online_consultants:
                logger.warning("当前没有在线顾问，将发送离线通知")
                await self._send_offline_notifications(user_id, conversation_id, user_info)
                return
            
            # 准备通知数据
            notification_data = self._prepare_notification_data(user_id, conversation_id, user_info)
            
            # WebSocket实时通知
            await self._send_realtime_notifications(online_consultants, notification_data)
            
            # 系统内通知
            await self._create_system_notifications(online_consultants, notification_data)
            
            logger.info(f"顾问通知发送完成: user_id={user_id}, consultants_count={len(online_consultants)}")
            
        except Exception as e:
            logger.error(f"通知顾问失败: user_id={user_id}, error={e}", exc_info=True)
    
    async def _get_online_consultants(self) -> List[Dict[str, Any]]:
        """获取在线顾问列表"""
        try:
            # 查询具有顾问角色的用户
            consultants = self.db.query(User).filter(
                and_(
                    User.is_active == True,
                    User.roles.any(lambda role: role.name == "consultant")
                )
            ).all()
            
            consultant_list = []
            for consultant in consultants:
                consultant_info = {
                    "user_id": consultant.id,
                    "username": consultant.username,
                    "email": consultant.email,
                    "is_online": await self._check_consultant_online_status(consultant.id)
                }
                
                # 只返回在线的顾问
                if consultant_info["is_online"]:
                    consultant_list.append(consultant_info)
            
            logger.info(f"找到在线顾问: {len(consultant_list)}位")
            return consultant_list
            
        except Exception as e:
            logger.error(f"获取在线顾问失败: {e}")
            return []
    
    async def _check_consultant_online_status(self, consultant_id: str) -> bool:
        """检查顾问在线状态"""
        try:
            # 这里可以检查WebSocket连接状态、最近活动时间等
            # 当前简化实现，认为所有活跃顾问都在线
            # 实际应用中可以集成Redis等缓存系统来跟踪在线状态
            return True
            
        except Exception as e:
            logger.error(f"检查顾问在线状态失败: consultant_id={consultant_id}, error={e}")
            return False
    
    def _prepare_notification_data(self, user_id: str, conversation_id: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """准备通知数据"""
        return {
            "type": "new_customer_registration",
            "title": "新客户注册通知",
            "message": f"新客户 {user_info.get('username', '未知用户')} 刚刚注册了系统",
            "data": {
                "customer_id": user_id,
                "conversation_id": conversation_id,
                "customer_info": {
                    "username": user_info.get("username", ""),
                    "email": user_info.get("email", ""),
                    "roles": user_info.get("roles", []),
                    "registration_time": datetime.now().isoformat(),
                    "primary_role": self._get_primary_role(user_info.get("roles", []))
                }
            },
            "priority": "normal",
            "timestamp": datetime.now().isoformat(),
            "actions": [
                {
                    "action": "claim_customer",
                    "label": "认领客户",
                    "url": f"/chat?conversationId={conversation_id}"
                },
                {
                    "action": "view_profile", 
                    "label": "查看档案",
                    "url": f"/customers/{user_id}"
                }
            ]
        }
    
    async def _send_realtime_notifications(self, consultants: List[Dict[str, Any]], notification_data: Dict[str, Any]):
        """发送实时WebSocket通知"""
        try:
            broadcasting_service = await create_broadcasting_service(self.db)
            
            for consultant in consultants:
                consultant_id = consultant["user_id"]
                
                # 为每个顾问发送个性化通知
                personalized_notification = notification_data.copy()
                personalized_notification["recipient_id"] = consultant_id
                personalized_notification["recipient_name"] = consultant["username"]
                
                # 通过WebSocket广播给特定顾问
                await broadcasting_service.send_to_user(
                    user_id=consultant_id,
                    message_type="notification",
                    data=personalized_notification
                )
                
                logger.debug(f"实时通知已发送: consultant_id={consultant_id}")
                
        except Exception as e:
            logger.error(f"发送实时通知失败: {e}")
    
    async def _create_system_notifications(self, consultants: List[Dict[str, Any]], notification_data: Dict[str, Any]):
        """创建系统内通知记录"""
        try:
            for consultant in consultants:
                consultant_id = consultant["user_id"]
                
                # 创建系统通知记录
                await self.notification_service.create_notification(
                    user_id=consultant_id,
                    title=notification_data["title"],
                    content=notification_data["message"],
                    notification_type="new_customer",
                    priority=notification_data["priority"],
                    data=notification_data["data"]
                )
                
                logger.debug(f"系统通知已创建: consultant_id={consultant_id}")
                
        except Exception as e:
            logger.error(f"创建系统通知失败: {e}")
    
    async def _send_offline_notifications(self, user_id: str, conversation_id: str, user_info: Dict[str, Any]):
        """发送离线通知（邮件等）"""
        try:
            # 获取所有顾问（包括离线的）
            all_consultants = self.db.query(User).filter(
                and_(
                    User.is_active == True,
                    User.roles.any(lambda role: role.name == "consultant")
                )
            ).all()
            
            if not all_consultants:
                logger.warning("系统中没有任何顾问用户")
                return
            
            # 准备邮件内容
            email_subject = "新客户注册通知"
            email_content = f"""
您好！

有新客户注册了我们的医美咨询平台：

客户信息：
- 用户名：{user_info.get('username', '未知用户')}
- 邮箱：{user_info.get('email', '未提供')}
- 注册时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

请及时登录系统查看客户详情并提供服务。

系统链接：/chat?conversationId={conversation_id}

祝好！
安美智享系统
            """.strip()
            
            # 发送邮件通知
            for consultant in all_consultants:
                if consultant.email:
                    try:
                        await self.notification_service.send_email_notification(
                            recipient_email=consultant.email,
                            subject=email_subject,
                            content=email_content
                        )
                        logger.debug(f"离线邮件通知已发送: consultant_email={consultant.email}")
                    except Exception as email_error:
                        logger.error(f"发送邮件失败: consultant_email={consultant.email}, error={email_error}")
                        
        except Exception as e:
            logger.error(f"发送离线通知失败: {e}")
    
    def _get_primary_role(self, roles: List[str]) -> str:
        """获取主要角色"""
        if not roles:
            return "customer"
        
        # 角色优先级
        role_priority = {
            "admin": 5,
            "consultant": 4,
            "doctor": 3,
            "operator": 2,
            "customer": 1
        }
        
        # 找到优先级最高的角色
        primary_role = max(roles, key=lambda role: role_priority.get(role, 0))
        return primary_role
    
    async def notify_customer_claimed(self, customer_id: str, consultant_id: str, conversation_id: str):
        """通知客户已被认领"""
        try:
            # 获取顾问信息
            consultant = self.db.query(User).filter(User.id == consultant_id).first()
            if not consultant:
                logger.warning(f"顾问不存在: consultant_id={consultant_id}")
                return
            
            # 发送通知给客户
            notification_data = {
                "type": "consultant_assigned",
                "title": "专属顾问分配通知",
                "message": f"您的专属顾问 {consultant.username} 已为您服务",
                "data": {
                    "consultant_id": consultant_id,
                    "consultant_name": consultant.username,
                    "conversation_id": conversation_id
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # WebSocket通知客户
            broadcasting_service = await create_broadcasting_service(self.db)
            await broadcasting_service.send_to_user(
                user_id=customer_id,
                message_type="notification",
                data=notification_data
            )
            
            logger.info(f"客户认领通知已发送: customer_id={customer_id}, consultant_id={consultant_id}")
            
        except Exception as e:
            logger.error(f"通知客户认领失败: customer_id={customer_id}, error={e}")


def create_consultant_notifier(db: Session) -> ConsultantNotifier:
    """创建顾问通知服务实例"""
    return ConsultantNotifier(db) 