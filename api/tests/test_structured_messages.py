"""
结构化消息功能测试

测试新的统一消息模型中的结构化消息类型（如预约确认卡、服务推荐等）
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.services.chat.message_service import MessageService
from app.schemas.chat import (
    AppointmentCardData, MessageInfo,
    create_appointment_card_content, 
    create_service_recommendation_content
)
from app.db.models.chat import Message, Conversation
from app.db.models.user import User, Role
from app.db.models.customer import Customer
from app.db.models.user import Consultant

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TestStructuredMessages:
    """结构化消息测试类"""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, db: Session):
        """设置测试数据"""
        # 查询或创建角色（如果不存在）
        customer_role = db.query(Role).filter(Role.name == "customer").first()
        if not customer_role:
            customer_role = Role(id="role_customer_test", name="customer_test", description="测试客户")
            db.add(customer_role)
        
        consultant_role = db.query(Role).filter(Role.name == "consultant").first()
        if not consultant_role:
            consultant_role = Role(id="role_consultant_test", name="consultant_test", description="测试顾问")
            db.add(consultant_role)
        
        system_role = db.query(Role).filter(Role.name == "system").first()
        if not system_role:
            system_role = Role(id="role_system_test", name="system_test", description="测试系统")
            db.add(system_role)
        
        # 创建测试用户，使用唯一的测试邮箱
        self.customer_user = User(
            id="test_user_001",
            username="测试客户001",
            email="test_customer001@test.com",
            hashed_password=pwd_context.hash("password123")
        )
        self.consultant_user = User(
            id="test_consultant_001", 
            username="测试顾问001",
            email="test_consultant001@test.com",
            hashed_password=pwd_context.hash("password123")
        )
        self.system_user = User(
            id="system",
            username="系统",
            email="system@test.com",
            hashed_password=pwd_context.hash("password123")
        )
        
        # 创建扩展信息
        customer_info = Customer(user_id="test_user_001")
        consultant_info = Consultant(user_id="test_consultant_001")
        
        # 创建测试会话
        self.test_conversation = Conversation(
            id="test_conv_001",
            title="测试会话",
            customer_id="test_user_001",
            assigned_consultant_id="test_consultant_001"
        )
        
        # 添加到数据库
        db.add_all([
            self.customer_user, self.consultant_user, self.system_user,
            customer_info, consultant_info,
            self.test_conversation
        ])
        db.commit()
        
        # 建立用户角色关系
        if customer_role:
            self.customer_user.roles.append(customer_role)
        if consultant_role:
            self.consultant_user.roles.append(consultant_role)
        if system_role:
            self.system_user.roles.append(system_role)
        db.commit()

    def test_create_appointment_card_message(self, db: Session):
        """测试创建预约确认卡片消息"""
        service = MessageService(db)
        
        # 准备预约数据
        appointment_data = AppointmentCardData(
            appointment_id="appt_12345",
            service_name="面部深层清洁护理",
            consultant_name="李美容师",
            consultant_avatar="/avatars/consultant1.png",
            scheduled_time=(datetime.now() + timedelta(days=1)).isoformat(),
            duration_minutes=60,
            price=388.0,
            location="北京市朝阳区美容院",
            status="pending",
            notes="请提前10分钟到达"
        )
        
        # 创建预约确认消息
        message = service.create_appointment_card_message(
            conversation_id="test_conv_001",
            sender_id="test_consultant_001",
            sender_type="consultant",
            appointment_data=appointment_data
        )
        
        # 验证消息创建成功
        assert message is not None
        assert message.type == "structured"
        assert message.is_important is True  # 预约消息应该标记为重要
        
        # 验证内容结构
        content = message.content
        assert content["card_type"] == "appointment_confirmation"
        assert content["title"] == "预约确认"
        assert "data" in content
        assert "actions" in content
        
        # 验证预约数据
        card_data = content["data"]
        assert card_data["appointment_id"] == "appt_12345"
        assert card_data["service_name"] == "面部深层清洁护理"
        assert card_data["price"] == 388.0
        assert card_data["status"] == "pending"
        
        # 验证操作按钮
        actions = content["actions"]
        assert "primary" in actions
        assert "secondary" in actions
        assert actions["primary"]["text"] == "确认预约"
        assert actions["secondary"]["text"] == "重新安排"

    def test_create_service_recommendation_message(self, db: Session):
        """测试创建服务推荐卡片消息"""
        service = MessageService(db)
        
        # 准备推荐服务数据
        services = [
            {
                "name": "面部深层清洁",
                "price": 288,
                "duration": 60,
                "description": "深层清洁毛孔，去除黑头",
                "suitableFor": "油性肌肤"
            },
            {
                "name": "补水保湿护理",
                "price": 188,
                "duration": 45,
                "description": "深度补水，改善肌肤干燥",
                "suitableFor": "干性肌肤"
            }
        ]
        
        # 创建服务推荐消息
        message = service.create_service_recommendation_message(
            conversation_id="test_conv_001",
            sender_id="test_consultant_001",
            sender_type="consultant",
            services=services,
            title="为您推荐的护理服务"
        )
        
        # 验证消息创建成功
        assert message is not None
        assert message.type == "structured"
        
        # 验证内容结构
        content = message.content
        assert content["card_type"] == "service_recommendation"
        assert content["title"] == "为您推荐的护理服务"
        
        # 验证服务数据
        card_data = content["data"]
        assert "services" in card_data
        assert len(card_data["services"]) == 2
        assert card_data["services"][0]["name"] == "面部深层清洁"
        assert card_data["services"][1]["price"] == 188

    def test_create_custom_structured_message(self, db: Session):
        """测试创建自定义结构化消息"""
        service = MessageService(db)
        
        # 创建自定义结构化消息
        message = service.create_custom_structured_message(
            conversation_id="test_conv_001",
            sender_id="test_consultant_001",
            sender_type="consultant",
            card_type="consultation_summary",
            title="咨询总结",
            data={
                "customer_concerns": ["肌肤暗沉", "毛孔粗大"],
                "recommended_treatments": ["深层清洁", "补水护理"],
                "next_steps": "建议预约深层清洁护理"
            },
            subtitle="根据您的肌肤状况",
            components=[
                {
                    "type": "text",
                    "content": "感谢您的咨询，基于我们的专业分析..."
                },
                {
                    "type": "button",
                    "content": "立即预约",
                    "action": {
                        "type": "book_appointment",
                        "data": {"service_type": "deep_cleansing"}
                    }
                }
            ]
        )
        
        # 验证消息创建成功
        assert message is not None
        assert message.type == "structured"
        
        # 验证内容结构
        content = message.content
        assert content["card_type"] == "consultation_summary"
        assert content["title"] == "咨询总结"
        assert content["subtitle"] == "根据您的肌肤状况"
        
        # 验证组件数据
        assert "components" in content
        assert len(content["components"]) == 2
        assert content["components"][0]["type"] == "text"
        assert content["components"][1]["type"] == "button"

    def test_message_info_schema_conversion(self, db: Session):
        """测试结构化消息的Schema转换"""
        service = MessageService(db)
        
        # 创建一个结构化消息
        appointment_data = AppointmentCardData(
            appointment_id="appt_test",
            service_name="测试服务",
            consultant_name="测试顾问",
            scheduled_time=datetime.now().isoformat(),
            duration_minutes=30,
            price=100.0,
            location="测试地点",
            status="confirmed"
        )
        
        message = service.create_appointment_card_message(
            conversation_id="test_conv_001",
            sender_id="test_consultant_001",
            sender_type="consultant",
            appointment_data=appointment_data
        )
        
        # 转换为Schema
        message_info = MessageInfo.from_model(message)
        
        # 验证转换成功
        assert message_info is not None
        assert message_info.type == "structured"
        assert message_info.id == message.id
        
        # 验证便利属性
        assert message_info.text_content == "预约确认"  # 应该返回title
        assert message_info.structured_data is not None
        assert message_info.structured_data["appointment_id"] == "appt_test"

    def test_schema_helper_functions(self):
        """测试Schema辅助函数"""
        # 测试预约卡片内容创建
        appointment_data = AppointmentCardData(
            appointment_id="appt_test",
            service_name="测试服务",
            consultant_name="测试顾问",
            scheduled_time=datetime.now().isoformat(),
            duration_minutes=30,
            price=100.0,
            location="测试地点",
            status="pending"
        )
        
        content = create_appointment_card_content(
            appointment_data=appointment_data,
            title="测试预约确认"
        )
        
        # 验证内容结构
        assert content["card_type"] == "appointment_confirmation"
        assert content["title"] == "测试预约确认"
        assert content["data"]["appointment_id"] == "appt_test"
        assert content["data"]["status"] == "pending"
        
        # 测试服务推荐内容创建
        services = [{"name": "测试服务", "price": 100}]
        content = create_service_recommendation_content(
            services=services,
            title="测试推荐"
        )
        
        # 验证内容结构
        assert content["card_type"] == "service_recommendation"
        assert content["title"] == "测试推荐"
        assert content["data"]["services"][0]["name"] == "测试服务"

    def test_message_types_enum_support(self, db: Session):
        """测试所有四种消息类型的枚举支持"""
        service = MessageService(db)
        
        # 测试 text 消息
        text_msg = service.create_text_message(
            conversation_id="test_conv_001",
            sender_id="test_user_001",
            sender_type="customer",
            text="测试文本消息"
        )
        
        # 测试 media 消息
        media_msg = service.create_media_message(
            conversation_id="test_conv_001",
            sender_id="test_user_001",
            sender_type="customer",
            media_url="http://example.com/test.jpg",
            media_name="test.jpg",
            mime_type="image/jpeg",
            size_bytes=1024
        )
        
        # 测试 system 消息
        system_msg = service.create_system_event_message(
            conversation_id="test_conv_001",
            event_type="user_joined",
            event_data={"user_name": "测试用户"}
        )
        
        # 测试 structured 消息
        appointment_data = AppointmentCardData(
            appointment_id="appt_enum_test",
            service_name="测试服务",
            consultant_name="测试顾问",
            scheduled_time=datetime.now().isoformat(),
            duration_minutes=30,
            price=100.0,
            location="测试地点",
            status="pending"
        )
        
        structured_msg = service.create_appointment_card_message(
            conversation_id="test_conv_001",
            sender_id="test_consultant_001",
            sender_type="consultant",
            appointment_data=appointment_data
        )
        
        # 验证所有消息都能正确保存到数据库
        saved_messages = [text_msg, media_msg, system_msg, structured_msg]
        for msg in saved_messages:
            assert msg is not None
            assert msg.id is not None
        
        # 验证类型正确
        message_types = {msg.type for msg in saved_messages}
        assert message_types == {"text", "media", "system", "structured"} 