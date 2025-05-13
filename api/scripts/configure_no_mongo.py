#!/usr/bin/env python
"""
配置脚本 - 禁用MongoDB
此脚本修改配置，使系统只使用PostgreSQL，不需要MongoDB
"""
import sys
import os
import re
import shutil

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def print_header():
    print("\n" + "=" * 60)
    print("安美智享智能医美服务系统 - 禁用MongoDB配置工具")
    print("=" * 60)

def backup_file(file_path):
    """备份文件"""
    backup_path = file_path + ".bak"
    try:
        shutil.copy2(file_path, backup_path)
        print(f"✓ 已备份文件到: {backup_path}")
        return True
    except Exception as e:
        print(f"✗ 备份文件失败: {str(e)}")
        return False

def modify_config_file():
    """修改配置文件"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "core", "config.py")
    
    if not os.path.exists(config_path):
        print(f"✗ 配置文件不存在: {config_path}")
        return False
    
    print(f"找到配置文件: {config_path}")
    
    # 备份配置文件
    if not backup_file(config_path):
        return False
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 修改MongoDB配置
        content = re.sub(
            r'MONGODB_URL: str = "(.+?)"',
            'MONGODB_URL: str = ""  # 已禁用',
            content
        )
        
        # 添加MongoDB禁用标志
        if "MONGODB_ENABLED" not in content:
            content = content.replace(
                "class Settings(BaseSettings):",
                "class Settings(BaseSettings):\n    \"\"\"应用配置类\"\"\"\n    MONGODB_ENABLED: bool = False"
            )
        else:
            content = re.sub(
                r'MONGODB_ENABLED: bool = True',
                'MONGODB_ENABLED: bool = False',
                content
            )
        
        # 写回文件
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print("✓ 成功修改配置文件，已禁用MongoDB")
        return True
        
    except Exception as e:
        print(f"✗ 修改配置文件失败: {str(e)}")
        return False

def modify_db_base_file():
    """修改数据库基础文件"""
    db_base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "db", "base.py")
    
    if not os.path.exists(db_base_path):
        print(f"✗ 数据库基础文件不存在: {db_base_path}")
        return False
    
    print(f"找到数据库基础文件: {db_base_path}")
    
    # 备份文件
    if not backup_file(db_base_path):
        return False
    
    try:
        with open(db_base_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 修改MongoDB配置，添加条件检查
        modified_content = []
        lines = content.split("\n")
        in_mongodb_section = False
        
        for line in lines:
            if "# MongoDB配置" in line:
                in_mongodb_section = True
                modified_content.append(line)
                modified_content.append("if settings.MONGODB_ENABLED:")
                modified_content.append("    mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)")
                modified_content.append("    mongodb = mongodb_client.medical_beauty")
                modified_content.append("else:")
                modified_content.append("    mongodb_client = None")
                modified_content.append("    mongodb = None")
                modified_content.append("")
            elif in_mongodb_section and "mongodb_client = " in line:
                # 跳过这一行，因为我们已经添加了条件检查
                pass
            elif in_mongodb_section and "mongodb = " in line:
                # 跳过这一行，因为我们已经添加了条件检查
                in_mongodb_section = False
            else:
                modified_content.append(line)
        
        # 修改获取MongoDB函数
        content = "\n".join(modified_content)
        content = re.sub(
            r'async def get_mongodb\(\)(.+?)return mongodb',
            'async def get_mongodb():\n    """获取MongoDB客户端"""\n    if settings.MONGODB_ENABLED:\n        return mongodb\n    else:\n        print("警告: MongoDB已禁用，返回None")\n        return None',
            content,
            flags=re.DOTALL
        )
        
        # 写回文件
        with open(db_base_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print("✓ 成功修改数据库基础文件，添加了MongoDB禁用逻辑")
        return True
        
    except Exception as e:
        print(f"✗ 修改数据库基础文件失败: {str(e)}")
        return False

def create_env_file():
    """创建.env文件"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    
    try:
        # 检查文件是否存在
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # 备份文件
            backup_file(env_path)
            
            # 修改MongoDB相关配置
            if "MONGODB_URL=" in content:
                content = re.sub(
                    r'MONGODB_URL=(.+?)\n',
                    'MONGODB_URL=\n',
                    content
                )
            
            if "MONGODB_ENABLED=" not in content:
                content += "\nMONGODB_ENABLED=false\n"
            else:
                content = re.sub(
                    r'MONGODB_ENABLED=(.+?)\n',
                    'MONGODB_ENABLED=false\n',
                    content
                )
        else:
            # 创建新的.env文件
            content = """# 数据库配置
DATABASE_URL=postgresql://postgres:difyai123456@localhost:5432/AnmeiSmart
MONGODB_URL=
MONGODB_ENABLED=false

# JWT配置
SECRET_KEY=difyai123456
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 项目信息
PROJECT_NAME=安美智享智能医美服务系统
VERSION=1.0.0
"""
        
        # 写入文件
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"✓ 成功{'修改' if os.path.exists(env_path) else '创建'} .env 文件")
        return True
        
    except Exception as e:
        print(f"✗ {'修改' if os.path.exists(env_path) else '创建'} .env 文件失败: {str(e)}")
        return False

def main():
    """主函数"""
    print_header()
    
    print("\n此脚本将修改配置，使系统只使用PostgreSQL，不需要MongoDB。")
    print("这对于没有安装MongoDB或不需要非结构化数据存储的环境非常有用。")
    print("\n注意: 此操作将备份并修改配置文件，如需恢复，可以使用.bak文件。")
    
    # 询问用户是否继续
    try:
        response = input("\n确定要继续吗? (y/n): ").strip().lower()
        if response != "y":
            print("操作已取消")
            return
    except KeyboardInterrupt:
        print("\n操作已取消")
        return
    
    steps = [
        ("修改配置文件", modify_config_file),
        ("修改数据库基础文件", modify_db_base_file),
        ("更新环境变量文件", create_env_file)
    ]
    
    all_success = True
    
    for step_name, step_func in steps:
        print(f"\n正在{step_name}...")
        if not step_func():
            all_success = False
            print(f"✗ {step_name}失败")
        else:
            print(f"✓ {step_name}成功")
    
    if all_success:
        print("\n✓ 所有配置更改已完成，系统现在只使用PostgreSQL，不需要MongoDB。")
        print("\n您现在可以运行以下命令来初始化数据库:")
        print("python scripts/setup_db.py")
        print("python scripts/init_db.py")
    else:
        print("\n✗ 部分配置更改失败，请查看上面的错误信息。")
        print("您可以尝试手动修改配置文件，或者恢复备份文件。")

if __name__ == "__main__":
    main() 