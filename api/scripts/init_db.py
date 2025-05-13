#!/usr/bin/env python
"""
数据库初始化脚本
用于创建数据库表和初始数据
"""
import asyncio
import sys
import os

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.db.init_db import main
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有必要的依赖已安装: pip install -r requirements.txt")
    sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("安美智享智能医美服务系统 - 数据库初始化工具")
    print("=" * 60)
    print("\n此工具将初始化数据库表结构和创建初始数据。")
    print("请确保已运行 setup_db.py 创建了数据库。")
    print("\n开始初始化...")
    
    try:
        main()
        print("\n初始化完成！您现在可以启动API服务:")
        print("cd .. && uvicorn main:app --reload")
    except Exception as e:
        print(f"\n初始化过程中发生错误: {e}")
        print("请检查配置和连接信息后重试。")
        sys.exit(1) 