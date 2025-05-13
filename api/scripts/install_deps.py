#!/usr/bin/env python
"""
安美智享智能医美服务系统 - 依赖安装脚本
此脚本帮助用户手动安装关键依赖
"""
import sys
import subprocess
import platform
import os

def print_header():
    print("\n" + "=" * 60)
    print("安美智享智能医美服务系统 - 依赖安装助手")
    print("=" * 60)

def run_command(command):
    """运行命令并返回结果"""
    try:
        process = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return True, process.stdout
    except subprocess.CalledProcessError as e:
        return False, f"错误: {e.stderr}"

def install_package(package, version=None):
    """安装指定的包"""
    package_spec = package
    if version:
        package_spec = f"{package}=={version}"
    
    print(f"\n正在安装 {package_spec}...")
    command = f"{sys.executable} -m pip install {package_spec} -v"
    
    success, output = run_command(command)
    if success:
        print(f"✓ {package_spec} 安装成功!")
    else:
        print(f"✗ 安装 {package_spec} 失败")
        print(output)
    
    return success

def check_package_installed(package):
    """检查包是否已安装"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def install_pymongo():
    """尝试安装pymongo，如果失败则尝试不同版本"""
    versions = ["4.0.1", "3.12.0", "3.11.0"]
    
    # 如果已经安装，则返回
    if check_package_installed("pymongo"):
        try:
            import pymongo
            print(f"✓ pymongo已安装，版本: {pymongo.__version__}")
            return True
        except:
            print("pymongo已安装但无法导入")
    
    # 尝试安装最新版本
    print("\n尝试安装pymongo...")
    if install_package("pymongo"):
        return True
    
    # 如果失败，尝试安装特定版本
    for version in versions:
        print(f"\n尝试安装pymongo {version}...")
        if install_package("pymongo", version):
            return True
    
    print("\n无法安装pymongo，尝试安装替代选项：motor")
    return install_package("motor")

def install_psycopg2():
    """尝试安装psycopg2，如果失败则尝试二进制版本"""
    if check_package_installed("psycopg2"):
        try:
            import psycopg2
            print(f"✓ psycopg2已安装")
            return True
        except:
            print("psycopg2已安装但无法导入")
    
    # 尝试安装psycopg2
    if install_package("psycopg2"):
        return True
    
    # 如果失败，尝试安装二进制版本
    print("\n尝试安装psycopg2-binary...")
    return install_package("psycopg2-binary")

def install_key_packages():
    """安装关键包"""
    key_packages = [
        ("fastapi", None),
        ("pydantic", "2.0.3"),  # 指定一个稳定版本
        ("uvicorn", None),
        ("python-jose[cryptography]", None),
        ("passlib[bcrypt]", None),
        ("python-multipart", None),
        ("python-dotenv", None)
    ]
    
    success_count = 0
    for package, version in key_packages:
        if install_package(package, version):
            success_count += 1
    
    # 安装数据库驱动
    if install_pymongo():
        success_count += 1
    
    if install_psycopg2():
        success_count += 1
    
    return success_count == len(key_packages) + 2  # +2是因为pymongo和psycopg2是分开处理的

def main():
    """主函数"""
    print_header()
    print("\n此脚本将帮助您安装项目所需的关键依赖。")
    print("这对于解决pymongo和psycopg2等常见安装问题非常有用。")
    
    # 检查pip
    print("\n检查pip...")
    success, output = run_command(f"{sys.executable} -m pip --version")
    if not success:
        print("✗ 未检测到pip，请先安装pip")
        sys.exit(1)
    else:
        print(f"✓ {output.strip()}")
    
    # 升级pip
    print("\n升级pip...")
    success, _ = run_command(f"{sys.executable} -m pip install --upgrade pip")
    if success:
        print("✓ pip已升级到最新版本")
    
    # 安装关键包
    print("\n开始安装关键依赖...")
    if install_key_packages():
        print("\n✓ 所有关键依赖安装成功!")
    else:
        print("\n✗ 部分依赖安装失败，请查看上面的错误信息。")
    
    print("\n安装完成后，您可以使用以下命令运行MongoDB连接测试:")
    print("python scripts/test_mongo.py")
    
    print("\n如果需要手动安装所有依赖，请使用:")
    print("pip install -r requirements.txt")

if __name__ == "__main__":
    main() 