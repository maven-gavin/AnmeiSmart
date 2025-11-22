"""
Agent 对话服务
负责协调 Agent 对话的完整流程
"""

import logging
import json
from typing import Optional, Dict, Any, List, AsyncIterator
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.ai.adapters.dify_agent_client import DifyAgentClientFactory, DifyAgentClient
from app.ai.schemas.agent_chat import (
    AgentMessageResponse,
    AgentConversationResponse
)
from app.chat.services.chat_service import ChatService
from app.chat.models.chat import Conversation, Message, ConversationParticipant
from app.chat.schemas.chat import ConversationInfo, MessageInfo
from app.websocket.broadcasting_service import BroadcastingService
from app.common.deps.uuid_utils import message_id

logger = logging.getLogger(__name__)


class AgentChatService:
    """
    Agent 对话服务
    负责协调 Agent 对话的完整流程
    """
    
    def __init__(
        self,
        dify_client_factory: DifyAgentClientFactory,
        chat_service: ChatService,
        broadcasting_service: Optional[BroadcastingService],
        db: Session
    ):
        self.dify_client_factory = dify_client_factory
        self.chat_service = chat_service
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
                conversation_info = self._create_conversation(
                    agent_config_id=agent_config_id,
                    user_id=user_id,
                    title="新对话"
                )
                conversation_id = conversation_info.id
                logger.info(f"✅ 创建新会话: {conversation_id}")
            else:
                conversation_info = self.chat_service.get_conversation(conversation_id, user_id)
                if not conversation_info:
                    raise ValueError(f"会话不存在: {conversation_id}")
                logger.info(f"✅ 使用现有会话: {conversation_id}")
            
            # 3. 保存用户消息
            logger.info("📝 步骤 3: 保存用户消息...")
            user_message_info = self.chat_service.create_text_message(
                conversation_id=conversation_id,
                sender_id=user_id,
                content=message,
                sender_type="customer"
            )
            logger.info(f"✅ 用户消息已保存: {user_message_info.id}")
            
            # 4. 调用 Dify Agent 流式对话
            user_identifier = f"user_{user_id}"
            
            # 从会话元数据中获取 Dify conversation_id（如果存在）
            # 需要从数据库模型获取 extra_metadata，因为 ConversationInfo 不包含该字段
            conversation_model = self.db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            dify_conv_id = None
            if conversation_model and conversation_model.extra_metadata:
                dify_conv_id = conversation_model.extra_metadata.get('dify_conversation_id')
                logger.info(f"   从元数据获取到的 dify_conversation_id: {dify_conv_id}")
            else:
                logger.info(f"   会话元数据为空或不存在")
            
            logger.info("📝 步骤 4: 调用 Dify API 流式对话...")
            logger.info(f"   完整 URL: {dify_client.base_url}/chat-messages")
            logger.info(f"   user_identifier: {user_identifier}")
            logger.info(f"   dify_conversation_id: {dify_conv_id or '(新会话)'}")
            
            # 处理文件字段：将文件ID转换为 Dify 文件格式（保留在 inputs 中）
            processed_inputs = {}
            if inputs:
                for key, value in inputs.items():
                    # 如果字段名包含 'file' 并且有值，转换为 Dify 文件格式
                    if 'file' in key.lower() and value:
                        # 转换为 Dify 文件对象格式
                        if isinstance(value, list):
                            # 文件列表
                            processed_inputs[key] = [
                                {
                                    "type": "document",
                                    "transfer_method": "local_file",
                                    "upload_file_id": file_id
                                }
                                for file_id in value
                            ]
                        else:
                            # 单个文件
                            processed_inputs[key] = {
                                "type": "document",
                                "transfer_method": "local_file",
                                "upload_file_id": value
                            }
                    else:
                        # 非文件字段，直接复制
                        processed_inputs[key] = value
            
            logger.info(f"   处理后的 inputs: {processed_inputs}")
            
            chunk_count = 0
            async for chunk in dify_client.create_chat_message(
                query=message,
                user=user_identifier,
                conversation_id=dify_conv_id,  # 使用保存的 Dify conversation_id
                inputs=processed_inputs,
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
                # 使用 ChatService 创建消息，但需要支持 extra_metadata
                # 由于 ChatService.create_text_message 不支持 extra_metadata，直接操作模型
                ai_message = Message(
                    id=message_id(),
                    conversation_id=conversation_id,
                    content={
                        "type": "text",
                        "text": ai_content_buffer
                    },
                    type="text",
                    sender_type="system",  # AI 回复标记为系统消息
                    extra_metadata={
                        "dify_message_id": ai_message_id,
                        "dify_conversation_id": dify_conversation_id,
                        "agent_config_id": agent_config_id
                    }
                )
                
                self.db.add(ai_message)
                
                # 更新会话统计
                conversation_model = self.db.query(Conversation).filter(
                    Conversation.id == conversation_id
                ).first()
                if conversation_model:
                    conversation_model.message_count = (conversation_model.message_count or 0) + 1
                    conversation_model.last_message_at = datetime.now()
                    conversation_model.unread_count = (conversation_model.unread_count or 0) + 1
                
                self.db.commit()
                self.db.refresh(ai_message)
                
                # 转换为 MessageInfo
                ai_message_info = MessageInfo.from_model(ai_message)
                logger.info(f"✅ AI 消息已保存: {ai_message_info.id}")
                
                # 保存 Dify conversation_id 到会话元数据（用于后续多轮对话）
                logger.info(f"📝 检查是否需要保存 Dify conversation_id:")
                logger.info(f"   dify_conversation_id: {dify_conversation_id}")
                logger.info(f"   dify_conv_id (原值): {dify_conv_id}")
                logger.info(f"   是否需要保存: {dify_conversation_id and dify_conversation_id != dify_conv_id}")
                if dify_conversation_id and dify_conversation_id != dify_conv_id:
                    if conversation_model:
                        if not conversation_model.extra_metadata:
                            conversation_model.extra_metadata = {}
                        conversation_model.extra_metadata['dify_conversation_id'] = dify_conversation_id
                        logger.info(f"   更新后的元数据: {conversation_model.extra_metadata}")
                        self.db.commit()
                        logger.info(f"✅ 已保存 Dify conversation_id: {dify_conversation_id}")
                
                # 6. WebSocket 广播（如果配置了）
                if self.broadcasting_service:
                    try:
                        await self.broadcasting_service.broadcast_to_conversation(
                            conversation_id=conversation_id,
                            event="agent_message",
                            data={
                                "message_id": ai_message_info.id,
                                "content": ai_content_buffer,
                                "timestamp": ai_message_info.timestamp.isoformat()
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
    
    def get_conversations(
        self,
        agent_config_id: str,
        user_id: str
    ) -> List[AgentConversationResponse]:
        """获取用户的 Agent 会话列表"""
        # 获取用户的所有会话
        conversations = self.chat_service.get_user_conversations(
            user_id=user_id,
            limit=1000  # 获取所有会话，然后过滤
        )
        
        # 需要从数据库模型获取 extra_metadata，因为 ConversationInfo 不包含该字段
        # 查询属于该 Agent 的会话
        conversation_models = self.db.query(Conversation).filter(
            Conversation.owner_id == user_id,
            Conversation.extra_metadata.isnot(None)
        ).all()
        
        # 过滤出属于该 Agent 的会话（通过 extra_metadata 标记）
        agent_conversations = []
        for conv_model in conversation_models:
            if conv_model.extra_metadata and conv_model.extra_metadata.get('agent_config_id') == agent_config_id:
                # 找到对应的 ConversationInfo
                conv_info = next((c for c in conversations if c.id == conv_model.id), None)
                if conv_info:
                    agent_conversations.append((conv_model, conv_info))
        
        # 转换为响应模型
        return [
            AgentConversationResponse(
                id=conv_info.id,
                agent_config_id=agent_config_id,
                title=conv_info.title,
                created_at=conv_info.created_at.isoformat(),
                updated_at=conv_info.updated_at.isoformat(),
                message_count=conv_info.message_count,
                last_message=conv_model.extra_metadata.get('last_message') if conv_model.extra_metadata else None
            )
            for conv_model, conv_info in agent_conversations
        ]
    
    def create_conversation(
        self,
        agent_config_id: str,
        user_id: str,
        title: Optional[str] = None
    ) -> AgentConversationResponse:
        """创建新会话"""
        conversation = self._create_conversation(
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
            message_count=conversation.message_count,
            last_message=None
        )
    
    def get_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 50
    ) -> List[AgentMessageResponse]:
        """获取会话消息历史"""
        # 验证会话访问权限
        conversation_info = self.chat_service.get_conversation(conversation_id, user_id)
        if not conversation_info:
            raise ValueError(f"会话不存在: {conversation_id}")
        
        # 检查用户权限（简化版，实际应该更复杂）
        # TODO: 实现完整的权限检查
        
        # 获取消息列表
        messages = self.chat_service.get_conversation_messages(
            conversation_id=conversation_id,
            limit=limit
        )
        
        # 转换为响应模型
        return [
            AgentMessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                content=msg.content.get('text', '') if isinstance(msg.content, dict) else str(msg.content),
                is_answer=(msg.sender.type == 'system' if hasattr(msg, 'sender') and msg.sender else False),
                timestamp=msg.timestamp.isoformat(),
                agent_thoughts=None,  # TODO: 解析 agent_thoughts
                files=None,
                is_error=False
            )
            for msg in messages
        ]
    
    def delete_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """删除会话"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.owner_id == user_id
        ).first()
        
        if not conversation:
            raise ValueError(f"会话不存在: {conversation_id}")
        
        # TODO: 验证用户权限
        
        # 删除会话（级联删除消息和参与者）
        self.db.delete(conversation)
        self.db.commit()
        
        return True
    
    def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        title: str
    ) -> AgentConversationResponse:
        """更新会话"""
        # 使用 ChatService 更新会话
        updated_conv_info = self.chat_service.update_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            updates={"title": title}
        )
        
        if not updated_conv_info:
            raise ValueError(f"会话不存在: {conversation_id}")
        
        # 获取 extra_metadata
        conversation_model = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        agent_config_id = ""
        if conversation_model and conversation_model.extra_metadata:
            agent_config_id = conversation_model.extra_metadata.get('agent_config_id', "")
        
        return AgentConversationResponse(
            id=updated_conv_info.id,
            agent_config_id=agent_config_id,
            title=updated_conv_info.title,
            created_at=updated_conv_info.created_at.isoformat(),
            updated_at=updated_conv_info.updated_at.isoformat(),
            message_count=updated_conv_info.message_count,
            last_message=None
        )
    
    # ========== 私有辅助方法 ==========
    
    def _create_conversation(
        self,
        agent_config_id: str,
        user_id: str,
        title: str
    ) -> ConversationInfo:
        """创建会话的内部方法"""
        # 使用 ChatService 创建会话，然后更新 extra_metadata
        conversation_info = self.chat_service.create_conversation(
            title=title,
            owner_id=user_id,
            chat_mode="single",
            tag="agent_chat"
        )
        
        # 更新会话的 extra_metadata
        conversation_model = self.db.query(Conversation).filter(
            Conversation.id == conversation_info.id
        ).first()
        
        if conversation_model:
            conversation_model.extra_metadata = {
                "agent_config_id": agent_config_id,
                "created_from": "agent_chat"
            }
            self.db.commit()
            self.db.refresh(conversation_model)
            
            # 重新加载并转换
            conversation_model = self.db.query(Conversation).options(
                joinedload(Conversation.owner),
                joinedload(Conversation.participants).joinedload(ConversationParticipant.user),
                joinedload(Conversation.messages).limit(1).order_by(desc(Message.timestamp))
            ).filter(Conversation.id == conversation_info.id).first()
            
            last_message = None
            if conversation_model.messages:
                last_msg = conversation_model.messages[0] if conversation_model.messages else None
                if last_msg:
                    last_message = MessageInfo.from_model(last_msg)
            
            return ConversationInfo.from_model(conversation_model, last_message=last_message)
        
        return conversation_info
    
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
            message_id: 我们系统的消息ID
            rating: 评分 ('like' 或 'dislike')
            user_id: 用户ID
        
        Returns:
            反馈结果
        """
        logger.info(f"提交消息反馈: message_id={message_id}, rating={rating}")
        
        # 1. 根据我们系统的 message_id 查找消息
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise ValueError(f"消息不存在: {message_id}")
        
        # 2. 从 extra_metadata 中获取 Dify 的原生 message_id
        dify_message_id = None
        if message.extra_metadata and isinstance(message.extra_metadata, dict):
            dify_message_id = message.extra_metadata.get('dify_message_id')
        
        if not dify_message_id:
            raise ValueError(f"消息缺少 Dify message_id: {message_id}")
        
        logger.info(f"找到 Dify message_id: {dify_message_id}")
        
        # 3. 创建 Dify 客户端
        dify_client = self.dify_client_factory.create_client_from_db(
            agent_config_id, self.db
        )
        
        # 4. 调用 Dify API（使用 Dify 的原生 message_id）
        user_identifier = f"user_{user_id}"
        result = await dify_client.message_feedback(
            message_id=dify_message_id,  # 使用 Dify 的原生 message_id
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
        
        先检查应用配置是否启用了建议问题功能，如果启用才调用建议问题API
        
        Args:
            agent_config_id: Agent 配置ID
            message_id: 我们系统的消息ID
            user_id: 用户ID
        
        Returns:
            建议问题列表
        """
        logger.info(f"获取建议问题: message_id={message_id}")
        
        try:
            # 1. 根据我们系统的 message_id 查找消息
            message = self.db.query(Message).filter(Message.id == message_id).first()
            if not message:
                raise ValueError(f"消息不存在: {message_id}")
            
            # 2. 从 extra_metadata 中获取 Dify 的原生 message_id
            dify_message_id = None
            if message.extra_metadata and isinstance(message.extra_metadata, dict):
                dify_message_id = message.extra_metadata.get('dify_message_id')
            
            if not dify_message_id:
                raise ValueError(f"消息缺少 Dify message_id: {message_id}")
            
            logger.info(f"找到 Dify message_id: {dify_message_id}")
            
            # 3. 首先获取应用参数配置
            app_params = await self.get_application_parameters(
                agent_config_id=agent_config_id,
                user_id=user_id
            )
            
            # 4. 检查建议问题配置是否启用
            suggested_questions_config = app_params.get('suggested_questions_after_answer')
            if not suggested_questions_config:
                logger.info("应用未启用建议问题功能，返回空列表")
                return []
            
            # 检查配置是否启用
            is_enabled = suggested_questions_config.get('enabled', False)
            if not is_enabled:
                logger.info("建议问题功能已禁用，返回空列表")
                return []
            
            logger.info("建议问题功能已启用，调用Dify API获取建议问题")
            
            # 5. 创建 Dify 客户端
            dify_client = self.dify_client_factory.create_client_from_db(
                agent_config_id, self.db
            )
            
            # 6. 调用 Dify API 获取建议问题（使用 Dify 的原生 message_id）
            user_identifier = f"user_{user_id}"
            result = await dify_client.get_suggested(
                message_id=dify_message_id,  # 使用 Dify 的原生 message_id
                user=user_identifier
            )
            
            # 提取建议问题列表
            questions = result.get('data', [])
            logger.info(f"获取到 {len(questions)} 个建议问题")
            return questions
            
        except Exception as e:
            logger.warning(f"获取建议问题失败，返回空列表: {e}")
            # 如果获取建议问题失败，返回空列表而不是抛出异常
            # 这样不会影响主要的对话功能
            return []
    
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
        
        # 转换 user_input_form 结构
        if "user_input_form" in result and isinstance(result["user_input_form"], list):
            transformed_form = []
            for item in result["user_input_form"]:
                # Dify 返回的结构是: [{"field-type": {field_config}}]
                # 需要转换为: [{field_config}]
                if isinstance(item, dict):
                    # 获取嵌套的字段配置
                    for field_type_key, field_config in item.items():
                        if isinstance(field_config, dict):
                            transformed_form.append(field_config)
                            break
                else:
                    # 如果已经是正确的结构，直接使用
                    transformed_form.append(item)
            
            result["user_input_form"] = transformed_form
            logger.info(f"转换后的 user_input_form: {transformed_form}")
        
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

