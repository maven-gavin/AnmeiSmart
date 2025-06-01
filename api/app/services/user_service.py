from datetime import datetime
from typing import Any, Dict, Optional, List, Union, Tuple

from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db.models.user import User, Role, Doctor, Consultant, Operator, Administrator
from app.db.models.customer import Customer
from app.db.uuid_utils import user_id, role_id
from app.core.password_utils import get_password_hash, verify_password
from app.schemas.user import UserCreate, UserUpdate, UserResponse, RoleResponse
from fastapi import status

async def get(db: Session, id: str) -> Optional[UserResponse]:
    """
    根据用户ID获取用户信息
    :param db: 数据库会话
    :param id: 用户ID
    :return: UserResponse 或 None
    """
    user = db.query(User).filter(User.id == id).first()
    return UserResponse.from_model(user) if user else None

async def get_by_email(db: Session, email: str) -> Optional[UserResponse]:
    """
    根据邮箱获取用户信息
    :param db: 数据库会话
    :param email: 邮箱
    :return: UserResponse 或 None
    """
    user = db.query(User).filter(User.email == email).first()
    return UserResponse.from_model(user) if user else None

async def get_by_username(db: Session, username: str) -> Optional[UserResponse]:
    """
    根据用户名获取用户信息
    :param db: 数据库会话
    :param username: 用户名
    :return: UserResponse 或 None
    """
    user = db.query(User).filter(User.username == username).first()
    return UserResponse.from_model(user) if user else None

async def get_role_by_name(db: Session, name: str) -> Optional[RoleResponse]:
    """
    根据角色名获取角色信息
    :param db: 数据库会话
    :param name: 角色名
    :return: RoleResponse 或 None
    """
    role = db.query(Role).filter(Role.name == name).first()
    return RoleResponse.from_orm(role) if role else None

async def get_role_by_id(db: Session, role_id: str) -> Optional[RoleResponse]:
    """
    根据角色ID获取角色信息
    :param db: 数据库会话
    :param role_id: 角色ID
    :return: RoleResponse 或 None
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    return RoleResponse.from_orm(role) if role else None

async def get_roles(db: Session) -> List[RoleResponse]:
    """
    获取所有角色列表
    :param db: 数据库会话
    :return: 角色响应列表
    """
    roles = db.query(Role).all()
    return [RoleResponse.from_orm(role) for role in roles]

async def create_role(db: Session, *, name: str, description: Optional[str] = None) -> RoleResponse:
    """
    创建新角色
    :param db: 数据库会话
    :param name: 角色名
    :param description: 角色描述
    :return: RoleResponse
    """
    db_obj = Role(name=name, description=description)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return RoleResponse.from_orm(db_obj)

async def get_or_create_role(db: Session, name: str) -> RoleResponse:
    """
    获取或创建角色
    :param db: 数据库会话
    :param name: 角色名
    :return: RoleResponse
    """
    role = db.query(Role).filter(Role.name == name).first()
    if not role:
        role = Role(name=name)
        db.add(role)
        db.commit()
        db.refresh(role)
    return RoleResponse.from_orm(role)

async def create(db: Session, obj_in: UserCreate) -> UserResponse:
    """
    创建新用户
    :param db: 数据库会话
    :param obj_in: 用户创建数据
    :return: UserResponse
    """
    existing_email = db.query(User).filter(User.email == obj_in.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email已被使用")
    existing_username = db.query(User).filter(User.username == obj_in.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="用户名已被使用")
    db_obj = User(
        id=obj_in.id if hasattr(obj_in, 'id') else user_id(),
        email=obj_in.email,
        username=obj_in.username,
        hashed_password=get_password_hash(obj_in.password),
        phone=obj_in.phone,
        avatar=obj_in.avatar,
        is_active=obj_in.is_active
    )
    roles = []
    for role_name in obj_in.roles:
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            # Do not create invalid roles; instead, raise an exception.
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"无效的角色: {role_name}")
        roles.append(role)
    db_obj.roles = roles
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    # 扩展信息略（如需可补充）
    return UserResponse.from_model(db_obj)

async def update(db: Session, user_id: str, obj_in: Union[UserUpdate, Dict[str, Any]]) -> UserResponse:
    """
    更新用户信息
    :param db: 数据库会话
    :param user_id: 要更新的用户ID
    :param obj_in: 用户更新数据
    :return: UserResponse
    """
    db_obj = db.query(User).filter(User.id == user_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        update_data["hashed_password"] = hashed_password
        del update_data["password"]
    if "roles" in update_data and update_data["roles"]:
        roles = []
        for role_name in update_data["roles"]:
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                # 根据实际需求，这里可以选择创建新角色或抛出错误
                # 假设如果角色不存在则创建
                role = Role(id=role_id(), name=role_name)
                db.add(role)
            roles.append(role)
        db_obj.roles = roles
        del update_data["roles"]
    
    # 更新其他字段
    for key, value in update_data.items():
        if hasattr(db_obj, key) and key not in ["customer_info", "doctor_info", "consultant_info", "operator_info", "administrator_info"] and value is not None : # 确保字段存在且不更新关联对象本身
            setattr(db_obj, key, value)
            
    db.add(db_obj) # 确保对象被添加到会话中以进行更新
    db.commit()
    db.refresh(db_obj)
    return UserResponse.from_model(db_obj)

async def remove(db: Session, *, id: str) -> Optional[UserResponse]:
    """
    删除用户
    :param db: 数据库会话
    :param id: 用户ID
    :return: 被删除的UserResponse 或 None
    """
    user = db.query(User).filter(User.id == id).first()
    if user:
        db.delete(user)
        db.commit()
        return UserResponse.from_model(user)
    return None

async def authenticate(db: Session, username_or_email: str, password: str) -> Optional[UserResponse]:
    """
    用户身份认证
    :param db: 数据库会话
    :param username_or_email: 用户名或邮箱
    :param password: 密码
    :return: UserResponse 或 None
    """
    is_email = "@" in username_or_email
    user = db.query(User).filter(User.email == username_or_email if is_email else User.username == username_or_email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return UserResponse.from_model(user)

async def get_user_roles(db: Session, *, user_id: str) -> List[str]:
    """
    获取用户的所有角色名
    :param db: 数据库会话
    :param user_id: 用户ID
    :return: 角色名列表
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []
    return [role.name for role in user.roles]

async def add_role_to_user(db: Session, *, user_id: str, role_name: str) -> Optional[UserResponse]:
    """
    为用户添加角色
    :param db: 数据库会话
    :param user_id: 用户ID
    :param role_name: 角色名
    :return: UserResponse 或 None
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    if role_name in [role.name for role in user.roles]:
        return UserResponse.from_model(user)
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        return None
    user.roles.append(role)
    db.commit()
    db.refresh(user)
    return UserResponse.from_model(user)

async def remove_role_from_user(db: Session, *, user_id: str, role_name: str) -> Optional[UserResponse]:
    """
    从用户移除角色
    :param db: 数据库会话
    :param user_id: 用户ID
    :param role_name: 角色名
    :return: UserResponse 或 None
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role or role not in user.roles:
        return UserResponse.from_model(user)
    user.roles.remove(role)
    db.commit()
    db.refresh(user)
    return UserResponse.from_model(user)

async def get_multi(db: Session, skip: int = 0, limit: int = 100) -> List[UserResponse]:
    """
    获取用户列表
    :param db: 数据库会话
    :param skip: 跳过的记录数
    :param limit: 返回的最大记录数
    :return: UserResponse列表
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserResponse.from_model(user) for user in users] 