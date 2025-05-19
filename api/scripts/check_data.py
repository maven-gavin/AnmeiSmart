#!/usr/bin/env python
"""
检查数据库中的数据
"""
import os
import sys

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.base import engine, SessionLocal
from app.db.models.user import User, Role

def check_roles():
    """检查角色表中的数据"""
    db = SessionLocal()
    try:
        roles = db.query(Role).all()
        
        print("\n角色表数据:")
        print("=" * 30)
        for role in roles:
            print(f"ID: {role.id}, 名称: {role.name}, 描述: {role.description}")
        
        print(f"\n共有 {len(roles)} 个角色")
    finally:
        db.close()

def check_users():
    """检查用户表中的数据"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        
        print("\n用户表数据:")
        print("=" * 30)
        for user in users:
            roles = [role.name for role in user.roles]
            print(f"ID: {user.id}, 邮箱: {user.email}, 用户名: {user.username}, 角色: {roles}")
        
        print(f"\n共有 {len(users)} 个用户")
    finally:
        db.close()

def main():
    """脚本入口点"""
    print("检查数据库中的数据...")
    check_roles()
    check_users()

if __name__ == "__main__":
    main() 