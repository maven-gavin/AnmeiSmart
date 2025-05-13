"""
修复 passlib 与最新版 bcrypt 之间的兼容性问题
"""
import sys
import bcrypt

# 检查 bcrypt 模块是否缺少 __about__ 属性
if not hasattr(bcrypt, '__about__'):
    # 添加缺失的属性
    bcrypt.__about__ = type('__about__', (), {'__version__': bcrypt.__version__})

# 打印调试信息
print(f"已应用 bcrypt 补丁: 版本 {bcrypt.__version__}") 