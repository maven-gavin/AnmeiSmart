#!/usr/bin/env python
"""
检查数据库中的表
"""
import os
import sys

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.base import engine
from sqlalchemy import inspect

def list_tables():
    """列出数据库中的所有表"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print("数据库中的表:")
    for i, table in enumerate(tables, 1):
        print(f"{i}. {table}")
    
    return tables

def main():
    """脚本入口点"""
    tables = list_tables()
    
    if not tables:
        print("\n数据库中没有表!")
    else:
        print(f"\n共找到 {len(tables)} 个表")

if __name__ == "__main__":
    main() 