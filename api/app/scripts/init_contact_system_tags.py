"""
初始化通讯录系统预设标签
"""
import asyncio
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.db.models.contacts import ContactTag
from app.db.models.user import User
from app.db.uuid_utils import tag_id
import logging

logger = logging.getLogger(__name__)

# 系统预设标签配置
SYSTEM_TAGS = {
    "medical": {
        "name": "医疗相关",
        "tags": [
            {"name": "医生", "color": "#059669", "icon": "stethoscope"},
            {"name": "顾问", "color": "#0891B2", "icon": "user-tie"},
            {"name": "护士", "color": "#DB2777", "icon": "heart"},
            {"name": "专家", "color": "#DC2626", "icon": "award"},
            {"name": "同行", "color": "#7C3AED", "icon": "users"}
        ]
    },
    "business": {
        "name": "商务关系",
        "tags": [
            {"name": "客户", "color": "#F59E0B", "icon": "user-heart"},
            {"name": "潜在客户", "color": "#F97316", "icon": "user-plus"},
            {"name": "VIP客户", "color": "#DC2626", "icon": "star"},
            {"name": "供应商", "color": "#7C3AED", "icon": "truck"},
            {"name": "合作伙伴", "color": "#10B981", "icon": "handshake"}
        ]
    },
    "work": {
        "name": "工作关系",
        "tags": [
            {"name": "同事", "color": "#3B82F6", "icon": "users"},
            {"name": "上级", "color": "#8B5CF6", "icon": "crown"},
            {"name": "下属", "color": "#06B6D4", "icon": "user-check"},
            {"name": "HR", "color": "#EC4899", "icon": "clipboard-list"}
        ]
    },
    "personal": {
        "name": "个人关系",
        "tags": [
            {"name": "朋友", "color": "#8B5CF6", "icon": "user-heart"},
            {"name": "家人", "color": "#EC4899", "icon": "home"},
            {"name": "同学", "color": "#06B6D4", "icon": "graduation-cap"}
        ]
    }
}


def init_system_tags_for_all_users():
    """为所有用户初始化系统预设标签"""
    db = SessionLocal()
    
    try:
        # 获取所有用户
        users = db.query(User).all()
        logger.info(f"找到 {len(users)} 个用户，开始初始化系统标签")
        
        for user in users:
            init_system_tags_for_user(db, user.id)
        
        db.commit()
        logger.info("系统标签初始化完成")
        
    except Exception as e:
        db.rollback()
        logger.error(f"初始化系统标签失败: {e}")
        raise
    finally:
        db.close()


def init_system_tags_for_user(db: Session, user_id: str):
    """为特定用户初始化系统预设标签"""
    try:
        display_order = 0
        
        for category, category_data in SYSTEM_TAGS.items():
            for tag_data in category_data["tags"]:
                # 检查标签是否已存在
                existing_tag = db.query(ContactTag).filter(
                    ContactTag.user_id == user_id,
                    ContactTag.name == tag_data["name"],
                    ContactTag.category == category
                ).first()
                
                if existing_tag:
                    logger.debug(f"标签已存在: {tag_data['name']} (用户: {user_id})")
                    continue
                
                # 创建系统标签
                tag = ContactTag(
                    id=tag_id(),
                    user_id=user_id,
                    name=tag_data["name"],
                    color=tag_data["color"],
                    icon=tag_data["icon"],
                    description=f"系统预设标签：{tag_data['name']}",
                    category=category,
                    is_system_tag=True,
                    display_order=display_order,
                    is_visible=True,
                    usage_count=0
                )
                
                db.add(tag)
                display_order += 1
                
                logger.debug(f"创建系统标签: {tag_data['name']} (用户: {user_id})")
        
        logger.info(f"用户 {user_id} 的系统标签初始化完成")
        
    except Exception as e:
        logger.error(f"为用户 {user_id} 初始化系统标签失败: {e}")
        raise


def init_system_tags_for_new_user(user_id: str):
    """为新注册用户初始化系统预设标签（单独调用）"""
    db = SessionLocal()
    
    try:
        init_system_tags_for_user(db, user_id)
        db.commit()
        logger.info(f"新用户 {user_id} 的系统标签初始化完成")
        
    except Exception as e:
        db.rollback()
        logger.error(f"为新用户 {user_id} 初始化系统标签失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # 直接运行时，为所有用户初始化系统标签
    logging.basicConfig(level=logging.INFO)
    init_system_tags_for_all_users()
    print("✅ 系统预设标签初始化完成！")



