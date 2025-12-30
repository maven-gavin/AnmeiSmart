#!/usr/bin/env python
"""
安美智享智能服务系统 - 安装指南
此脚本指导用户完成安装和配置步骤
"""
import os
import sys
import subprocess
import platform

def print_header():
    print("\n" + "=" * 60)
    print("安美智享智能服务系统 - 安装指南")
    print("=" * 60)

def print_step(step_num, description):
    print(f"\n步骤 {step_num}: {description}")
    print("-" * 40)

def check_python_version():
    print_step(1, "检查Python版本")
    version = sys.version_info
    required_version = (3, 9)
    
    if version >= required_version:
        print(f"✅ Python版本 {version.major}.{version.minor}.{version.micro} 满足要求")
        return True
    else:
        print(f"❌ 当前Python版本 {version.major}.{version.minor}.{version.micro} 过低")
        print(f"请安装Python {required_version[0]}.{required_version[1]} 或更高版本")
        return False

def check_dependencies():
    print_step(2, "检查必要的依赖")
    
    try:
        # 检查是否安装了pip
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, capture_output=True)
        print("✅ pip 已安装")
    except:
        print("❌ pip 未安装或无法访问")
        print("请安装pip后继续")
        return False
    
    required_packages = {
        "PostgreSQL": "psycopg2",
        "FastAPI": "fastapi",
        "Uvicorn": "uvicorn"
    }
    
    missing_packages = []
    
    for name, package in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {name} 相关依赖已安装")
        except ImportError:
            print(f"❌ {name} 相关依赖未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print("\n需要安装以下依赖:")
        for package in missing_packages:
            print(f"  - {package}")
        
        print("\n请使用以下命令安装所有依赖:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def check_database_config():
    print_step(3, "检查数据库配置")
    
    # 检查环境变量或.env文件
    required_vars = ["DATABASE_URL", "SECRET_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            # 检查.env文件
            env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
            if os.path.exists(env_file):
                with open(env_file, "r") as f:
                    content = f.read()
                    if f"{var}=" not in content:
                        missing_vars.append(var)
            else:
                missing_vars.append(var)
    
    if missing_vars:
        print("❌ 缺少以下必要的环境变量:")
        for var in missing_vars:
            print(f"  - {var}")
        
        print("\n请创建一个.env文件在项目根目录下，包含以下内容:")
        print("DATABASE_URL=postgresql://用户名:密码@localhost:5432/AnmeiSmart")
        print("SECRET_KEY=your_secret_key_here")
        return False
    
    print("✅ 环境变量设置完成")
    return True

def check_database_connection():
    print_step(4, "检查数据库连接")
    
    print("\n要检查数据库连接，请运行以下命令:")
    print("python scripts/setup_db.py")
    
    print("\n该命令将尝试连接到PostgreSQL，并创建必要的数据库。")
    return True

def initialize_database():
    print_step(5, "初始化数据库")
    
    print("\n要初始化数据库表和测试数据，请运行以下命令:")
    print("python scripts/init_db.py")
    
    print("\n该命令将创建所有必要的表，并添加默认角色和测试用户。")
    return True

def start_application():
    print_step(6, "启动应用")
    
    print("\n要启动API服务，请运行以下命令:")
    print("cd .. && uvicorn main:app --reload")
    
    print("\n启动后，您可以在浏览器中访问以下地址查看API文档:")
    print("http://localhost:8000/api/v1/docs")
    return True

def check_common_issues():
    print_step(7, "常见问题与解决方案")
    
    print("\n1. 无法连接到数据库")
    print("   - 确保PostgreSQL服务已启动")
    print("   - 检查用户名和密码是否正确")
    print("   - 确认主机名和端口是否可访问")
    
    print("\n2. 依赖安装失败")
    print("   - 尝试手动安装特定版本: pip install pydantic==2.0.0")
    print("   - 如遇psycopg2安装问题，尝试使用二进制包: pip install psycopg2-binary")
    
    print("\n3. JWT认证失败")
    print("   - 确保SECRET_KEY已正确设置")
    print("   - 检查token是否有效且未过期")
    
    return True

def run_installation_guide():
    """运行完整的安装指南"""
    print_header()
    
    print("\n欢迎使用安美智享智能服务系统安装指南！")
    print("此脚本将指导您完成系统的安装和配置过程。")
    
    steps = [
        check_python_version,
        check_dependencies,
        check_database_config,
        check_database_connection,
        initialize_database,
        start_application,
        check_common_issues
    ]
    
    for step_func in steps:
        result = step_func()
        if not result:
            print("\n请解决上述问题后再继续。")
            input("按任意键继续...")
    
    print("\n" + "=" * 60)
    print("安装指南已完成！")
    print("如遇任何问题，请参考API/README.md或联系开发团队。")
    print("=" * 60)

if __name__ == "__main__":
    run_installation_guide() 