#!/usr/bin/env python
"""
数据库设置脚本
用于在PostgreSQL中创建数据库
"""
import sys
import os
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import urlparse

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.core.config import get_settings
    settings = get_settings()
except Exception as e:
    print(f"读取配置时出错: {str(e)}")
    print("请确保您已正确设置环境变量，或在项目根目录创建.env文件")
    print("示例环境变量设置:")
    print("-" * 50)
    print("DATABASE_URL=postgresql://postgres:difyai123456@localhost:5432/anmeismart")
    print("SECRET_KEY=your_secret_key_here")
    print("-" * 50)
    sys.exit(1)

def create_database():
    """创建PostgreSQL数据库"""
    try:
        # 提取数据库名称和连接信息
        db_url = settings.DATABASE_URL
        parsed_url = urlparse(db_url)
        
        db_name = parsed_url.path.strip('/')
        user = parsed_url.username
        password = parsed_url.password
        host = parsed_url.hostname
        port = parsed_url.port or 5432
        
        # 构建不带数据库名的连接字符串，连接到默认的postgres数据库
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/postgres"
        
        print(f"正在连接到PostgreSQL服务器: {host}:{port}")
        
        try:
            conn = psycopg2.connect(connection_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # 检查数据库是否存在
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
            exists = cursor.fetchone()
            
            if not exists:
                print(f"创建数据库 {db_name}...")
                cursor.execute(f"CREATE DATABASE {db_name}")
                print(f"数据库 {db_name} 创建成功!")
            else:
                print(f"数据库 {db_name} 已存在，跳过创建")
                
            cursor.close()
            conn.close()
            return True
            
        except psycopg2.OperationalError as e:
            print(f"无法连接到PostgreSQL服务器: {str(e)}")
            print("请确保PostgreSQL服务器已启动，并且连接信息正确")
            return False
            
    except Exception as e:
        print(f"创建数据库时出错: {str(e)}")
        return False

def main():
    """主函数"""
    print("-" * 50)
    print("安美智享智能医美服务系统 - 数据库初始化")
    print("-" * 50)
    
    print("\n开始设置数据库...\n")
    
    postgres_ok = create_database()
    
    print("\n数据库设置状态:")
    print(f"PostgreSQL: {'成功' if postgres_ok else '失败'}")
    
    if postgres_ok:
        print("\n所有数据库设置完成！您可以继续使用以下命令初始化数据库表和测试数据:")
        print("python scripts/init_db.py")
    else:
        print("\n数据库设置未完成。请修复上述错误后重试。")
        sys.exit(1)

if __name__ == "__main__":
    main() 