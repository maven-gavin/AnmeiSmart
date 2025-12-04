import re
from typing import Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)

class StreamBuffer:
    """
    流式缓冲区，用于处理被分割的特殊标签
    确保发送给前端的内容不会包含被截断的标签，避免前端解析闪烁
    """
    
    def __init__(self):
        self.buffer = ""
        # 需要保护的标签列表
        self.tags = ["<think>", "</think>"]
        
    def process(self, chunk: str) -> str:
        """
        处理新的文本块
        
        Returns:
            safe_text: 可以安全发送给前端的文本
        """
        self.buffer += chunk
        
        # 检查缓冲区末尾是否有潜在的被截断的标签
        # 我们只需要确保不发送像 "<", "<t", "<think" 这样的不完整标签
        # 一旦标签完整（如 "<think>"），就可以发送
        
        # 1. 如果缓冲区为空，直接返回
        if not self.buffer:
            return ""
            
        # 2. 查找最后一个 '<' 的位置
        last_open_idx = self.buffer.rfind('<')
        
        # 如果没有 '<'，或者 '<' 后面有 '>' (说明标签已闭合)，则整个缓冲区都是安全的
        # 注意：这里简化处理，假设没有嵌套标签或复杂属性
        if last_open_idx == -1:
            safe_text = self.buffer
            self.buffer = ""
            return safe_text
            
        # 3. 检查最后一个 '<' 后的内容
        # 如果从 last_open_idx 开始的内容是一个完整的标签（包含 '>'），则安全
        # 否则，它可能是一个被截断的标签，需要保留在缓冲区
        
        potential_tag = self.buffer[last_open_idx:]
        if '>' in potential_tag:
            # 标签已闭合，安全
            safe_text = self.buffer
            self.buffer = ""
            return safe_text
        else:
            # 标签未闭合，保留 last_open_idx 之后的内容
            safe_text = self.buffer[:last_open_idx]
            self.buffer = self.buffer[last_open_idx:]
            return safe_text

    def flush(self) -> str:
        """
        强制清空缓冲区
        """
        remaining = self.buffer
        self.buffer = ""
        return remaining

