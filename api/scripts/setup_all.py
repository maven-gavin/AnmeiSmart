#!/usr/bin/env python
"""
安美智享智能医美服务系统 - 全套数据初始化脚本
用于一次性执行所有数据初始化步骤
"""
import os
import sys
import subprocess
from pathlib import Path

# 获取当前脚本目录
SCRIPT_DIR = Path(__file__).parent.absolute()

def print_banner():
    """打印脚本横幅"""
    print("=" * 60)
    print("安美智享智能医美服务系统 - 全套数据初始化工具")
    print("=" * 60)
    print("\n此工具将按顺序执行所有数据初始化步骤。")
    print("\n执行过程:")
    print("1. 初始化数据库表和基础数据 (init_db.py)")
    print("2. 初始化系统扩展数据 (seed_db.py)")
    print("\n开始初始化...")

def run_script(script_name):
    """运行指定的脚本文件"""
    script_path = SCRIPT_DIR / script_name
    print(f"\n正在执行: {script_name}")
    print("-" * 40)
    
    # 使用Python解释器运行脚本，确保兼容性
    result = subprocess.run([sys.executable, str(script_path)], check=False)
    
    if result.returncode != 0:
        print(f"\n{script_name} 执行失败，中止流程。")
        sys.exit(result.returncode)
    
    print(f"{script_name} 执行成功。")

if __name__ == "__main__":
    print_banner()
    
    try:
        # 1. 运行数据库初始化脚本
        run_script("init_db.py")
        
        # 2. 运行数据扩展初始化脚本
        run_script("seed_db.py")
        
        print("\n=" * 60)
        print("所有初始化步骤已完成！系统数据初始化成功。")
        print("现在可以启动API服务: cd .. && uvicorn main:app --reload")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n初始化过程被用户中断。")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n初始化过程中发生未知错误: {e}")
        sys.exit(1) 