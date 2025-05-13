from typing import Optional, Union, Dict, Any, List
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import UserCreate, UserUpdate
from app.db.models.user import User, Role

async def get(db: Session, id: int) -> Optional[User]:
    """根据ID获取用户"""
    return db.query(User).filter(User.id == id).first()

async def get_by_email(db: Session, email: str) -> Optional[User]:
    """根据邮箱获取用户"""
    return db.query(User).filter(User.email == email).first()

async def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    """根据名称获取角色"""
    return db.query(Role).filter(Role.name == name).first()

async def get_roles(db: Session) -> List[Role]:
    """获取所有角色"""
    return db.query(Role).all()

async def create_role(db: Session, *, name: str, description: Optional[str] = None) -> Role:
    """创建新角色"""
    db_obj = Role(name=name, description=description)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

async def get_or_create_role(db: Session, name: str) -> Role:
    """获取或创建角色"""
    role = await get_role_by_name(db, name=name)
    if not role:
        role = await create_role(db, name=name)
    return role

async def create(db: Session, *, obj_in: UserCreate) -> User:
    """创建新用户"""
    db_obj = User(
        email=obj_in.email,
        username=obj_in.username,
        hashed_password=get_password_hash(obj_in.password),
        phone=obj_in.phone,
        avatar=obj_in.avatar,
        is_active=True,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    # 添加角色
    if obj_in.roles:
        for role_name in obj_in.roles:
            role = await get_or_create_role(db, name=role_name)
            db_obj.roles.append(role)
        db.commit()
        db.refresh(db_obj)
    
    return db_obj

async def update(
    db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
) -> User:
    """更新用户信息"""
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.dict(exclude_unset=True)
    
    if update_data.get("password"):
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password
    
    # 处理角色更新
    roles_data = update_data.pop("roles", None)
    
    # 更新其他字段
    for field in update_data:
        if hasattr(db_obj, field):
            setattr(db_obj, field, update_data[field])
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    # 如果提供了角色信息，则更新角色
    if roles_data is not None:
        # 清除现有角色
        db_obj.roles = []
        # 添加新角色
        for role_name in roles_data:
            role = await get_or_create_role(db, name=role_name)
            db_obj.roles.append(role)
        db.commit()
        db.refresh(db_obj)
    
    return db_obj

async def authenticate(db: Session, *, email: str, password: str) -> Optional[User]:
    """验证用户"""
    user = await get_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_user_roles(db: Session, *, user_id: int) -> List[str]:
    """获取用户角色名列表"""
    user = await get(db, id=user_id)
    if not user:
        return []
    return [role.name for role in user.roles] 