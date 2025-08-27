"""
在线状态管理器 - 负责用户在线状态管理
"""
import asyncio
import logging
from typing import Set, Optional
from datetime import datetime

from app.core.redis_client import RedisClient

logger = logging.getLogger(__name__)


class PresenceManager:
    """在线状态管理器 - 专注于用户在线状态管理"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis_client = redis_client
        self.online_users_key = "ws:online_users"
        
        # 本地在线用户缓存（提高性能）
        self._local_online_users: Set[str] = set()
        self._cache_lock = asyncio.Lock()
    
    async def add_user_to_online(self, user_id: str) -> bool:
        """将用户添加到在线列表，返回用户之前是否在线"""
        try:
            # 使用Redis SADD，返回1表示新添加，0表示已存在
            result = await self.redis_client.execute_command("SADD", self.online_users_key, user_id)
            was_online = result == 0  # 返回之前是否在线
            
            # 更新本地缓存
            async with self._cache_lock:
                self._local_online_users.add(user_id)
            
            logger.debug(f"用户添加到在线列表: {user_id}, 之前在线: {was_online}")
            return was_online
            
        except Exception as e:
            logger.error(f"添加用户到在线列表失败: {e}")
            return False
    
    async def remove_user_from_online(self, user_id: str) -> bool:
        """从在线列表移除用户，返回用户之前是否在线"""
        try:
            # 使用Redis SREM，返回1表示成功移除，0表示不存在
            result = await self.redis_client.execute_command("SREM", self.online_users_key, user_id)
            was_online = result == 1  # 返回之前是否在线
            
            # 更新本地缓存
            async with self._cache_lock:
                self._local_online_users.discard(user_id)
            
            logger.debug(f"用户从在线列表移除: {user_id}, 之前在线: {was_online}")
            return was_online
            
        except Exception as e:
            logger.error(f"从在线列表移除用户失败: {e}")
            return False
    
    async def is_user_online(self, user_id: str) -> bool:
        """检查用户是否在线"""
        try:
            # 先检查本地缓存
            async with self._cache_lock:
                if user_id in self._local_online_users:
                    return True
            
            # 如果本地缓存没有，检查Redis
            result = await self.redis_client.execute_command("SISMEMBER", self.online_users_key, user_id)
            is_online = bool(result)
            
            # 更新本地缓存
            async with self._cache_lock:
                if is_online:
                    self._local_online_users.add(user_id)
                else:
                    self._local_online_users.discard(user_id)
            
            return is_online
            
        except Exception as e:
            logger.error(f"检查用户在线状态失败: {e}")
            return False
    
    async def get_online_users(self) -> Set[str]:
        """获取所有在线用户列表"""
        try:
            result = await self.redis_client.execute_command("SMEMBERS", self.online_users_key)
            online_users = set(result) if result else set()
            
            # 更新本地缓存
            async with self._cache_lock:
                self._local_online_users = online_users.copy()
            
            return online_users
            
        except Exception as e:
            logger.error(f"获取在线用户列表失败: {e}")
            return set()
    
    async def get_online_user_count(self) -> int:
        """获取在线用户数量"""
        try:
            result = await self.redis_client.execute_command("SCARD", self.online_users_key)
            return int(result) if result else 0
            
        except Exception as e:
            logger.error(f"获取在线用户数量失败: {e}")
            return 0
    
    async def clear_all_online_users(self) -> int:
        """清空所有在线用户（用于系统重启等场景）"""
        try:
            result = await self.redis_client.execute_command("DEL", self.online_users_key)
            cleared_count = int(result) if result else 0
            
            # 清空本地缓存
            async with self._cache_lock:
                self._local_online_users.clear()
            
            logger.info(f"清空了 {cleared_count} 个在线用户")
            return cleared_count
            
        except Exception as e:
            logger.error(f"清空在线用户失败: {e}")
            return 0
    
    async def refresh_local_cache(self) -> int:
        """刷新本地缓存"""
        try:
            online_users = await self.get_online_users()
            async with self._cache_lock:
                self._local_online_users = online_users.copy()
            
            logger.debug(f"本地缓存已刷新，在线用户数: {len(online_users)}")
            return len(online_users)
            
        except Exception as e:
            logger.error(f"刷新本地缓存失败: {e}")
            return 0
    
    def get_local_online_users(self) -> Set[str]:
        """获取本地缓存的在线用户（不保证最新）"""
        return self._local_online_users.copy()
    
    async def cleanup_stale_users(self, active_user_ids: Set[str]) -> int:
        """清理不在活跃列表中的用户（用于清理僵尸用户）"""
        try:
            # 获取Redis中的所有在线用户
            all_online_users = await self.get_online_users()
            
            # 找出需要清理的用户
            stale_users = all_online_users - active_user_ids
            
            if not stale_users:
                return 0
            
            # 批量移除僵尸用户
            removed_count = 0
            for user_id in stale_users:
                if await self.remove_user_from_online(user_id):
                    removed_count += 1
            
            if removed_count > 0:
                logger.info(f"清理了 {removed_count} 个僵尸用户: {stale_users}")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"清理僵尸用户失败: {e}")
            return 0
    
    async def get_user_online_duration(self, user_id: str) -> Optional[float]:
        """获取用户在线时长（秒）"""
        try:
            # 这里可以实现更复杂的在线时长跟踪
            # 目前返回None表示不支持
            return None
            
        except Exception as e:
            logger.error(f"获取用户在线时长失败: {e}")
            return None
    
    async def get_online_statistics(self) -> dict:
        """获取在线状态统计信息"""
        try:
            total_online = await self.get_online_user_count()
            local_cache_size = len(self._local_online_users)
            
            return {
                "total_online_users": total_online,
                "local_cache_size": local_cache_size,
                "cache_hit_rate": local_cache_size / total_online if total_online > 0 else 0,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取在线状态统计失败: {e}")
            return {
                "total_online_users": 0,
                "local_cache_size": 0,
                "cache_hit_rate": 0,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
