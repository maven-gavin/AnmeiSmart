#!/usr/bin/env python3
"""
测试安全模块重构后的功能

验证重构后的安全模块是否正常工作。
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

def test_imports():
    """测试导入是否正常"""
    try:
        print("测试导入...")
        
        # 测试向后兼容性导入
        from app.core.security import (
            get_current_user,
            get_current_admin,
            check_role_permission,
            verify_token,
            create_access_token,
            create_refresh_token
        )
        print("✓ 向后兼容性导入成功")
        
        # 测试新的DDD架构模块
        from app.identity_access.infrastructure.jwt_service import JWTService
        print("✓ JWT服务导入成功")
        
        from app.identity_access.domain.security_domain_service import SecurityDomainService
        print("✓ 安全领域服务导入成功")
        
        from app.identity_access.application.security_application_service import SecurityApplicationService
        print("✓ 安全应用服务导入成功")
        
        from app.identity_access.deps.security_deps import (
            get_jwt_service,
            get_security_domain_service,
            get_security_application_service
        )
        print("✓ 安全依赖注入导入成功")
        
        return True
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 其他错误: {e}")
        return False

def test_jwt_service():
    """测试JWT服务功能"""
    try:
        print("\n测试JWT服务...")
        
        from app.identity_access.infrastructure.jwt_service import JWTService
        
        jwt_service = JWTService()
        
        # 测试创建令牌
        token = jwt_service.create_access_token("test-user-id", active_role="customer")
        print(f"✓ 创建访问令牌成功: {token[:20]}...")
        
        # 测试验证令牌
        payload = jwt_service.verify_token(token)
        if payload and payload.get("sub") == "test-user-id":
            print("✓ 验证令牌成功")
        else:
            print("✗ 验证令牌失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ JWT服务测试失败: {e}")
        return False

def test_backward_compatibility():
    """测试向后兼容性"""
    try:
        print("\n测试向后兼容性...")
        
        from app.core.security import create_access_token, verify_token
        
        # 测试创建令牌
        token = create_access_token("test-user-id", active_role="customer")
        print(f"✓ 向后兼容创建令牌成功: {token[:20]}...")
        
        # 测试验证令牌
        user_id = verify_token(token)
        if user_id == "test-user-id":
            print("✓ 向后兼容验证令牌成功")
        else:
            print("✗ 向后兼容验证令牌失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 向后兼容性测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试安全模块重构...")
    print("=" * 50)
    
    tests = [
        ("导入测试", test_imports),
        ("JWT服务测试", test_jwt_service),
        ("向后兼容性测试", test_backward_compatibility),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"✗ {test_name}失败")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！重构成功！")
        return 0
    else:
        print("❌ 部分测试失败，需要检查")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
