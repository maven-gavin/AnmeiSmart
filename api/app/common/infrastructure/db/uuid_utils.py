import uuid
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID


def generate_uuid() -> str:
    """生成UUID字符串"""
    return str(uuid.uuid4())


def prefixed_uuid(prefix: str) -> str:
    """生成带前缀的UUID字符串，但长度不超过36个字符
    
    Args:
        prefix: 前缀字符串，建议不超过4个字符
        
    Returns:
        带前缀的UUID，例如: user_550e8400
    """
    # 生成一个完整的UUID
    full_uuid = uuid.uuid4().hex
    
    # 截取部分UUID，确保总长度不超过36
    max_uuid_chars = 36 - len(prefix) - 1  # -1 是下划线占用的长度
    uuid_part = full_uuid[:max_uuid_chars]
    
    return f"{prefix}_{uuid_part}"


# 用户ID前缀生成函数
def user_id() -> str:
    """生成用户ID"""
    return prefixed_uuid("usr")


# 角色ID前缀生成函数
def role_id() -> str:
    """生成角色ID"""
    return prefixed_uuid("role")


# 会话ID前缀生成函数
def conversation_id() -> str:
    """生成会话ID"""
    return prefixed_uuid("conv")


# 消息ID前缀生成函数
def message_id() -> str:
    """生成消息ID"""
    return prefixed_uuid("msg")


# 客户ID前缀生成函数
def customer_id() -> str:
    """生成客户ID"""
    return prefixed_uuid("cust")


# 客户档案ID前缀生成函数
def profile_id() -> str:
    """生成客户档案ID"""
    return prefixed_uuid("prof")


# 系统设置ID前缀生成函数
def system_id() -> str:
    """生成系统设置ID"""
    return prefixed_uuid("sys")


# AI模型配置ID前缀生成函数
def model_id() -> str:
    """生成AI模型配置ID"""
    return prefixed_uuid("mdl")


# Agent配置ID前缀生成函数
def generate_agent_id() -> str:
    """生成Agent配置ID"""
    return prefixed_uuid("age")


# 数字人ID前缀生成函数
def digital_human_id() -> str:
    """生成数字人ID"""
    return prefixed_uuid("dh")


# 咨询记录ID前缀生成函数
def consultation_id() -> str:
    """生成咨询记录ID"""
    return prefixed_uuid("cons")


# 任务ID前缀生成函数
def task_id() -> str:
    """生成任务ID"""
    return prefixed_uuid("task")


# 通讯录相关ID前缀生成函数
def friendship_id() -> str:
    """生成好友关系ID"""
    return prefixed_uuid("frd")


def tag_id() -> str:
    """生成标签ID"""
    return prefixed_uuid("tag")


def group_id() -> str:
    """生成分组ID"""
    return prefixed_uuid("grp")


def relation_id() -> str:
    """生成关联关系ID"""
    return prefixed_uuid("rel")


def record_id() -> str:
    """生成记录ID"""
    return prefixed_uuid("rec")


def setting_id() -> str:
    """生成设置ID"""
    return prefixed_uuid("set")


# 创建SQLAlchemy的UUID类型，在不同数据库中使用
class UUID(TypeDecorator):
    """Platform-independent UUID type.
    
    Uses PostgreSQL's UUID type when available, otherwise
    uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if not isinstance(value, uuid.UUID):
                try:
                    # 如果是带前缀的UUID，只取UUID部分
                    if '_' in value:
                        _, uuid_part = value.split('_', 1)
                        return str(uuid.UUID(uuid_part))
                    return str(uuid.UUID(value))
                except (AttributeError, ValueError):
                    return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value 