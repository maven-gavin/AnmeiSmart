"""
客户领域服务 - 处理客户相关的领域逻辑
"""
from typing import List, Optional, Dict, Any

from app.customer.domain.entities.customer import CustomerEntity
from app.customer.domain.value_objects.customer_status import CustomerPriority


class CustomerDomainService:
    """客户领域服务 - 处理跨聚合的业务逻辑"""
    
    def __init__(self):
        pass
    
    def validate_customer_data(
        self,
        medical_history: Optional[str] = None,
        allergies: Optional[str] = None,
        preferences: Optional[str] = None,
        age: Optional[int] = None,
        gender: Optional[str] = None
    ) -> None:
        """验证客户数据"""
        # 验证病史长度
        if medical_history and len(medical_history.strip()) > 1000:
            raise ValueError("病史信息过长，不能超过1000字符")
        
        # 验证过敏史长度
        if allergies and len(allergies.strip()) > 500:
            raise ValueError("过敏史信息过长，不能超过500字符")
        
        # 验证偏好长度
        if preferences and len(preferences.strip()) > 500:
            raise ValueError("偏好信息过长，不能超过500字符")
        
        # 验证年龄
        if age is not None and (age < 0 or age > 150):
            raise ValueError("年龄必须在0-150之间")
        
        # 验证性别
        if gender and gender not in ['male', 'female', 'other']:
            raise ValueError("性别值无效")
    
    def calculate_customer_priority(
        self,
        medical_history: Optional[str] = None,
        allergies: Optional[str] = None,
        age: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> CustomerPriority:
        """根据客户信息计算优先级"""
        priority_score = 0
        
        # 病史权重
        if medical_history and medical_history.strip():
            priority_score += 2
        
        # 过敏史权重
        if allergies and allergies.strip():
            priority_score += 2
        
        # 年龄权重（老年人和儿童优先级更高）
        if age is not None:
            if age < 18 or age > 65:
                priority_score += 1
        
        # 特殊标签权重
        if tags:
            high_priority_tags = ['vip', 'urgent', 'critical', 'emergency']
            for tag in tags:
                if tag.lower() in high_priority_tags:
                    priority_score += 3
        
        # 根据分数确定优先级
        if priority_score >= 5:
            return CustomerPriority.HIGH
        elif priority_score >= 2:
            return CustomerPriority.MEDIUM
        else:
            return CustomerPriority.LOW
    
    def validate_profile_data(
        self,
        medical_history: Optional[str] = None,
        allergies: Optional[str] = None,
        preferences: Optional[str] = None,
        tags: Optional[str] = None
    ) -> None:
        """验证客户档案数据"""
        # 验证病史长度
        if medical_history and len(medical_history.strip()) > 1000:
            raise ValueError("病史信息过长，不能超过1000字符")
        
        # 验证过敏史长度
        if allergies and len(allergies.strip()) > 500:
            raise ValueError("过敏史信息过长，不能超过500字符")
        
        # 验证偏好长度
        if preferences and len(preferences.strip()) > 500:
            raise ValueError("偏好信息过长，不能超过500字符")
        
        # 验证标签长度
        if tags and len(tags.strip()) > 200:
            raise ValueError("标签信息过长，不能超过200字符")
    
    def validate_risk_note(self, risk_note: Dict[str, Any]) -> None:
        """验证风险提示数据"""
        required_fields = ['type', 'description', 'level']
        for field in required_fields:
            if field not in risk_note:
                raise ValueError(f"风险提示缺少必要字段: {field}")
        
        if not risk_note['type'] or not risk_note['type'].strip():
            raise ValueError("风险类型不能为空")
        
        if not risk_note['description'] or not risk_note['description'].strip():
            raise ValueError("风险描述不能为空")
        
        if risk_note['level'] not in ['high', 'medium', 'low']:
            raise ValueError("风险级别必须是 high、medium 或 low")
        
        if len(risk_note['description'].strip()) > 500:
            raise ValueError("风险描述过长，不能超过500字符")
    
    def merge_customer_tags(self, existing_tags: List[str], new_tags: List[str]) -> List[str]:
        """合并客户标签，去重并排序"""
        if not existing_tags and not new_tags:
            return []
        
        # 合并标签
        all_tags = []
        if existing_tags:
            all_tags.extend(existing_tags)
        if new_tags:
            all_tags.extend(new_tags)
        
        # 去重并排序
        unique_tags = list(set(tag.strip() for tag in all_tags if tag and tag.strip()))
        unique_tags.sort()
        
        return unique_tags
    
    def format_tags_for_storage(self, tags: List[str]) -> str:
        """将标签列表格式化为存储字符串"""
        if not tags:
            return None
        
        # 过滤空标签并去重
        valid_tags = list(set(tag.strip() for tag in tags if tag and tag.strip()))
        valid_tags.sort()
        
        return ','.join(valid_tags)
    
    def parse_tags_from_storage(self, tags_string: Optional[str]) -> List[str]:
        """从存储字符串解析标签列表"""
        if not tags_string:
            return []
        
        tags = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
        return list(set(tags))  # 去重
    
    def should_update_customer(self, customer: CustomerEntity, update_data: Dict[str, Any]) -> bool:
        """判断是否需要更新客户信息"""
        if not customer or not update_data:
            return False
        
        # 检查是否有实际变化
        for field, value in update_data.items():
            camel_field = self._to_camel_case(field)
            if hasattr(customer, camel_field):
                current_value = getattr(customer, camel_field)
                if current_value != value:
                    return True
        
        return False
    
    def get_customer_summary(self, customer: CustomerEntity) -> Dict[str, Any]:
        """获取客户摘要信息"""
        if not customer:
            return {}
        
        return {
            "id": customer.id,
            "user_id": customer.userId,
            "has_medical_history": customer.hasMedicalCondition(),
            "has_allergies": customer.hasAllergies(),
            "priority": customer.priority.value,
            "tag_count": len(customer.tags),
            "last_updated": customer.updatedAt.isoformat() if customer.updatedAt else None
        }

    @staticmethod
    def _to_camel_case(field_name: str) -> str:
        parts = field_name.split('_')
        if not parts:
            return field_name
        return parts[0] + ''.join(part.capitalize() for part in parts[1:])
