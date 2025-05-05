from typing import Optional, Union, Dict, Any
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import UserCreate, UserUpdate
from app.db.models.user import User

async def get(db: Session, id: int) -> Optional[User]:
    """根据ID获取用户"""
    return db.query(User).filter(User.id == id).first()

async def get_by_email(db: Session, email: str) -> Optional[User]:
    """根据邮箱获取用户"""
    return db.query(User).filter(User.email == email).first()

async def create(db: Session, *, obj_in: UserCreate) -> User:
    """创建新用户"""
    db_obj = User(
        email=obj_in.email,
        username=obj_in.username,
        hashed_password=get_password_hash(obj_in.password),
        is_active=True,
    )
    db.add(db_obj)
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
    
    for field in update_data:
        if hasattr(db_obj, field):
            setattr(db_obj, field, update_data[field])
    
    db.add(db_obj)
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