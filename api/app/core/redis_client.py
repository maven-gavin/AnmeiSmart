"""
Redis客户端配置 - 提供Redis连接实例
"""
import logging
import os
import redis.asyncio as aioredis
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

# Redis连接配置（从环境变量读取）
REDIS_URL = os.getenv("REDIS_URL")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

class RedisClient:
    """Redis客户端管理器"""
    
    def __init__(self):
        self._client: Optional[aioredis.Redis] = None
    
    async def get_client(self) -> aioredis.Redis:
        """获取Redis客户端实例"""
        if self._client is None:
            try:
                # 优先使用REDIS_URL，如果不存在则使用分离的配置参数
                if REDIS_URL:
                    self._client = aioredis.from_url(
                        REDIS_URL, 
                        decode_responses=True,
                        socket_keepalive=True,
                        socket_keepalive_options={},
                        health_check_interval=30
                    )
                    logger.info(f"使用REDIS_URL连接: {REDIS_URL.split('@')[0]}@***")
                else:
                    # 使用分离的配置参数
                    self._client = aioredis.Redis(
                        host=REDIS_HOST,
                        port=REDIS_PORT,
                        password=REDIS_PASSWORD,
                        db=REDIS_DB,
                        decode_responses=True,
                        socket_keepalive=True,
                        socket_keepalive_options={},
                        health_check_interval=30
                    )
                    logger.info(f"使用分离配置连接Redis: {REDIS_HOST}:{REDIS_PORT}")
                
                # 测试连接
                await self._client.ping()
                logger.info("Redis连接成功建立")
            except Exception as e:
                logger.error(f"Redis连接失败: {e}")
                # 提供详细的错误信息和配置检查建议
                if not REDIS_URL and not REDIS_HOST:
                    logger.error("请在.env文件中配置REDIS_URL或REDIS_HOST等Redis连接参数")
                raise
        
        return self._client
    
    async def close(self):
        """关闭Redis连接"""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Redis连接已关闭")

# 全局Redis客户端实例
redis_manager = RedisClient()

async def get_redis_client() -> aioredis.Redis:
    """依赖注入函数：获取Redis客户端"""
    return await redis_manager.get_client() 