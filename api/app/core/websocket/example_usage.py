"""
重构后的分布式连接管理器使用示例
"""
import asyncio
import logging
from typing import Dict, Any

from .redis_client import RedisClient, get_redis_manager
from .distributed_connection_manager import DistributedConnectionManager

logger = logging.getLogger(__name__)


async def example_usage():
    """使用示例"""
    
    # 1. 初始化Redis客户端
    redis_manager = get_redis_manager()
    
    # 2. 创建分布式连接管理器
    connection_manager = DistributedConnectionManager(
        redis_client=redis_manager,
        max_connections_per_user=5,      # 每个用户最多5个连接
        max_message_size=1024 * 1024,   # 消息最大1MB
        rate_limit_window=60,           # 频率限制窗口60秒
        rate_limit_max_messages=100     # 每分钟最多100条消息
    )
    
    try:
        # 3. 初始化管理器
        await connection_manager.initialize()
        logger.info("分布式连接管理器初始化成功")
        
        # 4. 模拟用户连接
        # 注意：这里只是示例，实际使用时需要通过WebSocket连接
        
        # 5. 发送消息示例
        await connection_manager.send_to_user("user123", {
            "event": "notification",
            "data": "您有一条新消息",
            "timestamp": "2024-01-01T12:00:00"
        })
        
        # 6. 发送到特定设备类型
        await connection_manager.send_to_device_type("user123", "mobile", {
            "event": "alert",
            "data": "移动端专用通知",
            "priority": "high"
        })
        
        # 7. 检查用户在线状态
        is_online = await connection_manager.is_user_online("user123")
        logger.info(f"用户user123在线状态: {is_online}")
        
        # 8. 获取在线用户列表
        online_users = await connection_manager.get_online_users()
        logger.info(f"在线用户数量: {len(online_users)}")
        
        # 9. 获取系统统计信息
        stats = await connection_manager.get_statistics()
        logger.info(f"系统统计: {stats}")
        
        # 10. 等待一段时间观察运行状态
        await asyncio.sleep(10)
        
    except Exception as e:
        logger.error(f"使用示例出错: {e}")
    
    finally:
        # 11. 清理资源
        await connection_manager.cleanup()
        await redis_manager.close()
        logger.info("资源清理完成")


async def example_with_error_handling():
    """带错误处理的使用示例"""
    
    redis_manager = get_redis_manager()
    connection_manager = DistributedConnectionManager(redis_manager)
    
    try:
        await connection_manager.initialize()
        
        # 测试消息大小限制
        try:
            large_message = {"data": "x" * (1024 * 1024 + 1)}  # 超过1MB
            await connection_manager.send_to_user("user123", large_message)
        except Exception as e:
            logger.info(f"预期的消息大小限制: {e}")
        
        # 测试频率限制
        try:
            for i in range(150):  # 超过100条消息限制
                await connection_manager.send_to_user("user123", {
                    "event": "test",
                    "data": f"消息 {i}"
                })
        except Exception as e:
            logger.info(f"预期的频率限制: {e}")
        
        # 测试连接数量限制
        # 注意：这里只是示例，实际需要真实的WebSocket连接
        
    except Exception as e:
        logger.error(f"错误处理示例出错: {e}")
    
    finally:
        await connection_manager.cleanup()
        await redis_manager.close()


async def example_monitoring():
    """监控示例"""
    
    redis_manager = get_redis_manager()
    connection_manager = DistributedConnectionManager(redis_manager)
    
    try:
        await connection_manager.initialize()
        
        # 定期监控系统状态
        for i in range(5):
            stats = await connection_manager.get_statistics()
            logger.info(f"监控周期 {i+1}: {stats}")
            await asyncio.sleep(2)
        
    except Exception as e:
        logger.error(f"监控示例出错: {e}")
    
    finally:
        await connection_manager.cleanup()
        await redis_manager.close()


if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    
    # 运行示例
    asyncio.run(example_usage())
    asyncio.run(example_with_error_handling())
    asyncio.run(example_monitoring())
