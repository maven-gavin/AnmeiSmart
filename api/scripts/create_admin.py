#!/usr/bin/env python
"""
创建管理员账号脚本
根据 LoginForm.tsx 中的信息创建管理员账号
"""

import os
import sys

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 先导入 bcrypt 补丁修复 passlib 问题
from app.core.bcrypt_patch import *

import logging
from sqlalchemy.orm import Session

from app.identity_access.models.user import User, Role, Administrator
from app.identity_access.enums import AdminLevel
from app.db.base import get_db, engine
from app.core.password_utils import get_password_hash
from app.db.uuid_utils import user_id

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_admin_user():
    """创建管理员账号"""
    
    # 管理员账号信息（来自 LoginForm.tsx）
    admin_email = "admin@anmeismart.com"
    admin_password = "Admin@123456"
    admin_username = "系统管理员"
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 检查管理员账号是否已存在
        existing_user = db.query(User).filter(User.email == admin_email).first()
        if existing_user:
            logger.info(f"管理员账号 {admin_email} 已存在")
            return existing_user
        
        # 检查administrator角色是否存在
        admin_role = db.query(Role).filter(Role.name == "administrator").first()
        if not admin_role:
            logger.info("创建administrator角色")
            admin_role = Role(
                name="administrator",
                description="系统管理员角色"
            )
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
        
        # 创建管理员用户
        logger.info(f"创建管理员账号: {admin_email}")
        admin_user = User(
            id=user_id(),
            email=admin_email,
            username=admin_username,
            hashed_password=get_password_hash(admin_password),
            phone=None,
            avatar="/avatars/default.png",
            is_active=True
        )
        
        # 分配admin角色
        admin_user.roles = [admin_role]
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # 创建管理员扩展信息
        logger.info("创建管理员扩展信息")
        administrator = Administrator(
            user_id=admin_user.id,
            admin_level=AdminLevel.SUPER,  # 使用枚举值，表示超级管理员级别
            access_permissions="全局系统管理权限"
        )
        
        db.add(administrator)
        db.commit()
        
        logger.info(f"管理员账号创建成功!")
        logger.info(f"邮箱: {admin_email}")
        logger.info(f"密码: {admin_password}")
        logger.info(f"用户名: {admin_username}")
        
        return admin_user
        
    except Exception as e:
        logger.error(f"创建管理员账号时出错: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """主函数"""
    print("=" * 60)
    print("安美智享智能医美服务系统 - 创建管理员账号")
    print("=" * 60)
    print()
    
    try:
        admin_user = create_admin_user()
        print("✅ 管理员账号创建完成!")
        print(f"   邮箱: admin@anmeismart.com")
        print(f"   密码: Admin@123456")
        print(f"   用户名: 系统管理员")
        print()
        print("现在你可以使用此账号登录系统了。")
        
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 