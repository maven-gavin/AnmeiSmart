"""
API密钥加密存储测试
测试加密解密功能、安全性和边界情况
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet

from app.core.encryption import (
    APIKeyEncryption,
    get_encryption,
    encrypt_api_key,
    decrypt_api_key,
    safe_decrypt_api_key
)


class TestAPIKeyEncryption:
    """API密钥加密类测试"""
    
    def test_encrypt_decrypt_basic(self):
        """测试基本的加密解密功能"""
        encryption = APIKeyEncryption()
        
        # 测试字符串加密解密
        original_text = "sk-1234567890abcdef"
        encrypted = encryption.encrypt(original_text)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == original_text
        assert encrypted != original_text
        assert len(encrypted) > len(original_text)
    
    def test_encrypt_empty_string(self):
        """测试空字符串加密"""
        encryption = APIKeyEncryption()
        
        assert encryption.encrypt("") == ""
        assert encryption.encrypt(None) == ""
        assert encryption.decrypt("") == ""
    
    def test_encrypt_bytes(self):
        """测试字节类型加密"""
        encryption = APIKeyEncryption()
        
        original_bytes = b"binary_api_key_data"
        encrypted = encryption.encrypt(original_bytes)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == original_bytes.decode('utf-8')
    
    def test_is_encrypted_detection(self):
        """测试加密检测功能"""
        encryption = APIKeyEncryption()
        
        plain_text = "plain_api_key"
        encrypted_text = encryption.encrypt(plain_text)
        
        assert not encryption.is_encrypted(plain_text)
        assert encryption.is_encrypted(encrypted_text)
        assert not encryption.is_encrypted("")
        assert not encryption.is_encrypted("invalid_base64!")
    
    def test_ensure_encrypted(self):
        """测试确保加密功能"""
        encryption = APIKeyEncryption()
        
        plain_text = "api_key_to_encrypt"
        
        # 第一次调用应该加密
        encrypted1 = encryption.ensure_encrypted(plain_text)
        assert encryption.is_encrypted(encrypted1)
        
        # 第二次调用应该返回相同的加密文本（已加密）
        encrypted2 = encryption.ensure_encrypted(encrypted1)
        assert encrypted1 == encrypted2
        
        # 解密后应该得到原文
        decrypted = encryption.decrypt(encrypted1)
        assert decrypted == plain_text
    
    def test_safe_decrypt(self):
        """测试安全解密功能"""
        encryption = APIKeyEncryption()
        
        # 已加密的数据
        plain_text = "encrypted_api_key"
        encrypted_text = encryption.encrypt(plain_text)
        assert encryption.safe_decrypt(encrypted_text) == plain_text
        
        # 未加密的数据（向后兼容）
        unencrypted_text = "unencrypted_api_key"
        assert encryption.safe_decrypt(unencrypted_text) == unencrypted_text
        
        # 空字符串
        assert encryption.safe_decrypt("") == ""
    
    def test_encryption_with_custom_key(self):
        """测试自定义加密密钥"""
        custom_key = Fernet.generate_key().decode('utf-8')
        
        with patch.dict(os.environ, {'ENCRYPTION_KEY': custom_key}):
            encryption = APIKeyEncryption()
            
            original_text = "custom_key_test"
            encrypted = encryption.encrypt(original_text)
            decrypted = encryption.decrypt(encrypted)
            
            assert decrypted == original_text
    
    def test_invalid_custom_key(self):
        """测试无效的自定义加密密钥"""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': 'invalid_key_format'}):
            with pytest.raises(ValueError, match="无效的加密密钥格式"):
                APIKeyEncryption()
    
    def test_decrypt_invalid_data(self):
        """测试解密无效数据"""
        encryption = APIKeyEncryption()
        
        with pytest.raises(ValueError, match="解密操作失败"):
            encryption.decrypt("invalid_encrypted_data")
        
        with pytest.raises(ValueError, match="解密操作失败"):
            encryption.decrypt("not_base64_data!")
    
    def test_generate_key(self):
        """测试密钥生成"""
        key = APIKeyEncryption.generate_key()
        
        assert isinstance(key, str)
        assert len(key) > 0
        
        # 生成的密钥应该能用于创建Fernet实例
        fernet = Fernet(key.encode())
        assert fernet is not None
    
    def test_consistency_across_instances(self):
        """测试多个实例间的一致性"""
        encryption1 = APIKeyEncryption()
        encryption2 = APIKeyEncryption()
        
        original_text = "consistency_test"
        encrypted = encryption1.encrypt(original_text)
        decrypted = encryption2.decrypt(encrypted)
        
        assert decrypted == original_text


class TestGlobalEncryptionFunctions:
    """全局加密函数测试"""
    
    def test_get_encryption_singleton(self):
        """测试单例模式"""
        encryption1 = get_encryption()
        encryption2 = get_encryption()
        
        assert encryption1 is encryption2
    
    def test_encrypt_api_key_function(self):
        """测试API密钥加密便利函数"""
        api_key = "sk-test1234567890"
        encrypted = encrypt_api_key(api_key)
        
        assert encrypted != api_key
        assert get_encryption().is_encrypted(encrypted)
    
    def test_decrypt_api_key_function(self):
        """测试API密钥解密便利函数"""
        api_key = "sk-test1234567890"
        encrypted = encrypt_api_key(api_key)
        decrypted = decrypt_api_key(encrypted)
        
        assert decrypted == api_key
    
    def test_safe_decrypt_api_key_function(self):
        """测试安全解密便利函数"""
        # 已加密的密钥
        api_key = "sk-encrypted1234567890"
        encrypted = encrypt_api_key(api_key)
        decrypted = safe_decrypt_api_key(encrypted)
        assert decrypted == api_key
        
        # 未加密的密钥（向后兼容）
        unencrypted_key = "sk-unencrypted1234567890"
        result = safe_decrypt_api_key(unencrypted_key)
        assert result == unencrypted_key


class TestEncryptionSecurity:
    """加密安全性测试"""
    
    def test_different_encryptions_of_same_text(self):
        """测试相同文本的不同加密结果"""
        encryption = APIKeyEncryption()
        
        text = "same_text_test"
        encrypted1 = encryption.encrypt(text)
        encrypted2 = encryption.encrypt(text)
        
        # 由于Fernet使用随机IV，相同文本的加密结果应该不同
        assert encrypted1 != encrypted2
        
        # 但都应该能正确解密
        assert encryption.decrypt(encrypted1) == text
        assert encryption.decrypt(encrypted2) == text
    
    def test_encrypted_text_not_readable(self):
        """测试加密文本不可读"""
        encryption = APIKeyEncryption()
        
        sensitive_text = "very_secret_api_key_12345"
        encrypted = encryption.encrypt(sensitive_text)
        
        # 加密文本中不应包含原文
        assert sensitive_text not in encrypted
        assert "secret" not in encrypted.lower()
        assert "api" not in encrypted.lower()
    
    def test_encryption_length_security(self):
        """测试加密长度安全性"""
        encryption = APIKeyEncryption()
        
        # 不同长度的输入应该产生不同长度的输出
        short_text = "sk-123"
        long_text = "sk-" + "a" * 100
        
        encrypted_short = encryption.encrypt(short_text)
        encrypted_long = encryption.encrypt(long_text)
        
        # 加密文本长度应该大于原文
        assert len(encrypted_short) > len(short_text)
        assert len(encrypted_long) > len(long_text)


class TestEncryptionEdgeCases:
    """加密边界情况测试"""
    
    def test_unicode_text_encryption(self):
        """测试Unicode文本加密"""
        encryption = APIKeyEncryption()
        
        unicode_text = "API密钥🔐测试文本"
        encrypted = encryption.encrypt(unicode_text)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == unicode_text
    
    def test_very_long_text_encryption(self):
        """测试长文本加密"""
        encryption = APIKeyEncryption()
        
        long_text = "api_key_" + "x" * 10000
        encrypted = encryption.encrypt(long_text)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == long_text
    
    def test_special_characters_encryption(self):
        """测试特殊字符加密"""
        encryption = APIKeyEncryption()
        
        special_text = "sk-!@#$%^&*()_+-=[]{}|;':\",./<>?"
        encrypted = encryption.encrypt(special_text)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == special_text


@pytest.mark.asyncio
class TestEncryptionPerformance:
    """加密性能测试"""
    
    async def test_encryption_performance(self):
        """测试加密性能"""
        encryption = APIKeyEncryption()
        
        # 测试批量加密性能
        texts = [f"api_key_{i}" for i in range(100)]
        
        import time
        start_time = time.time()
        
        encrypted_texts = [encryption.encrypt(text) for text in texts]
        
        encryption_time = time.time() - start_time
        
        # 测试批量解密性能
        start_time = time.time()
        
        decrypted_texts = [encryption.decrypt(encrypted) for encrypted in encrypted_texts]
        
        decryption_time = time.time() - start_time
        
        # 验证正确性
        assert decrypted_texts == texts
        
        # 性能检查（100个密钥加密+解密应该在1秒内完成）
        total_time = encryption_time + decryption_time
        assert total_time < 1.0, f"加密解密耗时过长: {total_time}秒"
    
    def test_singleton_performance(self):
        """测试单例模式性能"""
        import time
        
        start_time = time.time()
        
        # 多次获取实例应该很快
        instances = [get_encryption() for _ in range(1000)]
        
        end_time = time.time()
        
        # 所有实例应该是同一个对象
        assert all(instance is instances[0] for instance in instances)
        
        # 1000次获取应该在0.1秒内完成
        assert (end_time - start_time) < 0.1 