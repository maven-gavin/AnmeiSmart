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
from app.chat.domain.entities.conversation import Conversation  # 领域实体
from app.chat.domain.entities.message import Message  # 领域实体
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
            logger.info("=" * 80)
            logger.info(f"🚀 开始 Agent 对话")
            logger.info(f"   agent_config_id: {agent_config_id}")
            logger.info(f"   user_id: {user_id}")
            logger.info(f"   message: {message[:100]}..." if len(message) > 100 else f"   message: {message}")
            logger.info(f"   conversation_id: {conversation_id}")
            
            # 1. 创建 Dify 客户端
            logger.info("📝 步骤 1: 创建 Dify 客户端...")
            dify_client = self.dify_client_factory.create_client_from_db(
                agent_config_id, self.db
            )
            logger.info(f"✅ Dify 客户端创建成功")
            logger.info(f"   base_url: {dify_client.base_url}")
            logger.info(f"   api_key: {'*' * 20}...{dify_client.api_key[-8:] if len(dify_client.api_key) > 8 else '***'}")
            
            # 2. 获取或创建会话
            logger.info("📝 步骤 2: 获取或创建会话...")
            if not conversation_id:
                conversation = await self._create_conversation(
                    agent_config_id=agent_config_id,
                    user_id=user_id,
                    title="新对话"
                )
                conversation_id = conversation.id
                logger.info(f"✅ 创建新会话: {conversation_id}")
            else:
                conversation = await self.conversation_repo.get_by_id(conversation_id)
                if not conversation:
                    raise ValueError(f"会话不存在: {conversation_id}")
                logger.info(f"✅ 使用现有会话: {conversation_id}")
            
            # 3. 保存用户消息
            logger.info("📝 步骤 3: 保存用户消息...")
            user_message = Message.create_text_message(
                conversation_id=conversation_id,
                text=message,
                sender_id=user_id,
                sender_type="customer"
            )
            await self.message_repo.save(user_message)
            logger.info(f"✅ 用户消息已保存: {user_message.id}")
            
            # 4. 调用 Dify Agent 流式对话
            user_identifier = f"user_{user_id}"
            
            # 从会话元数据中获取 Dify conversation_id（如果存在）
            dify_conv_id = None
            logger.info(f"   会话元数据: {conversation.extra_metadata}")
            if conversation.extra_metadata:
                dify_conv_id = conversation.extra_metadata.get('dify_conversation_id')
                logger.info(f"   从元数据获取到的 dify_conversation_id: {dify_conv_id}")
            
            logger.info("📝 步骤 4: 调用 Dify API 流式对话...")
            logger.info(f"   完整 URL: {dify_client.base_url}/chat-messages")
            logger.info(f"   user_identifier: {user_identifier}")
            logger.info(f"   dify_conversation_id: {dify_conv_id or '(新会话)'}")
            
            chunk_count = 0
            async for chunk in dify_client.create_chat_message(
                query=message,
                user=user_identifier,
                conversation_id=dify_conv_id,  # 使用保存的 Dify conversation_id
                inputs=inputs,
                response_mode="streaming"
            ):
                chunk_count += 1
                # 解析 SSE 事件
                chunk_str = chunk.decode('utf-8') if isinstance(chunk, bytes) else chunk
                
                # 前几个 chunk 打印详细日志
                if chunk_count <= 3:
                    logger.info(f"📦 收到第 {chunk_count} 个 chunk: {chunk_str[:200]}...")
                elif chunk_count % 10 == 0:
                    logger.debug(f"📦 已收到 {chunk_count} 个 chunks...")
                
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
                            logger.info(f"   检测到 Dify conversation_id: {dify_conversation_id}")
                            # 不再发送自定义事件，让前端直接处理 Dify 的标准 message 事件
                            
                    except json.JSONDecodeError:
                        pass
            
            # 5. 保存 AI 响应消息
            if ai_content_buffer:
                ai_message = Message.create_text_message(
                    conversation_id=conversation_id,
                    text=ai_content_buffer,
                    sender_type="system",  # AI 回复标记为系统消息
                    extra_metadata={
                        "dify_message_id": ai_message_id,
                        "dify_conversation_id": dify_conversation_id,
                        "agent_config_id": agent_config_id
                    }
                )
                await self.message_repo.save(ai_message)
                logger.info(f"✅ AI 消息已保存: {ai_message.id}")
                
                # 保存 Dify conversation_id 到会话元数据（用于后续多轮对话）
                logger.info(f"📝 检查是否需要保存 Dify conversation_id:")
                logger.info(f"   dify_conversation_id: {dify_conversation_id}")
                logger.info(f"   dify_conv_id (原值): {dify_conv_id}")
                logger.info(f"   是否需要保存: {dify_conversation_id and dify_conversation_id != dify_conv_id}")
                if dify_conversation_id and dify_conversation_id != dify_conv_id:
                    if not conversation.extra_metadata:
                        conversation.extra_metadata = {}
                    conversation.extra_metadata['dify_conversation_id'] = dify_conversation_id
                    logger.info(f"   更新后的元数据: {conversation.extra_metadata}")
                    await self.conversation_repo.save(conversation)
                    logger.info(f"✅ 已保存 Dify conversation_id: {dify_conversation_id}")
                
                # 6. WebSocket 广播（如果配置了）
                if self.broadcasting_service:
                    try:
                        await self.broadcasting_service.broadcast_to_conversation(
                            conversation_id=conversation_id,
                            event="agent_message",
                            data={
                                "message_id": ai_message.id,
                                "content": ai_content_buffer,
                                "timestamp": ai_message.created_at.isoformat()
                            }
                        )
                    except Exception as e:
                        logger.warning(f"WebSocket 广播失败: {e}")
            
            logger.info(f"✅ Agent 对话完成")
            logger.info(f"   conversation_id: {conversation_id}")
            logger.info(f"   ai_message_id: {ai_message_id}")
            logger.info(f"   内容长度: {len(ai_content_buffer)} 字符")
            logger.info(f"   总 chunks: {chunk_count}")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"❌ Agent 对话失败: {e}", exc_info=True)
            logger.error("=" * 80)
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
        messages = await self.message_repo.get_conversation_messages(
            conversation_id, limit=limit
        )
        
        # 转换为响应模型
        return [
            AgentMessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                content=msg.content.get('text', '') if isinstance(msg.content, dict) else str(msg.content),
                is_answer=(msg.sender_type == 'system'),
                timestamp=msg.created_at.isoformat(),
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
        
        # 使用领域实体的方法更新标题
        conversation.update_title(title)
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
    
    # ========== 消息反馈功能 ==========
    
    async def message_feedback(
        self,
        agent_config_id: str,
        message_id: str,
        rating: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        提交消息反馈
        
        Args:
            agent_config_id: Agent 配置ID
            message_id: Dify 消息ID
            rating: 评分 ('like' 或 'dislike')
            user_id: 用户ID
        
        Returns:
            反馈结果
        """
        logger.info(f"提交消息反馈: message_id={message_id}, rating={rating}")
        
        # 创建 Dify 客户端
        dify_client = self.dify_client_factory.create_client_from_db(
            agent_config_id, self.db
        )
        
        # 调用 Dify API
        user_identifier = f"user_{user_id}"
        result = await dify_client.message_feedback(
            message_id=message_id,
            rating=rating,
            user=user_identifier
        )
        
        logger.info(f"消息反馈成功: {result}")
        return result
    
    # ========== 建议问题功能 ==========
    
    async def get_suggested_questions(
        self,
        agent_config_id: str,
        message_id: str,
        user_id: str
    ) -> List[str]:
        """
        获取建议问题
        
        Args:
            agent_config_id: Agent 配置ID
            message_id: Dify 消息ID
            user_id: 用户ID
        
        Returns:
            建议问题列表
        """
        logger.info(f"获取建议问题: message_id={message_id}")
        
        # 创建 Dify 客户端
        dify_client = self.dify_client_factory.create_client_from_db(
            agent_config_id, self.db
        )
        
        # 调用 Dify API
        user_identifier = f"user_{user_id}"
        result = await dify_client.get_suggested(
            message_id=message_id,
            user=user_identifier
        )
        
        # 提取建议问题列表
        questions = result.get('data', [])
        logger.info(f"获取到 {len(questions)} 个建议问题")
        return questions
    
    # ========== 停止消息生成功能 ==========
    
    async def stop_message_generation(
        self,
        agent_config_id: str,
        task_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        停止消息生成
        
        Args:
            agent_config_id: Agent 配置ID
            task_id: Dify 任务ID
            user_id: 用户ID
        
        Returns:
            停止结果
        """
        logger.info(f"停止消息生成: task_id={task_id}")
        
        # 创建 Dify 客户端
        dify_client = self.dify_client_factory.create_client_from_db(
            agent_config_id, self.db
        )
        
        # 调用 Dify API
        user_identifier = f"user_{user_id}"
        result = await dify_client.stop_message(
            task_id=task_id,
            user=user_identifier
        )
        
        logger.info(f"停止消息成功: {result}")
        return result
    
    # ========== 语音转文字功能 ==========
    
    async def audio_to_text(
        self,
        agent_config_id: str,
        audio_file: Any,
        user_id: str
    ) -> str:
        """
        语音转文字
        
        Args:
            agent_config_id: Agent 配置ID
            audio_file: 音频文件
            user_id: 用户ID
        
        Returns:
            转换后的文本
        """
        logger.info(f"语音转文字: 用户={user_id}")
        
        # 创建 Dify 客户端
        dify_client = self.dify_client_factory.create_client_from_db(
            agent_config_id, self.db
        )
        
        # 调用 Dify API
        user_identifier = f"user_{user_id}"
        result = await dify_client.audio_to_text(
            audio_file=audio_file,
            user=user_identifier
        )
        
        # 提取文本
        text = result.get('text', '')
        logger.info(f"语音转文字成功: {len(text)} 字符")
        return text
    
    # ========== 文字转语音功能 ==========
    
    async def text_to_audio(
        self,
        agent_config_id: str,
        text: str,
        user_id: str,
        streaming: bool = False
    ) -> Dict[str, Any]:
        """
        文字转语音
        
        Args:
            agent_config_id: Agent 配置ID
            text: 文本内容
            user_id: 用户ID
            streaming: 是否流式返回
        
        Returns:
            音频数据或流
        """
        logger.info(f"文字转语音: {len(text)} 字符")
        
        # 创建 Dify 客户端
        dify_client = self.dify_client_factory.create_client_from_db(
            agent_config_id, self.db
        )
        
        # 调用 Dify API
        user_identifier = f"user_{user_id}"
        result = await dify_client.text_to_audio(
            text=text,
            user=user_identifier,
            streaming=streaming
        )
        
        logger.info(f"文字转语音成功")
        return result
    
    # ========== 文件上传功能 ==========
    
    async def upload_file(
        self,
        agent_config_id: str,
        file: Any,
        user_id: str
    ) -> Dict[str, Any]:
        """
        上传文件到 Dify
        
        Args:
            agent_config_id: Agent 配置ID
            file: 文件对象
            user_id: 用户ID
        
        Returns:
            上传结果，包含 upload_file_id
        """
        logger.info(f"上传文件: 用户={user_id}")
        
        # 创建 Dify 客户端
        dify_client = self.dify_client_factory.create_client_from_db(
            agent_config_id, self.db
        )
        
        # 调用 Dify API
        user_identifier = f"user_{user_id}"
        result = await dify_client.file_upload(
            user=user_identifier,
            files=file
        )
        
        logger.info(f"文件上传成功: {result}")
        return result
    
    # ========== 应用配置功能 ==========
    
    async def get_application_parameters(
        self,
        agent_config_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        获取应用参数配置
        
        Args:
            agent_config_id: Agent 配置ID
            user_id: 用户ID
        
        Returns:
            应用参数配置
        """
        logger.info(f"获取应用参数: agent_config_id={agent_config_id}, user_id={user_id}")
        
        # 创建 Dify 客户端
        dify_client = self.dify_client_factory.create_client_from_db(
            agent_config_id, self.db
        )
        
        # 调用 Dify API
        user_identifier = f"user_{user_id}"
        result = await dify_client.get_application_parameters(
            user=user_identifier
        )
        
        logger.info(f"获取应用参数成功")
        return result
    
    async def get_application_meta(
        self,
        agent_config_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        获取应用元数据
        
        Args:
            agent_config_id: Agent 配置ID
            user_id: 用户ID
        
        Returns:
            应用元数据
        """
        logger.info(f"获取应用元数据: agent_config_id={agent_config_id}, user_id={user_id}")
        
        # 创建 Dify 客户端
        dify_client = self.dify_client_factory.create_client_from_db(
            agent_config_id, self.db
        )
        
        # 调用 Dify API
        user_identifier = f"user_{user_id}"
        result = await dify_client.get_meta(
            user=user_identifier
        )
        
        logger.info(f"获取应用元数据成功")
        return result

