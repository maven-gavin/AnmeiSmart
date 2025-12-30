#!/usr/bin/env python
"""
安美智享智能服务系统 - 全套数据初始化脚本
用于一次性执行所有数据初始化步骤
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

# 获取当前脚本目录
SCRIPT_DIR = Path(__file__).parent.absolute()

def print_banner():
    """打印脚本横幅"""
    print("=" * 60)
    print("安美智享智能服务系统 - 全套数据初始化工具")
    print("=" * 60)
    print("\n此工具将按顺序执行所有数据初始化步骤。")
    print("\n执行过程:")
    print("1. 设置数据库 (setup_db.py)")
    print("2. 应用数据库迁移 (migration.py)")
    print("3. 初始化基础数据 (init_db.py)")
    print("4. 初始化系统扩展数据 (seed_db.py)")
    print("\n开始初始化...")

def run_script(script_name, args=None):
    """运行指定的脚本文件
    
    Args:
        script_name: 脚本文件名
        args: 命令行参数列表
    """
    script_path = SCRIPT_DIR / script_name
    print(f"\n正在执行: {script_name}")
    print("-" * 40)
    
    # 构建命令
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    # 使用Python解释器运行脚本，确保兼容性
    result = subprocess.run(cmd, check=False)
    
    if result.returncode != 0:
        print(f"\n{script_name} 执行失败，中止流程。")
        sys.exit(result.returncode)
    
    print(f"{script_name} 执行成功。")

def main():
    """脚本入口点"""
    # 命令行参数
    parser = argparse.ArgumentParser(description="数据库完整初始化")
    parser.add_argument("--skip-setup", action="store_true", help="跳过数据库创建步骤")
    parser.add_argument("--force", action="store_true", help="强制重新创建表结构")
    parser.add_argument("--migration-only", action="store_true", help="只执行迁移，不初始化数据")
    parser.add_argument("--fresh", action="store_true", help="完全重置：删除所有数据，重新开始")
    args = parser.parse_args()
    
    print_banner()
    
    try:
        # 1. 设置数据库 (如果不跳过)
        if not args.skip_setup:
            run_script("setup_db.py")
        
        # 2. 应用数据库迁移
        run_script("migration.py", ["upgrade"])
        
        # 如果只执行迁移，到此结束
        if args.migration_only:
            print("\n迁移完成，根据参数跳过数据初始化。")
            return
        
        # 3. 运行数据库初始化脚本
        init_args = []
        if args.force or args.fresh:
            init_args.append("--drop-all")
        run_script("init_db.py", init_args)
        
        # 4. 运行数据扩展初始化脚本
        seed_args = []
        if args.force or args.fresh:
            seed_args.append("--force")
        run_script("seed_db.py", seed_args)
        
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

if __name__ == "__main__":
    main() 