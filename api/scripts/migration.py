#!/usr/bin/env python
"""
数据库迁移脚本
用于管理和应用数据库迁移
"""

import os
import sys
import subprocess
import argparse
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_alembic_command(command_args):
    """运行alembic命令
    
    Args:
        command_args: alembic命令参数列表
    """
    try:
        # 确保在api目录下运行
        os.chdir(os.path.dirname(os.path.dirname(__file__)))
        
        # 构建完整命令
        cmd = [sys.executable, "-m", "alembic"] + command_args
        
        logger.info(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
            
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Alembic命令执行失败: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据库迁移管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # upgrade命令
    upgrade_parser = subparsers.add_parser('upgrade', help='应用迁移到指定版本')
    upgrade_parser.add_argument('revision', nargs='?', default='head', help='目标版本 (默认: head)')
    
    # downgrade命令
    downgrade_parser = subparsers.add_parser('downgrade', help='回退到指定版本')
    downgrade_parser.add_argument('revision', help='目标版本')
    
    # current命令
    current_parser = subparsers.add_parser('current', help='显示当前版本')
    
    # history命令
    history_parser = subparsers.add_parser('history', help='显示迁移历史')
    
    # revision命令
    revision_parser = subparsers.add_parser('revision', help='创建新的迁移')
    revision_parser.add_argument('-m', '--message', required=True, help='迁移描述')
    revision_parser.add_argument('--autogenerate', action='store_true', help='自动生成迁移内容')
    
    # stamp命令
    stamp_parser = subparsers.add_parser('stamp', help='标记当前数据库版本')
    stamp_parser.add_argument('revision', help='要标记的版本')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 根据命令执行相应操作
    if args.command == 'upgrade':
        success = run_alembic_command(['upgrade', args.revision])
    elif args.command == 'downgrade':
        success = run_alembic_command(['downgrade', args.revision])
    elif args.command == 'current':
        success = run_alembic_command(['current'])
    elif args.command == 'history':
        success = run_alembic_command(['history'])
    elif args.command == 'revision':
        cmd_args = ['revision', '-m', args.message]
        if args.autogenerate:
            cmd_args.append('--autogenerate')
        success = run_alembic_command(cmd_args)
    elif args.command == 'stamp':
        success = run_alembic_command(['stamp', args.revision])
    else:
        logger.error(f"未知命令: {args.command}")
        success = False
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 