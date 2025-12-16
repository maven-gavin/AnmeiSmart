#!/usr/bin/env python
"""
企业微信配置测试脚本
用于验证企业微信配置是否正确
"""
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_wechat_work_config():
    """测试企业微信配置"""
    from app.channels.adapters.wechat_work.client import WeChatWorkClient
    
    # 从环境变量读取配置
    corp_id = os.getenv("WECHAT_WORK_CORP_ID")
    agent_id = os.getenv("WECHAT_WORK_AGENT_ID")
    secret = os.getenv("WECHAT_WORK_SECRET")
    token = os.getenv("WECHAT_WORK_TOKEN")
    encoding_aes_key = os.getenv("WECHAT_WORK_ENCODING_AES_KEY")
    
    # 检查配置是否完整
    missing_configs = []
    if not corp_id:
        missing_configs.append("WECHAT_WORK_CORP_ID")
    if not agent_id:
        missing_configs.append("WECHAT_WORK_AGENT_ID")
    if not secret:
        missing_configs.append("WECHAT_WORK_SECRET")
    if not token:
        missing_configs.append("WECHAT_WORK_TOKEN")
    if not encoding_aes_key:
        missing_configs.append("WECHAT_WORK_ENCODING_AES_KEY")
    
    if missing_configs:
        logger.error(f"❌ 缺少以下环境变量配置: {', '.join(missing_configs)}")
        logger.info("请在 .env 文件中添加这些配置")
        return False
    
    logger.info("✅ 所有环境变量配置已设置")
    logger.info(f"  - CorpID: {corp_id[:10]}...")
    logger.info(f"  - AgentID: {agent_id}")
    logger.info(f"  - Secret: {secret[:10]}...")
    logger.info(f"  - Token: {token[:10]}...")
    logger.info(f"  - EncodingAESKey: {encoding_aes_key[:10]}...")
    
    # 测试 API 客户端
    try:
        logger.info("\n📡 测试获取 Access Token...")
        client = WeChatWorkClient(
            corp_id=corp_id,
            agent_id=agent_id,
            secret=secret
        )
        
        access_token = await client.get_access_token()
        logger.info(f"✅ 成功获取 Access Token: {access_token[:20]}...")
        
        # 测试发送消息（需要提供真实的用户ID）
        test_user_id = os.getenv("WECHAT_WORK_TEST_USER_ID")
        if test_user_id:
            logger.info(f"\n📤 测试发送消息到用户: {test_user_id}")
            success = await client.send_text_message(test_user_id, "这是一条测试消息")
            if success:
                logger.info("✅ 消息发送成功")
            else:
                logger.warning("⚠️  消息发送失败，请检查用户ID是否正确")
        else:
            logger.info("\n💡 提示: 设置 WECHAT_WORK_TEST_USER_ID 环境变量可以测试消息发送功能")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False


async def test_webhook_endpoint():
    """测试 Webhook 端点配置"""
    import httpx
    
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    webhook_url = f"{base_url}/api/v1/channels/webhook/wechat-work"
    
    logger.info(f"\n🔗 测试 Webhook 端点: {webhook_url}")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 测试 GET 请求（验证端点）
            response = await client.get(
                webhook_url,
                params={
                    "msg_signature": "test",
                    "timestamp": "1234567890",
                    "nonce": "test",
                    "echostr": "test_echo"
                }
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Webhook 端点可访问，响应: {response.text[:50]}")
            else:
                logger.warning(f"⚠️  Webhook 端点返回状态码: {response.status_code}")
                
    except httpx.ConnectError:
        logger.error(f"❌ 无法连接到服务器: {base_url}")
        logger.info("请确保后端服务正在运行")
        return False
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        return False
    
    return True


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("企业微信配置测试")
    logger.info("=" * 60)
    
    # 测试配置
    config_ok = asyncio.run(test_wechat_work_config())
    
    # 测试 Webhook 端点
    webhook_ok = asyncio.run(test_webhook_endpoint())
    
    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("测试结果总结")
    logger.info("=" * 60)
    logger.info(f"配置测试: {'✅ 通过' if config_ok else '❌ 失败'}")
    logger.info(f"Webhook测试: {'✅ 通过' if webhook_ok else '❌ 失败'}")
    
    if config_ok and webhook_ok:
        logger.info("\n🎉 所有测试通过！可以开始使用企业微信集成功能了")
        return 0
    else:
        logger.error("\n⚠️  部分测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    sys.exit(main())

