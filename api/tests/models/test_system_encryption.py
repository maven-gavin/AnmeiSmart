"""
数据库模型加密存储测试
测试DifyConnection和AIModelConfig的API密钥加密功能
"""
import pytest
from sqlalchemy.orm import Session
from unittest.mock import patch

from app.db.models.system import DifyConnection, AIModelConfig, AgentType, SyncStatus
from app.core.encryption import get_encryption
from app.db.uuid_utils import system_id, model_id


class TestDifyConnectionEncryption:
    """DifyConnection模型加密测试"""
    
    def test_api_key_encryption_on_set(self, db: Session):
        """测试设置API密钥时自动加密"""
        connection = DifyConnection(
            name="测试连接",
            api_base_url="https://test.example.com",
            api_key="sk-test1234567890"  # 这会自动加密
        )
        
        db.add(connection)
        db.commit()
        db.refresh(connection)
        
        # 检查存储的是加密值
        encrypted_value = connection.get_api_key_encrypted()
        assert encrypted_value != "sk-test1234567890"
        assert len(encrypted_value) > len("sk-test1234567890")
        
        # 检查通过属性访问得到的是解密值
        assert connection.api_key == "sk-test1234567890"
    
    def test_api_key_decryption_on_get(self, db: Session):
        """测试获取API密钥时自动解密"""
        connection = DifyConnection(
            name="测试连接2",
            api_base_url="https://test2.example.com"
        )
        
        # 直接设置加密值
        encryption = get_encryption()
        encrypted_key = encryption.encrypt("sk-encrypted-test")
        connection.set_api_key_raw(encrypted_key)
        
        db.add(connection)
        db.commit()
        db.refresh(connection)
        
        # 通过属性访问应该得到解密值
        assert connection.api_key == "sk-encrypted-test"
    
    def test_empty_api_key_handling(self, db: Session):
        """测试空API密钥处理"""
        connection = DifyConnection(
            name="空密钥连接",
            api_base_url="https://empty.example.com",
            api_key=""
        )
        
        db.add(connection)
        db.commit()
        db.refresh(connection)
        
        assert connection.api_key == ""
        assert connection.get_api_key_encrypted() == ""
    
    def test_api_key_update(self, db: Session):
        """测试API密钥更新"""
        connection = DifyConnection(
            name="更新测试连接",
            api_base_url="https://update.example.com",
            api_key="sk-original-key"
        )
        
        db.add(connection)
        db.commit()
        
        # 更新密钥
        connection.api_key = "sk-updated-key"
        db.commit()
        db.refresh(connection)
        
        # 验证更新后的值
        assert connection.api_key == "sk-updated-key"
        
        # 验证存储的是新的加密值
        encrypted_value = connection.get_api_key_encrypted()
        encryption = get_encryption()
        decrypted = encryption.decrypt(encrypted_value)
        assert decrypted == "sk-updated-key"
    
    def test_backward_compatibility(self, db: Session):
        """测试向后兼容性（未加密的数据）"""
        connection = DifyConnection(
            name="兼容性测试",
            api_base_url="https://compat.example.com"
        )
        
        # 模拟旧数据（未加密）
        connection.set_api_key_raw("sk-unencrypted-old-key")
        
        db.add(connection)
        db.commit()
        db.refresh(connection)
        
        # 应该能正确返回未加密的数据
        assert connection.api_key == "sk-unencrypted-old-key"


class TestAIModelConfigEncryption:
    """AIModelConfig模型加密测试"""
    
    def test_api_key_encryption_optional(self, db: Session):
        """测试可选API密钥加密"""
        config = AIModelConfig(
            model_name="测试模型",
            provider="openai",
            api_key="sk-openai-test-key"
        )
        
        db.add(config)
        db.commit()
        db.refresh(config)
        
        # 检查加密存储
        assert config.api_key == "sk-openai-test-key"
        encrypted_value = config.get_api_key_encrypted()
        assert encrypted_value != "sk-openai-test-key"
    
    def test_null_api_key_handling(self, db: Session):
        """测试NULL API密钥处理"""
        config = AIModelConfig(
            model_name="无密钥模型",
            provider="dify",
            api_key=None
        )
        
        db.add(config)
        db.commit()
        db.refresh(config)
        
        assert config.api_key is None
        assert config.get_api_key_encrypted() is None
    
    def test_dify_model_without_api_key(self, db: Session):
        """测试Dify模型不需要API密钥"""
        config = AIModelConfig(
            model_name="Dify模型",
            provider="dify",
            dify_app_id="test-app-123",
            agent_type=AgentType.BEAUTY_PLAN
        )
        
        db.add(config)
        db.commit()
        db.refresh(config)
        
        assert config.api_key is None
        assert config.provider == "dify"
        assert config.agent_type == AgentType.BEAUTY_PLAN


class TestEncryptionIntegration:
    """加密集成测试"""
    
    def test_mixed_encrypted_unencrypted_data(self, db: Session):
        """测试混合加密和未加密数据的场景"""
        # 创建两个连接，一个加密一个未加密
        connection1 = DifyConnection(
            name="加密连接",
            api_base_url="https://encrypted.example.com",
            api_key="sk-encrypted-key"
        )
        
        connection2 = DifyConnection(
            name="兼容连接",
            api_base_url="https://compat.example.com"
        )
        # 直接设置未加密数据（模拟旧数据）
        connection2.set_api_key_raw("sk-unencrypted-key")
        
        db.add_all([connection1, connection2])
        db.commit()
        
        # 查询并验证
        connections = db.query(DifyConnection).all()
        
        for conn in connections:
            if conn.name == "加密连接":
                assert conn.api_key == "sk-encrypted-key"
                # 验证确实是加密存储的
                encryption = get_encryption()
                assert encryption.is_encrypted(conn.get_api_key_encrypted())
            elif conn.name == "兼容连接":
                assert conn.api_key == "sk-unencrypted-key"
                # 验证是未加密的
                encryption = get_encryption()
                assert not encryption.is_encrypted(conn.get_api_key_encrypted())
    
    def test_encryption_with_database_operations(self, db: Session):
        """测试数据库操作中的加密行为"""
        # 批量创建连接
        connections = []
        for i in range(3):
            conn = DifyConnection(
                name=f"批量连接{i}",
                api_base_url=f"https://batch{i}.example.com",
                api_key=f"sk-batch-key-{i}"
            )
            connections.append(conn)
        
        db.add_all(connections)
        db.commit()
        
        # 查询并验证
        saved_connections = db.query(DifyConnection).filter(
            DifyConnection.name.like("批量连接%")
        ).all()
        
        assert len(saved_connections) == 3
        
        for i, conn in enumerate(saved_connections):
            expected_key = f"sk-batch-key-{i}"
            assert conn.api_key == expected_key
            
            # 验证加密存储
            encryption = get_encryption()
            encrypted_value = conn.get_api_key_encrypted()
            assert encryption.is_encrypted(encrypted_value)
            assert encryption.decrypt(encrypted_value) == expected_key
    
    def test_query_with_encrypted_fields(self, db: Session):
        """测试包含加密字段的查询"""
        connection = DifyConnection(
            name="查询测试连接",
            api_base_url="https://query.example.com",
            api_key="sk-query-test-key",
            sync_status=SyncStatus.SUCCESS
        )
        
        db.add(connection)
        db.commit()
        
        # 通过其他字段查询
        found_connection = db.query(DifyConnection).filter(
            DifyConnection.name == "查询测试连接"
        ).first()
        
        assert found_connection is not None
        assert found_connection.api_key == "sk-query-test-key"
        assert found_connection.sync_status == SyncStatus.SUCCESS


class TestEncryptionErrorHandling:
    """加密错误处理测试"""
    
    def test_corrupted_encrypted_data_handling(self, db: Session):
        """测试损坏的加密数据处理"""
        connection = DifyConnection(
            name="损坏数据测试",
            api_base_url="https://corrupted.example.com"
        )
        
        # 设置无效的加密数据
        connection.set_api_key_raw("corrupted_encrypted_data_not_base64")
        
        db.add(connection)
        db.commit()
        db.refresh(connection)
        
        # 应该回退到返回原文（向后兼容）
        assert connection.api_key == "corrupted_encrypted_data_not_base64"
    
    @patch('app.core.encryption.get_encryption')
    def test_encryption_service_failure(self, mock_get_encryption, db: Session):
        """测试加密服务失败的处理"""
        # 模拟加密服务失败
        mock_encryption = mock_get_encryption.return_value
        mock_encryption.encrypt.side_effect = Exception("加密服务不可用")
        
        connection = DifyConnection(
            name="加密失败测试",
            api_base_url="https://failure.example.com"
        )
        
        # 设置API密钥时应该处理异常
        with pytest.raises(Exception):
            connection.api_key = "sk-test-key"


class TestModelIntegrity:
    """模型完整性测试"""
    
    def test_model_constraints_with_encryption(self, db: Session):
        """测试模型约束与加密的兼容性"""
        # 测试唯一约束等是否与加密兼容
        connection1 = DifyConnection(
            name="约束测试1",
            api_base_url="https://constraint1.example.com",
            api_key="sk-constraint-key-1",
            is_default=True
        )
        
        connection2 = DifyConnection(
            name="约束测试2",
            api_base_url="https://constraint2.example.com",
            api_key="sk-constraint-key-2",
            is_default=False
        )
        
        db.add_all([connection1, connection2])
        db.commit()
        
        # 验证约束正常工作
        default_connections = db.query(DifyConnection).filter(
            DifyConnection.is_default == True
        ).all()
        
        assert len(default_connections) == 1
        assert default_connections[0].name == "约束测试1"
        assert default_connections[0].api_key == "sk-constraint-key-1" 