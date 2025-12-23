"""
企业微信消息加解密工具
参考：https://developer.work.weixin.qq.com/document/path/90930
"""
import base64
import hashlib
import struct
import logging
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class WeChatWorkCrypto:
    """企业微信消息加解密工具类"""
    
    def __init__(self, token: str, encoding_aes_key: str, corp_id: str):
        """
        初始化加解密工具
        
        Args:
            token: 企业微信配置的Token
            encoding_aes_key: 企业微信配置的EncodingAESKey（43位Base64字符串）
            corp_id: 企业ID
        """
        self.token = token
        self.corp_id = corp_id
        
        # 将EncodingAESKey转换为AES密钥（32字节）
        # 43位Base64字符串，需要补齐到44位（添加1个=）
        try:
            # 补齐Base64填充（43位需要1个=，44位需要2个==）
            padding_needed = 4 - (len(encoding_aes_key) % 4)
            if padding_needed == 4:
                padding_needed = 0
            padded_key = encoding_aes_key + ("=" * padding_needed)
            aes_key = base64.b64decode(padded_key)
            if len(aes_key) != 32:
                raise ValueError(f"EncodingAESKey长度错误，应为32字节，实际为{len(aes_key)}字节")
            self.aes_key = aes_key
            logger.debug(f"成功初始化AES密钥，长度: {len(aes_key)}字节")
        except Exception as e:
            raise ValueError(f"无效的EncodingAESKey: {e}")
    
    def verify_signature(self, msg_signature: str, timestamp: str, nonce: str, value: str) -> bool:
        """
        验证企业微信签名
        
        签名算法：SHA1(排序[token, timestamp, nonce, value])
        
        Args:
            msg_signature: 企业微信发送的签名
            timestamp: 时间戳
            nonce: 随机数
            value: echostr(验证) 或 Encrypt(消息体加密字段)
            
        Returns:
            验证是否通过
        """
        try:
            # 按字典序排序并拼接
            sorted_list = sorted([self.token, timestamp, nonce, value])
            signature_str = "".join(sorted_list)
            
            logger.debug(f"签名计算: token={self.token[:10]}..., timestamp={timestamp}, nonce={nonce}, value={value[:20]}...")
            logger.debug(f"排序后字符串: {signature_str[:50]}...")
            
            # SHA1哈希
            sha1_hash = hashlib.sha1(signature_str.encode('utf-8')).hexdigest()
            
            # 比较签名
            is_valid = sha1_hash == msg_signature
            if not is_valid:
                logger.warning(f"签名验证失败: 期望={sha1_hash}, 实际={msg_signature}")
                logger.warning(f"签名计算字符串: {signature_str}")
            else:
                logger.info(f"签名验证成功: {sha1_hash}")
            return is_valid
        except Exception as e:
            logger.error(f"签名验证异常: {e}", exc_info=True)
            return False

    def decrypt_echostr(self, encrypted_echostr: str) -> Optional[str]:
        """解密企业微信 echostr（回调配置校验用）"""
        plaintext = self._decrypt_ciphertext_flexible(encrypted_echostr)
        if not plaintext:
            return None
        msg, _corp_id = self._parse_wechat_plaintext(plaintext)
        return msg

    def decrypt_encrypt_field(self, encrypt_b64: str) -> Optional[str]:
        """解密回调消息体中的 Encrypt 字段，返回明文 XML/JSON 字符串"""
        plaintext = self._decrypt_ciphertext_flexible(encrypt_b64)
        if not plaintext:
            return None
        msg, _corp_id = self._parse_wechat_plaintext(plaintext)
        return msg

    def _decrypt_ciphertext_flexible(self, cipher_b64: str) -> Optional[bytes]:
        """
        解密 base64(ciphertext)
        - 优先使用企业微信标准 iv = aes_key[:16]
        - 兼容旧实现：如果 cipher_b64 实际包含 iv+密文，则回退到 iv=前16字节
        """
        try:
            cipher_bytes = base64.b64decode(cipher_b64)
        except Exception:
            logger.error("cipher_b64 base64解码失败", exc_info=True)
            return None

        # 标准实现：iv = key[:16]，cipher_bytes 全量为密文
        try:
            iv = self.aes_key[:16]
            cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(cipher_bytes) + decryptor.finalize()
            decrypted = self._pkcs7_unpad(decrypted)
            return decrypted
        except Exception as e:
            logger.warning(f"标准解密失败，回退兼容模式: {e}")

        # 兼容实现：iv = cipher_bytes[:16]，密文 = cipher_bytes[16:]
        try:
            if len(cipher_bytes) < 32:
                return None
            iv = cipher_bytes[:16]
            cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(cipher_bytes[16:]) + decryptor.finalize()
            decrypted = self._pkcs7_unpad(decrypted)
            return decrypted
        except Exception:
            logger.error("兼容模式解密也失败", exc_info=True)
            return None

    @staticmethod
    def _pkcs7_unpad(data: bytes) -> bytes:
        if not data:
            raise ValueError("empty decrypted data")
        pad = data[-1]
        # 调试日志：记录解密后的末尾字节
        logger.debug(f"PKCS7 解填充: data_len={len(data)}, pad_value={pad}, last_16_bytes={data[-16:].hex()}")
        
        # 企业微信使用 32 字节作为填充块大小
        if pad < 1 or pad > 32:
            raise ValueError(f"invalid pkcs7 padding value: {pad}")
        if len(data) < pad:
            raise ValueError("invalid pkcs7 padding length")
        
        # 验证填充内容是否一致
        padding = data[-pad:]
        if any(p != pad for p in padding):
            # 记录具体的填充内容以便排查
            logger.warning(f"填充内容验证失败: pad={pad}, padding={padding.hex()}")
            raise ValueError("invalid pkcs7 padding content")
            
        return data[:-pad]

    @staticmethod
    def _parse_wechat_plaintext(plaintext: bytes) -> Tuple[str, Optional[str]]:
        """
        明文结构：
        - random(16 bytes)
        - msg_len(4 bytes, network byte order)
        - msg(msg_len bytes)
        - corp_id(remaining bytes)
        """
        if len(plaintext) < 20:
            raise ValueError("plaintext too short")
        content = plaintext[16:]
        msg_len = struct.unpack(">I", content[:4])[0]
        msg_bytes = content[4:4 + msg_len]
        corp_bytes = content[4 + msg_len:]
        msg = msg_bytes.decode("utf-8", errors="ignore")
        corp_id = corp_bytes.decode("utf-8", errors="ignore") if corp_bytes else None
        return msg, corp_id
    
    # 旧 decrypt_echostr 已由新实现替代（保留接口兼容）

