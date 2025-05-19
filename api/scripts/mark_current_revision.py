#!/usr/bin/env python
"""
标记当前数据库版本
"""
import os
import sys
import uuid

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()

def main():
    """脚本入口点"""
    # 生成一个随机的迁移版本ID
    revision_id = uuid.uuid4().hex[:12]
    print(f"使用迁移版本ID: {revision_id}")
    
    # 创建数据库连接
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM alembic_version"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:version)"), {"version": revision_id})
        conn.commit()
        print(f"成功标记当前版本为: {revision_id}")
    
    print("\n现在你可以使用此版本ID创建一个空白的迁移文件：")
    print(f"python scripts/migration.py create --message \"初始数据库状态\" --rev-id {revision_id}")

if __name__ == "__main__":
    main() 