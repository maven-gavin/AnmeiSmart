"""
Agent 对话应用服务
遵循 DDD 架构，协调领域逻辑和基础设施
"""

import logging
import json
from typing import Optional, Dict, Any, List, AsyncIterator
from datetime import datetime
from sqlalchemy.orm import Session

from app.ai.infrastructure.dify_agent_client import DifyAgentClientFactory, DifyAgentClient
from app.ai.schemas.agent_chat import (
    AgentMessageResponse,
    AgentConversationResponse
)
from app.chat.infrastructure.conversation_repository import ConversationRepository
from app.chat.infrastructure.message_repository import MessageRepository
from app.chat.infrastructure.db.chat import Conversation, Message
from app.websocket.broadcasting_service import BroadcastingService

logger = logging.getLogger(__name__)


class AgentChatApplicationService:
    """
    Agent 对话应用服务
    负责协调 Agent 对话的完整流程
    """
    
    def __init__(
        self,
        dify_client_factory: DifyAgentClientFactory,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        broadcasting_service: Optional[BroadcastingService],
        db: Session
    ):
        self.dify_client_factory = dify_client_factory
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.broadcasting_service = broadcasting_service
        self.db = db
    
    async def stream_chat(
        self,
        agent_config_id: str,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[bytes]:
        """
        流式对话主逻辑
        
        流程：
        1. 获取或创建会话
        2. 保存用户消息
        3. 调用 Dify Agent 获取流式响应
        4. 实时转发响应给前端
        5. 保存 AI 响应
        6. 通过 WebSocket 广播（可选）
        """
        dify_client: Optional[DifyAgentClient] = None
        ai_message_id: Optional[str] = None
        ai_content_buffer = ""
        dify_conversation_id: Optional[str] = None
        
        try:
            # 1. 创建 Dify 客户端
            dify_client = self.dify_client_factory.create_client_from_db(
                agent_config_id, self.db
            )
            
            # 2. 获取或创建会话
            if not conversation_id:
                conversation = await self._create_conversation(
                    agent_config_id=agent_config_id,
                    user_id=user_id,
                    title="新对话"
                )
                conversation_id = conversation.id
            else:
                conversation = await self.conversation_repo.get_by_id(conversation_id)
                if not conversation:
                    raise ValueError(f"会话不存在: {conversation_id}")
            
            # 3. 保存用户消息
            user_message = Message(
                id="",  # 由仓储生成
                conversation_id=conversation_id,
                content={"text": message},
                type="text",
                sender_id=user_id,
                sender_type="customer",
                is_read=True,
                timestamp=datetime.now()
            )
            await self.message_repo.save(user_message)
            
            # 4. 调用 Dify Agent 流式对话
            user_identifier = f"user_{user_id}"
            
            async for chunk in dify_client.stream_chat(
                message=message,
                user=user_identifier,
                conversation_id=None,  # 让 Dify 管理自己的会话ID
                inputs=inputs
            ):
                # 解析 SSE 事件
                chunk_str = chunk.decode('utf-8') if isinstance(chunk, bytes) else chunk
                
                # 直接转发给前端
                yield chunk
                
                # 解析并记录关键信息
                if chunk_str.startswith('data: '):
                    try:
                        data = json.loads(chunk_str[6:])
                        event_type = data.get('event')
                        
                        # 记录消息ID
                        if event_type in ['message', 'agent_message']:
                            if not ai_message_id and data.get('id'):
                                ai_message_id = data.get('id')
                            if data.get('answer'):
                                ai_content_buffer += data.get('answer', '')
                        
                        # 记录 Dify 会话ID
                        if data.get('conversation_id') and not dify_conversation_id:
                            dify_conversation_id = data.get('conversation_id')
                            # 发送我们的会话ID给前端
                            custom_event = f'data: {{"event": "message", "conversation_id": "{conversation_id}", "message_id": "{ai_message_id or ""}"}}\n\n'
                            yield custom_event.encode('utf-8')
                            
                    except json.JSONDecodeError:
                        pass
            
            # 5. 保存 AI 响应消息
            if ai_content_buffer:
                ai_message = Message(
                    id=ai_message_id or "",
                    conversation_id=conversation_id,
                    content={"text": ai_content_buffer},
                    type="text",
                    sender_id=None,
                    sender_digital_human_id=None,
                    sender_type="system",
                    is_read=False,
                    timestamp=datetime.now()
                )
                await self.message_repo.save(ai_message)
                
                # 6. WebSocket 广播（如果配置了）
                if self.broadcasting_service:
                    try:
                        await self.broadcasting_service.broadcast_to_conversation(
                            conversation_id=conversation_id,
                            event="agent_message",
                            data={
                                "message_id": ai_message.id,
                                "content": ai_content_buffer,
                                "timestamp": ai_message.timestamp.isoformat()
                            }
                        )
                    except Exception as e:
                        logger.warning(f"WebSocket 广播失败: {e}")
            
            logger.info(f"Agent 对话完成: conversation_id={conversation_id}")
            
        except Exception as e:
            logger.error(f"Agent 对话失败: {e}", exc_info=True)
            # 发送错误事件
            error_event = f'data: {{"event": "error", "message": "{str(e)}"}}\n\n'
            yield error_event.encode('utf-8')
    
    async def get_conversations(
        self,
        agent_config_id: str,
        user_id: str
    ) -> List[AgentConversationResponse]:
        """获取用户的 Agent 会话列表"""
        conversations = await self.conversation_repo.get_user_conversations(
            user_id=user_id,
            user_role="customer"  # 默认角色
        )
        
        # 过滤出属于该 Agent 的会话（通过 extra_metadata 标记）
        agent_conversations = [
            conv for conv in conversations
            if conv.extra_metadata and conv.extra_metadata.get('agent_config_id') == agent_config_id
        ]
        
        # 转换为响应模型
        return [
            AgentConversationResponse(
                id=conv.id,
                agent_config_id=agent_config_id,
                title=conv.title,
                created_at=conv.created_at.isoformat(),
                updated_at=conv.updated_at.isoformat(),
                message_count=conv.message_count,
                last_message=conv.extra_metadata.get('last_message') if conv.extra_metadata else None
            )
            for conv in agent_conversations
        ]
    
    async def create_conversation(
        self,
        agent_config_id: str,
        user_id: str,
        title: Optional[str] = None
    ) -> AgentConversationResponse:
        """创建新会话"""
        conversation = await self._create_conversation(
            agent_config_id=agent_config_id,
            user_id=user_id,
            title=title or "新对话"
        )
        
        return AgentConversationResponse(
            id=conversation.id,
            agent_config_id=agent_config_id,
            title=conversation.title,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            message_count=0,
            last_message=None
        )
    
    async def get_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 50
    ) -> List[AgentMessageResponse]:
        """获取会话消息历史"""
        # 验证会话访问权限
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"会话不存在: {conversation_id}")
        
        # 检查用户权限（简化版，实际应该更复杂）
        # TODO: 实现完整的权限检查
        
        # 获取消息列表
        messages = await self.message_repo.get_by_conversation_id(
            conversation_id, limit=limit
        )
        
        # 转换为响应模型
        return [
            AgentMessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                content=msg.content.get('text', '') if isinstance(msg.content, dict) else str(msg.content),
                is_answer=(msg.sender_type == 'system'),
                timestamp=msg.timestamp.isoformat(),
                agent_thoughts=None,  # TODO: 解析 agent_thoughts
                files=None,
                is_error=False
            )
            for msg in messages
        ]
    
    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """删除会话"""
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"会话不存在: {conversation_id}")
        
        # TODO: 验证用户权限
        
        return await self.conversation_repo.delete(conversation_id)
    
    async def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        title: str
    ) -> AgentConversationResponse:
        """更新会话"""
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"会话不存在: {conversation_id}")
        
        # TODO: 验证用户权限
        
        conversation.title = title
        conversation.updated_at = datetime.now()
        updated_conv = await self.conversation_repo.save(conversation)
        
        agent_config_id = updated_conv.extra_metadata.get('agent_config_id') if updated_conv.extra_metadata else ""
        
        return AgentConversationResponse(
            id=updated_conv.id,
            agent_config_id=agent_config_id,
            title=updated_conv.title,
            created_at=updated_conv.created_at.isoformat(),
            updated_at=updated_conv.updated_at.isoformat(),
            message_count=updated_conv.message_count,
            last_message=None
        )
    
    # ========== 私有辅助方法 ==========
    
    async def _create_conversation(
        self,
        agent_config_id: str,
        user_id: str,
        title: str
    ) -> Conversation:
        """创建会话的内部方法"""
        conversation = Conversation.create(
            title=title,
            owner_id=user_id,
            chat_mode="single",
            extra_metadata={
                "agent_config_id": agent_config_id,
                "created_from": "agent_chat"
            }
        )
        
        return await self.conversation_repo.save(conversation)

