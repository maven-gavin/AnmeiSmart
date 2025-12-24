"""
Agent 对话服务
负责协调 Agent 对话的完整流程
"""

import logging
import json
from typing import Optional, Dict, Any, List, AsyncIterator
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.ai.adapters.dify_agent_client import DifyAgentClientFactory, DifyAgentClient
from app.ai.schemas.agent_chat import (
    AgentMessageResponse,
    AgentConversationResponse
)
from app.chat.services.chat_service import ChatService
from app.websocket.broadcasting_service import BroadcastingService
from app.ai.utils.stream_buffer import StreamBuffer

logger = logging.getLogger(__name__)


class AgentChatService:
    """
    Agent 对话服务
    负责协调 Agent 对话的完整流程
    """
    
    def __init__(
        self,
        dify_client_factory: DifyAgentClientFactory,
        chat_service: ChatService,  # 保留以保持接口兼容性，但已不再使用
        broadcasting_service: Optional[BroadcastingService],  # 保留以保持接口兼容性，但已不再使用
        db: Session
    ):
        self.dify_client_factory = dify_client_factory
        self.chat_service = chat_service  # 已不再使用，保留以保持接口兼容性
        self.broadcasting_service = broadcasting_service  # 已不再使用，保留以保持接口兼容性
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
        
        优化后流程：
        1. 创建 Dify 客户端
        2. 调用 Dify Agent 获取流式响应
        3. 使用 StreamBuffer 处理被分割的标签
        4. 实时转发响应给前端
        """
        dify_client: Optional[DifyAgentClient] = None
        stream_buffer = StreamBuffer()
        dify_sse_buffer = ""

        def _find_event_separator_index(input_str: str) -> Optional[tuple[int, int]]:
            """找到一个完整 SSE event 分隔符的位置，返回 (index, sep_len)。"""
            idx_crlf = input_str.find("\r\n\r\n")
            idx_lf = input_str.find("\n\n")
            if idx_crlf == -1 and idx_lf == -1:
                return None
            if idx_crlf != -1 and (idx_lf == -1 or idx_crlf < idx_lf):
                return (idx_crlf, 4)
            return (idx_lf, 2)

        def _extract_event_data(event_block: str) -> str:
            """兼容 data: 与 data: <space>，并支持同一个事件多行 data:。"""
            data_parts: list[str] = []
            for line in event_block.splitlines():
                if not line.startswith("data:"):
                    continue
                part = line[5:]
                if part.startswith(" "):
                    part = part[1:]
                data_parts.append(part)
            # Dify 返回的 data 通常是一行 JSON；若被拆成多行，拼接可避免插入换行导致 json.loads 失败
            return "".join(data_parts)
        
        try:
            logger.info("=" * 80)
            logger.info(f"🚀 开始 Agent 对话")
            logger.info(f"   agent_config_id: {agent_config_id}")
            logger.info(f"   user_id: {user_id}")
            logger.info(f"   message: {message[:100]}..." if len(message) > 100 else f"   message: {message}")
            logger.info(f"   conversation_id: {conversation_id or '(新会话)'}")
            
            # 1. 创建 Dify 客户端
            logger.info("📝 步骤 1: 创建 Dify 客户端...")
            dify_client = self.dify_client_factory.create_client_from_db(
                agent_config_id, self.db
            )
            logger.info(f"✅ Dify 客户端创建成功")
            logger.info(f"   base_url: {dify_client.base_url}")
            logger.info(f"   api_key: {'*' * 20}...{dify_client.api_key[-8:] if len(dify_client.api_key) > 8 else '***'}")
            
            # 2. 调用 Dify Agent 流式对话
            user_identifier = f"user_{user_id}"
            dify_conv_id = conversation_id
            
            logger.info("📝 步骤 2: 调用 Dify API 流式对话...")
            
            # 处理文件字段
            processed_inputs = {}
            if inputs:
                for key, value in inputs.items():
                    if 'file' in key.lower() and value:
                        if isinstance(value, list):
                            processed_inputs[key] = [
                                {
                                    "type": "document",
                                    "transfer_method": "local_file",
                                    "upload_file_id": file_id
                                }
                                for file_id in value
                            ]
                        else:
                            processed_inputs[key] = {
                                "type": "document",
                                "transfer_method": "local_file",
                                "upload_file_id": value
                            }
                    else:
                        processed_inputs[key] = value
            
            # 3. 流式转发响应（使用 StreamBuffer）
            chunk_count = 0
            event_types = {}
            
            # 保存最后的元数据以便 flush 时使用
            last_conversation_id = dify_conv_id
            last_message_id = ""
            last_task_id = ""
            
            async for chunk in dify_client.create_chat_message(
                query=message,
                user=user_identifier,
                conversation_id=dify_conv_id,
                inputs=processed_inputs,
                response_mode="streaming"
            ):
                chunk_count += 1
                chunk_str = chunk.decode('utf-8') if isinstance(chunk, bytes) else chunk
                
                # 使用缓冲区按 SSE 事件分隔符解析，避免 chunk 边界/多行 data: 导致丢片段
                dify_sse_buffer += chunk_str

                while True:
                    sep = _find_event_separator_index(dify_sse_buffer)
                    if not sep:
                        break
                    sep_idx, sep_len = sep
                    event_block = dify_sse_buffer[:sep_idx]
                    dify_sse_buffer = dify_sse_buffer[sep_idx + sep_len:]

                    data_str = _extract_event_data(event_block)
                    if not data_str:
                        continue

                    try:
                        data = json.loads(data_str)
                        event_type = data.get("event", "unknown")
                        
                        # 更新元数据
                        if data.get('conversation_id'):
                            last_conversation_id = data.get('conversation_id')
                        if data.get('message_id'):
                            last_message_id = data.get('message_id')
                        if data.get('task_id'):
                            last_task_id = data.get('task_id')
                        
                        event_types[event_type] = event_types.get(event_type, 0) + 1
                        
                        # 核心处理逻辑
                        if event_type in ['message', 'agent_message']:
                            answer = data.get('answer', '')
                            # 使用 StreamBuffer 处理内容，区分正常内容和思考内容
                            normal_content, think_content = stream_buffer.process(answer)
                            
                            # 如果有正常内容，发送正常消息事件
                            if normal_content:
                                data['answer'] = normal_content
                                new_event_str = f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                                yield new_event_str.encode('utf-8')
                            
                            # 如果有思考内容，发送 agent_thought 事件
                            if think_content:
                                thought_data = {
                                    "event": "agent_thought",
                                    "id": data.get('message_id') or data.get('id', ''),
                                    "message_id": data.get('message_id', ''),
                                    "task_id": last_task_id,
                                    "conversation_id": last_conversation_id,
                                    "thought": think_content,
                                    "created_at": int(datetime.now().timestamp())
                                }
                                thought_event_str = f"data: {json.dumps(thought_data, ensure_ascii=False)}\n\n"
                                yield thought_event_str.encode('utf-8')
                            
                        elif event_type in ['message_end', 'workflow_finished']:
                            # 结束前清空缓冲区
                            normal_remaining, think_remaining = stream_buffer.flush()
                            
                            # 发送剩余正常内容
                            if normal_remaining:
                                flush_data = {
                                    "event": "message" if event_type == 'message_end' else 'agent_message',
                                    "answer": normal_remaining,
                                    "conversation_id": last_conversation_id,
                                    "message_id": last_message_id,
                                    "task_id": last_task_id,
                                    "id": data.get("id") # 某些事件可能使用 id
                                }
                                yield f"data: {json.dumps(flush_data, ensure_ascii=False)}\n\n".encode('utf-8')
                            
                            # 发送剩余思考内容
                            if think_remaining:
                                thought_data = {
                                    "event": "agent_thought",
                                    "id": last_message_id or data.get("id", ''),
                                    "message_id": last_message_id,
                                    "task_id": last_task_id,
                                    "conversation_id": last_conversation_id,
                                    "thought": think_remaining,
                                    "created_at": int(datetime.now().timestamp())
                                }
                                thought_event_str = f"data: {json.dumps(thought_data, ensure_ascii=False)}\n\n"
                                yield thought_event_str.encode('utf-8')
                            
                            # 发送原始结束事件（重新规范化为 data: JSON）
                            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n".encode('utf-8')
                            
                        else:
                            # 其他事件直接转发
                            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n".encode('utf-8')
                            
                    except json.JSONDecodeError:
                        # 解析失败：继续等待后续 chunk 补全（不要把半截 JSON 往下游转发）
                        # 将本次 block 放回缓冲区头部并退出循环
                        dify_sse_buffer = event_block + ("\n\n" if sep_len == 2 else "\r\n\r\n") + dify_sse_buffer
                        break
                
                if chunk_count % 10 == 0:
                    logger.debug(f"📦 已处理 {chunk_count} 个 chunks...")

            # 循环结束后，再次检查缓冲区（防止非正常结束）
            normal_remaining, think_remaining = stream_buffer.flush()
            
            # 发送剩余正常内容
            if normal_remaining:
                flush_data = {
                    "event": "message",
                    "answer": normal_remaining,
                    "conversation_id": last_conversation_id,
                    "message_id": last_message_id,
                    "task_id": last_task_id
                }
                yield f"data: {json.dumps(flush_data, ensure_ascii=False)}\n\n".encode('utf-8')
            
            # 发送剩余思考内容
            if think_remaining:
                thought_data = {
                    "event": "agent_thought",
                    "id": last_message_id or '',
                    "message_id": last_message_id,
                    "task_id": last_task_id,
                    "conversation_id": last_conversation_id,
                    "thought": think_remaining,
                    "created_at": int(datetime.now().timestamp())
                }
                thought_event_str = f"data: {json.dumps(thought_data, ensure_ascii=False)}\n\n"
                yield thought_event_str.encode('utf-8')

            if event_types:
                logger.info(f"📊 事件类型统计: {event_types}")
            
            logger.info(f"✅ Agent 对话完成")
            
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
        """
        获取用户的 Agent 会话列表
        
        直接从 Dify API 获取，不再从业务库查询
        """
        # 创建 Dify 客户端
        dify_client = self.dify_client_factory.create_client_from_db(
            agent_config_id, self.db
        )
        
        # 调用 Dify API 获取会话列表
        user_identifier = f"user_{user_id}"
        dify_response = await dify_client.get_conversations(
            user=user_identifier,
            limit=100
        )
        
        # 转换 Dify 响应为业务 Schema
        conversations_data = dify_response.get('data', [])
        result = []
        
        for conv_data in conversations_data:
            # Dify 返回的时间戳是 Unix 时间戳（整数）
            created_at_ts = conv_data.get('created_at', 0)
            updated_at_ts = conv_data.get('updated_at', 0)
            
            # 转换为 ISO 格式字符串
            created_at = datetime.fromtimestamp(created_at_ts).isoformat() if created_at_ts else datetime.now().isoformat()
            updated_at = datetime.fromtimestamp(updated_at_ts).isoformat() if updated_at_ts else datetime.now().isoformat()
            
            result.append(
                AgentConversationResponse(
                    id=conv_data.get('id', ''),
                    agent_config_id=agent_config_id,
                    title=conv_data.get('name', '新对话'),
                    created_at=created_at,
                    updated_at=updated_at,
                    message_count=0,  # Dify API 不返回消息数量，设为 0
                    last_message=None  # Dify API 不返回最后一条消息内容
                )
            )
        
        return result
    
    async def create_conversation(
        self,
        agent_config_id: str,
        user_id: str,
        title: Optional[str] = None
    ) -> AgentConversationResponse:
        """
        创建新会话
        
        不再在业务库创建记录，Dify 会在第一次发送消息时自动创建会话
        这里返回一个占位符响应，实际会话会在 stream_chat 时创建
        """
        # Dify 会在第一次发送消息时自动创建会话
        # 这里返回一个占位符响应
        # 如果需要立即创建会话，可以调用 Dify API，但通常不需要
        
        return AgentConversationResponse(
            id="",  # 空ID，实际会话ID会在第一次消息时由Dify返回
            agent_config_id=agent_config_id,
            title=title or "新对话",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            message_count=0,
            last_message=None
        )
    
    async def get_messages(
        self,
        agent_config_id: str,
        conversation_id: str,
        user_id: str,
        limit: int = 50
    ) -> List[AgentMessageResponse]:
        """
        获取会话消息历史
        
        直接从 Dify API 获取，不再从业务库查询
        """
        # 创建 Dify 客户端
        dify_client = self.dify_client_factory.create_client_from_db(
            agent_config_id, self.db
        )
        
        # 调用 Dify API 获取消息历史
        user_identifier = f"user_{user_id}"
        dify_response = await dify_client.get_conversation_messages(
            user=user_identifier,
            conversation_id=conversation_id,
            limit=limit
        )
        
        # 转换 Dify 响应为业务 Schema
        messages_data = dify_response.get('data', [])
        result = []
        
        for msg_data in messages_data:
            # Dify 返回的时间戳是 Unix 时间戳（整数）
            created_at_ts = msg_data.get('created_at', 0)
            base_timestamp = datetime.fromtimestamp(created_at_ts) if created_at_ts else datetime.now()
            
            # Dify 消息格式：query 是用户消息，answer 是 AI 回复
            # 需要将一条 Dify 消息拆分为两条业务消息（用户消息 + AI 回复）
            query = msg_data.get('query', '')
            answer = msg_data.get('answer', '')
            
            # 如果有用户消息，添加用户消息（时间戳稍早，确保排在 AI 回复之前）
            if query:
                user_timestamp = (base_timestamp - timedelta(seconds=1)).isoformat()
                result.append(
                    AgentMessageResponse(
                        id=f"{msg_data.get('id', '')}_user",
                        conversation_id=conversation_id,
                        content=query,
                        is_answer=False,
                        timestamp=user_timestamp,
                        agent_thoughts=None,
                        files=msg_data.get('message_files'),
                        is_error=False
                    )
                )
            
            # 如果有 AI 回复，添加 AI 回复（使用原始时间戳）
            if answer:
                answer_timestamp = base_timestamp.isoformat()
                result.append(
                    AgentMessageResponse(
                        id=msg_data.get('id', ''),
                        conversation_id=conversation_id,
                        content=answer,
                        is_answer=True,
                        timestamp=answer_timestamp,
                        agent_thoughts=None,  # TODO: 从 Dify 响应中解析 agent_thoughts
                        files=None,
                        is_error=False
                    )
                )
        
        # 按时间戳排序（正序：最早的在前）
        # 如果时间戳相同，用户消息（is_answer=False）排在 AI 回复（is_answer=True）之前
        def get_sort_key(msg: AgentMessageResponse):
            try:
                # 解析 ISO 格式的时间戳
                ts = datetime.fromisoformat(msg.timestamp.replace('Z', '+00:00'))
                return (ts.timestamp(), 1 if msg.is_answer else 0)  # 用户消息优先
            except (ValueError, AttributeError):
                # 如果解析失败，使用默认值
                return (0.0, 1 if msg.is_answer else 0)
        
        result.sort(key=get_sort_key)
        
        return result
    
    async def delete_conversation(
        self,
        agent_config_id: str,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """
        删除会话
        
        直接调用 Dify API 删除，不再操作业务库
        """
        # 创建 Dify 客户端
        dify_client = self.dify_client_factory.create_client_from_db(
            agent_config_id, self.db
        )
        
        # 调用 Dify API 删除会话
        user_identifier = f"user_{user_id}"
        await dify_client.delete_conversation(
            conversation_id=conversation_id,
            user=user_identifier
        )
        
        return True
    
    async def update_conversation(
        self,
        agent_config_id: str,
        conversation_id: str,
        user_id: str,
        title: str
    ) -> AgentConversationResponse:
        """
        更新会话
        
        直接调用 Dify API 更新，不再操作业务库
        """
        # 创建 Dify 客户端
        dify_client = self.dify_client_factory.create_client_from_db(
            agent_config_id, self.db
        )
        
        # 调用 Dify API 重命名会话
        user_identifier = f"user_{user_id}"
        dify_response = await dify_client.rename_conversation(
            conversation_id=conversation_id,
            name=title,
            user=user_identifier,
            auto_generate=False
        )
        
        # 转换 Dify 响应为业务 Schema
        created_at_ts = dify_response.get('created_at', 0)
        updated_at_ts = dify_response.get('updated_at', 0)
        
        created_at = datetime.fromtimestamp(created_at_ts).isoformat() if created_at_ts else datetime.now().isoformat()
        updated_at = datetime.fromtimestamp(updated_at_ts).isoformat() if updated_at_ts else datetime.now().isoformat()
        
        return AgentConversationResponse(
            id=dify_response.get('id', conversation_id),
            agent_config_id=agent_config_id,
            title=dify_response.get('name', title),
            created_at=created_at,
            updated_at=updated_at,
            message_count=0,  # Dify API 不返回消息数量
            last_message=None
        )
    
    # ========== 私有辅助方法 ==========
    
    # 已移除 _create_conversation 方法，不再在业务库创建会话
    
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
            message_id: Dify 的消息ID（直接使用 Dify 的 message_id）
            rating: 评分 ('like' 或 'dislike')
            user_id: 用户ID
        
        Returns:
            反馈结果
        """
        logger.info(f"提交消息反馈: dify_message_id={message_id}, rating={rating}")
        
        # 创建 Dify 客户端
        dify_client = self.dify_client_factory.create_client_from_db(
            agent_config_id, self.db
        )
        
        # 直接调用 Dify API（message_id 已经是 Dify 的 message_id）
        user_identifier = f"user_{user_id}"
        result = await dify_client.message_feedback(
            message_id=message_id,  # 直接使用 Dify message_id
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
            message_id: Dify 的消息ID（直接使用 Dify 的 message_id）
            user_id: 用户ID
        
        Returns:
            建议问题列表
        """
        logger.info(f"获取建议问题: dify_message_id={message_id}")
        
        try:
            # 1. 首先获取应用参数配置
            app_params = await self.get_application_parameters(
                agent_config_id=agent_config_id,
                user_id=user_id
            )
            
            # 2. 检查建议问题配置是否启用
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
            
            # 3. 创建 Dify 客户端
            dify_client = self.dify_client_factory.create_client_from_db(
                agent_config_id, self.db
            )
            
            # 4. 调用 Dify API 获取建议问题（直接使用 Dify message_id）
            user_identifier = f"user_{user_id}"
            result = await dify_client.get_suggested(
                message_id=message_id,  # 直接使用 Dify message_id
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
        # Dify 原生格式: [{"text-input": {...}}, {"number": {...}}]
        # 目标格式: [{"type": "text-input", ...}, {"type": "number", ...}]
        if "user_input_form" in result and isinstance(result["user_input_form"], list):
            logger.debug(f"📥 Dify 原始 user_input_form: {json.dumps(result['user_input_form'], ensure_ascii=False)}")
            
            transformed_form = []
            for item in result["user_input_form"]:
                if isinstance(item, dict):
                    # 获取嵌套的字段配置，键名就是字段类型
                    for field_type_key, field_config in item.items():
                        if isinstance(field_config, dict):
                            # 将类型作为 type 属性添加到配置中
                            field_config["type"] = field_type_key
                            transformed_form.append(field_config)
                            logger.debug(f"📝 转换字段: {field_type_key} -> {field_config}")
                            break
                else:
                    # 如果已经是正确的结构，直接使用
                    transformed_form.append(item)
            
            result["user_input_form"] = transformed_form
            logger.info(f"✅ 转换后的 user_input_form: {json.dumps(transformed_form, ensure_ascii=False)}")
        
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
