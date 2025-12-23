#!/usr/bin/env python
"""
企业微信 Webhook 验证测试脚本
用于测试 webhook 验证端点是否正常工作
"""
import os
import sys
import asyncio
import logging
import httpx
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_webhook_verify():
    """测试 Webhook 验证端点"""
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    webhook_url = f"{base_url}/api/v1/channels/webhook/wechat-work"
    
    # 从环境变量读取配置
    token = os.getenv("WECHAT_WORK_TOKEN", "")
    encoding_aes_key = os.getenv("WECHAT_WORK_ENCODING_AES_KEY", "")
    
    logger.info("=" * 60)
    logger.info("企业微信 Webhook 验证测试")
    logger.info("=" * 60)
    logger.info(f"Webhook URL: {webhook_url}")
    logger.info(f"Token: {token[:10] + '...' if token else '未配置'}")
    logger.info(f"EncodingAESKey: {'已配置' if encoding_aes_key else '未配置'}")
    logger.info("")
    
    # 测试参数（模拟企业微信的验证请求）
    test_params = {
        "msg_signature": "test_signature_1234567890abcdef",
        "timestamp": "1234567890",
        "nonce": "test_nonce_12345",
        "echostr": "test_echo_string_12345"
    }
    
    try:
        logger.info("📡 发送测试请求...")
        logger.info(f"  参数: {test_params}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(webhook_url, params=test_params)
            
            logger.info("")
            logger.info(f"响应状态码: {response.status_code}")
            logger.info(f"响应内容: {response.text[:100]}")
            logger.info("")
            
            if response.status_code == 200:
                logger.info("✅ Webhook 端点可访问")
                logger.info("")
                logger.info("💡 注意：")
                logger.info("   - 如果配置了 EncodingAESKey，需要正确的签名才能解密")
                logger.info("   - 这个测试使用的是模拟参数，实际验证需要企业微信的真实请求")
                logger.info("   - 在企业微信管理后台配置 Webhook 时会自动发送验证请求")
                return True
            elif response.status_code == 403:
                logger.warning("⚠️  验证失败（403 Forbidden）")
                logger.info("   这可能是正常的，因为测试参数不是真实的签名")
                logger.info("   请在企业微信管理后台进行真实验证")
                return True  # 403 表示端点存在，只是验证失败
            elif response.status_code == 500:
                logger.error("❌ 服务器内部错误")
                logger.error(f"   错误信息: {response.text}")
                return False
            else:
                logger.warning(f"⚠️  意外的状态码: {response.status_code}")
                return False
                
    except httpx.ConnectError:
        logger.error("❌ 无法连接到服务器")
        logger.error(f"   请确保后端服务正在运行: {base_url}")
        logger.info("")
        logger.info("启动命令:")
        logger.info("  cd api")
        logger.info("  source venv/bin/activate")
        logger.info("  python run_dev.py")
        return False
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False


async def test_real_webhook():
    """测试真实的企业微信 Webhook 配置"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("真实 Webhook 配置检查")
    logger.info("=" * 60)
    
    # 检查必要的环境变量
    required_vars = [
        "WECHAT_WORK_CORP_ID",
        "WECHAT_WORK_AGENT_ID", 
        "WECHAT_WORK_SECRET",
        "WECHAT_WORK_TOKEN",
        "WECHAT_WORK_ENCODING_AES_KEY"
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            logger.info(f"✅ {var}: {value[:20]}...")
    
    if missing:
        logger.error("")
        logger.error("❌ 缺少以下环境变量:")
        for var in missing:
            logger.error(f"   - {var}")
        logger.error("")
        logger.error("请在 .env 文件中配置这些变量")
        return False
    
    logger.info("")
    logger.info("✅ 所有必要的环境变量已配置")
    logger.info("")
    logger.info("📝 下一步:")
    logger.info("   1. 确保后端服务正在运行")
    logger.info("   2. 确保 FRP 内网穿透已配置并运行")
    logger.info("   3. 在企业微信管理后台配置 Webhook URL")
    logger.info("   4. 点击保存，企业微信会自动发送验证请求")
    logger.info("")
    
    return True


def main():
    """主函数"""
    # 测试端点可访问性
    endpoint_ok = asyncio.run(test_webhook_verify())
    
    # 检查配置
    config_ok = asyncio.run(test_real_webhook())
    
    # 总结
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    logger.info(f"端点测试: {'✅ 通过' if endpoint_ok else '❌ 失败'}")
    logger.info(f"配置检查: {'✅ 通过' if config_ok else '❌ 失败'}")
    logger.info("")
    
    if endpoint_ok and config_ok:
        logger.info("🎉 可以开始在企业微信管理后台配置 Webhook 了！")
        return 0
    else:
        logger.warning("⚠️  请先解决上述问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())

