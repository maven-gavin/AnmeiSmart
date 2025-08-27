"""
Redis客户端配置 - 提供Redis连接实例和连接池管理
"""
import logging
import os
import asyncio
import functools
from typing import Optional, Any, Callable
import redis.asyncio as aioredis
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

# 连接池配置
REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
REDIS_RETRY_ATTEMPTS = int(os.getenv("REDIS_RETRY_ATTEMPTS", "3"))
REDIS_RETRY_DELAY = float(os.getenv("REDIS_RETRY_DELAY", "1.0"))


def redis_retry(max_attempts: int = REDIS_RETRY_ATTEMPTS, delay: float = REDIS_RETRY_DELAY):
    """Redis操作重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (aioredis.ConnectionError, aioredis.TimeoutError) as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Redis操作失败，尝试重试 {attempt + 1}/{max_attempts}: {e}")
                        await asyncio.sleep(delay * (attempt + 1))  # 指数退避
                    else:
                        logger.error(f"Redis操作最终失败: {e}")
                        raise
                except Exception as e:
                    logger.error(f"Redis操作异常: {e}")
                    raise
            if last_exception is not None:
                raise last_exception
        return wrapper
    return decorator


class RedisClient:
    """Redis客户端管理器 - 支持连接池、重试机制和健康检查"""
    
    def __init__(self):
        self._client: Optional[aioredis.Redis] = None
        self._connection_pool: Optional[aioredis.ConnectionPool] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._is_healthy = False
    
    async def get_client(self) -> aioredis.Redis:
        """获取Redis客户端实例（单例模式）"""
        if self._client is None:
            await self._initialize_client()
        if self._client is None:
            raise RuntimeError("Redis客户端初始化失败")
        return self._client
    
    async def _initialize_client(self):
        """初始化Redis客户端"""
        try:
            # 创建连接池
            if REDIS_URL:
                self._connection_pool = aioredis.ConnectionPool.from_url(
                    REDIS_URL,
                    max_connections=REDIS_MAX_CONNECTIONS,
                    decode_responses=True,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    health_check_interval=30
                )
                logger.info(f"使用REDIS_URL创建连接池: {REDIS_URL.split('@')[0]}@***")
            else:
                self._connection_pool = aioredis.ConnectionPool(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    password=REDIS_PASSWORD,
                    db=REDIS_DB,
                    max_connections=REDIS_MAX_CONNECTIONS,
                    decode_responses=True,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    health_check_interval=30
                )
                logger.info(f"使用分离配置创建连接池: {REDIS_HOST}:{REDIS_PORT}")
            
            # 创建Redis客户端
            self._client = aioredis.Redis(connection_pool=self._connection_pool)
            
            # 测试连接
            await self._test_connection()
            
            # 启动健康检查
            self._start_health_check()
            
            logger.info("Redis客户端初始化成功")
            
        except Exception as e:
            logger.error(f"Redis客户端初始化失败: {e}")
            if not REDIS_URL and not REDIS_HOST:
                logger.error("请在.env文件中配置REDIS_URL或REDIS_HOST等Redis连接参数")
            raise
    
    @redis_retry()
    async def _test_connection(self):
        """测试Redis连接"""
        if self._client is None:
            raise RuntimeError("Redis客户端未初始化")
        await self._client.ping()
        self._is_healthy = True
        logger.info("Redis连接测试成功")
    
    def _start_health_check(self):
        """启动健康检查任务"""
        if self._health_check_task is None:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                if self._client is not None:
                    await self._client.ping()
                    if not self._is_healthy:
                        self._is_healthy = True
                        logger.info("Redis连接已恢复")
            except asyncio.CancelledError:
                logger.info("Redis健康检查已取消")
                break
            except Exception as e:
                if self._is_healthy:
                    self._is_healthy = False
                    logger.warning(f"Redis连接异常: {e}")
    
    @redis_retry()
    async def execute_command(self, command: str, *args, **kwargs) -> Any:
        """执行Redis命令（带重试）"""
        client = await self.get_client()
        return await client.execute_command(command, *args, **kwargs)
    
    @redis_retry()
    async def publish(self, channel: str, message: str) -> int:
        """发布消息到频道（带重试）"""
        client = await self.get_client()
        return await client.publish(channel, message)
    
    @redis_retry()
    async def subscribe(self, *channels: str):
        """订阅频道（带重试）"""
        client = await self.get_client()
        return await client.pubsub().subscribe(*channels)
    
    def is_healthy(self) -> bool:
        """检查Redis连接是否健康"""
        return self._is_healthy
    
    async def close(self):
        """关闭Redis连接和连接池"""
        try:
            # 停止健康检查
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            # 关闭客户端
            if self._client:
                await self._client.close()
                self._client = None
            
            # 关闭连接池
            if self._connection_pool:
                await self._connection_pool.disconnect()
                self._connection_pool = None
            
            self._is_healthy = False
            logger.info("Redis连接已关闭")
            
        except Exception as e:
            logger.error(f"关闭Redis连接失败: {e}")


# 全局Redis客户端实例
redis_manager = RedisClient()

async def get_redis_client() -> aioredis.Redis:
    """依赖注入函数：获取Redis客户端"""
    return await redis_manager.get_client()

async def get_redis_manager() -> RedisClient:
    """依赖注入函数：获取Redis管理器"""
    return redis_manager 