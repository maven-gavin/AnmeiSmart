import re
from typing import Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)

class StreamBuffer:
    """
    流式缓冲区，用于处理被分割的特殊标签
    优化：支持思考过程（<think>）的实时流式输出
    一旦检测到开始标签，立即流式输出内容，而不是等待标签闭合
    """
    
    OPEN_TAG = "<think>"
    CLOSE_TAG = "</think>"
    
    def __init__(self):
        self.buffer = ""
        self.in_reasoning_tag = False  # 是否在思考标签内部
        self.pending_tag_start = ""  # 可能被截断的开始标签
        
    def process(self, chunk: str) -> Tuple[str, str]:
        """
        处理新的文本块，区分正常内容和思考内容
        
        Returns:
            tuple: (normal_content, think_content)
            - normal_content: 正常内容（不包含思考过程）
            - think_content: 思考过程内容（流式输出，可能为空）
        """
        self.buffer += chunk
        normal_output = []
        think_output = []
        
        while self.buffer:
            if self.in_reasoning_tag:
                # 在思考标签内部，查找结束标签
                close_idx = self.buffer.find(self.CLOSE_TAG)
                if close_idx != -1:
                    # 找到结束标签，输出思考内容并关闭标签
                    content = self.buffer[:close_idx]
                    think_output.append(content)
                    self.buffer = self.buffer[close_idx + len(self.CLOSE_TAG):]
                    self.in_reasoning_tag = False
                else:
                    # 未找到结束标签，检查末尾是否可能被截断
                    # 如果末尾是 "</redacted_reasoning" 的一部分，保留在缓冲区
                    if len(self.buffer) >= len(self.CLOSE_TAG):
                        # 检查末尾是否可能是结束标签的开头
                        check_len = min(len(self.CLOSE_TAG) - 1, len(self.buffer))
                        if self.buffer[-check_len:] == self.CLOSE_TAG[:check_len]:
                            # 可能是被截断的结束标签，保留末尾
                            safe_len = len(self.buffer) - check_len
                            if safe_len > 0:
                                think_output.append(self.buffer[:safe_len])
                            self.buffer = self.buffer[safe_len:]
                            break
                    
                    # 没有截断风险，输出所有思考内容
                    think_output.append(self.buffer)
                    self.buffer = ""
                    break
            else:
                # 不在思考标签内部，查找开始标签
                # 先检查缓冲区中是否有完整的开始标签
                open_idx = self.buffer.find(self.OPEN_TAG)
                if open_idx != -1:
                    # 找到开始标签，输出之前的内容（正常内容）
                    if open_idx > 0:
                        normal_output.append(self.buffer[:open_idx])
                    self.buffer = self.buffer[open_idx + len(self.OPEN_TAG):]
                    self.in_reasoning_tag = True
                else:
                    # 未找到开始标签，检查末尾是否可能被截断的开始标签
                    # 查找最后一个 '<' 的位置
                    last_open_idx = self.buffer.rfind('<')
                    if last_open_idx != -1:
                        # 检查从 last_open_idx 开始的内容是否可能是开始标签
                        potential_tag = self.buffer[last_open_idx:]
                        # 检查是否可能是被截断的开始标签
                        if len(potential_tag) < len(self.OPEN_TAG):
                            # 检查是否匹配开始标签的前缀
                            if self.OPEN_TAG.startswith(potential_tag):
                                # 可能是被截断的开始标签，保留在缓冲区
                                if last_open_idx > 0:
                                    normal_output.append(self.buffer[:last_open_idx])
                                self.buffer = self.buffer[last_open_idx:]
                                break
                        
                        # 检查是否可能是被截断的结束标签（虽然不在标签内，但可能是误判）
                        if len(potential_tag) < len(self.CLOSE_TAG):
                            if self.CLOSE_TAG.startswith(potential_tag):
                                # 可能是被截断的结束标签，保留在缓冲区
                                if last_open_idx > 0:
                                    normal_output.append(self.buffer[:last_open_idx])
                                self.buffer = self.buffer[last_open_idx:]
                                break
                        
                        # 检查是否可能是完整的开始标签（但被其他字符分隔）
                        # 这种情况不应该发生，但为了安全起见，检查一下
                        if potential_tag.startswith('<') and '>' in potential_tag:
                            # 可能是一个完整的标签，但不是我们要找的开始标签
                            # 输出到标签之前的内容
                            tag_end = potential_tag.find('>')
                            if tag_end != -1:
                                # 找到了一个完整的标签，但不是我们的开始标签
                                # 输出到标签结束之后
                                safe_end = last_open_idx + tag_end + 1
                                if safe_end > 0:
                                    normal_output.append(self.buffer[:safe_end])
                                self.buffer = self.buffer[safe_end:]
                                continue
                    
                    # 没有截断风险，输出所有内容（正常内容）
                    normal_output.append(self.buffer)
                    self.buffer = ""
                    break
        
        return ("".join(normal_output), "".join(think_output))

    def flush(self) -> Tuple[str, str]:
        """
        强制清空缓冲区，返回剩余内容
        
        Returns:
            tuple: (normal_content, think_content)
        """
        if self.in_reasoning_tag:
            # 如果还在思考标签内，剩余内容是思考内容
            think_content = self.buffer
            normal_content = ""
        else:
            # 否则是正常内容
            normal_content = self.buffer
            think_content = ""
        
        self.buffer = ""
        self.in_reasoning_tag = False
        self.pending_tag_start = ""
        return (normal_content, think_content)

