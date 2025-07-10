"""
API密钥加密存储工具
使用Fernet对称加密确保敏感信息安全存储
"""
import base64
import os
import logging
from typing import Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class APIKeyEncryption:
    """API密钥加密解密工具类"""
    
    def __init__(self):
        """初始化加密器"""
        self._fernet = None
        self._init_encryption()
    
    def _init_encryption(self) -> None:
        """初始化Fernet加密器"""
        try:
            # 从环境变量获取加密密钥，如果没有则生成
            encryption_key = os.environ.get("ENCRYPTION_KEY")
            
            if not encryption_key:
                # 使用应用密钥和盐生成加密密钥
                password = settings.SECRET_KEY.encode()
                salt = b"anmeismart_encryption_salt_2025"  # 固定盐值，确保一致性
                
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password))
                self._fernet = Fernet(key)
                
                logger.warning("使用派生密钥进行加密，建议设置环境变量 ENCRYPTION_KEY")
            else:
                # 验证提供的密钥格式
                try:
                    self._fernet = Fernet(encryption_key.encode())
                except Exception as e:
                    logger.error(f"提供的加密密钥格式无效: {e}")
                    raise ValueError("无效的加密密钥格式")
                    
        except Exception as e:
            logger.error(f"初始化加密器失败: {e}")
            raise
    
    def encrypt(self, plaintext: Union[str, bytes]) -> str:
        """
        加密明文
        
        Args:
            plaintext: 要加密的明文（字符串或字节）
            
        Returns:
            str: Base64编码的加密字符串
        """
        if not plaintext:
            return ""
        
        try:
            # 确保输入是字节类型
            if isinstance(plaintext, str):
                plaintext = plaintext.encode('utf-8')
            
            # 加密数据
            encrypted_data = self._fernet.encrypt(plaintext)
            
            # 返回Base64编码的字符串
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise ValueError(f"加密操作失败: {str(e)}")
    
    def decrypt(self, encrypted_text: str) -> str:
        """
        解密密文
        
        Args:
            encrypted_text: Base64编码的加密字符串
            
        Returns:
            str: 解密后的明文字符串
        """
        if not encrypted_text:
            return ""
        
        try:
            # Base64解码
            encrypted_data = base64.urlsafe_b64decode(encrypted_text.encode('utf-8'))
            
            # 解密数据
            decrypted_data = self._fernet.decrypt(encrypted_data)
            
            # 返回UTF-8字符串
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise ValueError(f"解密操作失败: {str(e)}")
    
    def is_encrypted(self, text: str) -> bool:
        """
        检查文本是否已加密
        
        Args:
            text: 要检查的文本
            
        Returns:
            bool: True表示已加密，False表示未加密
        """
        if not text:
            return False
        
        try:
            # 尝试解密来判断是否已加密
            self.decrypt(text)
            return True
        except (ValueError, Exception):
            return False
    
    def ensure_encrypted(self, text: str) -> str:
        """
        确保文本被加密（如果未加密则加密）
        
        Args:
            text: 要处理的文本
            
        Returns:
            str: 加密后的文本
        """
        if not text:
            return ""
        
        if self.is_encrypted(text):
            return text
        else:
            return self.encrypt(text)
    
    def safe_decrypt(self, encrypted_text: str) -> str:
        """
        安全解密（如果解密失败则返回原文）
        用于向后兼容未加密的数据
        
        Args:
            encrypted_text: 可能已加密的文本
            
        Returns:
            str: 解密后的明文或原文
        """
        if not encrypted_text:
            return ""
        
        try:
            return self.decrypt(encrypted_text)
        except (ValueError, Exception):
            # 解密失败，可能是未加密的数据，直接返回
            logger.warning("解密失败，返回原文（可能是未加密数据）")
            return encrypted_text
    
    @staticmethod
    def generate_key() -> str:
        """
        生成新的Fernet密钥
        
        Returns:
            str: Base64编码的密钥字符串
        """
        key = Fernet.generate_key()
        return key.decode('utf-8')


# 全局加密器实例
_encryption_instance: Optional[APIKeyEncryption] = None


def get_encryption() -> APIKeyEncryption:
    """
    获取全局加密器实例（单例模式）
    
    Returns:
        APIKeyEncryption: 加密器实例
    """
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = APIKeyEncryption()
    return _encryption_instance


def encrypt_api_key(api_key: str) -> str:
    """
    加密API密钥的便利函数
    
    Args:
        api_key: 要加密的API密钥
        
    Returns:
        str: 加密后的API密钥
    """
    return get_encryption().encrypt(api_key)


def decrypt_api_key(encrypted_api_key: str) -> str:
    """
    解密API密钥的便利函数
    
    Args:
        encrypted_api_key: 加密的API密钥
        
    Returns:
        str: 解密后的API密钥
    """
    return get_encryption().decrypt(encrypted_api_key)


def safe_decrypt_api_key(encrypted_api_key: str) -> str:
    """
    安全解密API密钥的便利函数（向后兼容）
    
    Args:
        encrypted_api_key: 可能已加密的API密钥
        
    Returns:
        str: 解密后的API密钥或原文
    """
    return get_encryption().safe_decrypt(encrypted_api_key) 