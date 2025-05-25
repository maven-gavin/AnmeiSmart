from datetime import datetime
from typing import Any, Dict, Optional, List, Union, Tuple

from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db.models.user import User, Role, Doctor, Consultant, Operator, Administrator
from app.db.models.customer import Customer
from app.db.uuid_utils import user_id, role_id
from app.core.password_utils import get_password_hash, verify_password
from app.schemas.user import UserCreate, UserUpdate

async def get(db: Session, id: str) -> Optional[User]:
    """根据ID获取用户"""
    return db.query(User).filter(User.id == id).first() 

async def get_by_email(db: Session, email: str) -> Optional[User]:
    """根据邮箱获取用户"""
    return db.query(User).filter(User.email == email).first()

async def get_by_username(db: Session, username: str) -> Optional[User]:
    """通过用户名获取用户"""
    return db.query(User).filter(User.username == username).first()

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

async def create(db: Session, obj_in: UserCreate) -> User:
    """创建新用户"""
    # 检查是否已存在相同email或username的用户
    existing_email = await get_by_email(db, email=obj_in.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email已被使用")
    
    existing_username = await get_by_username(db, username=obj_in.username)
    if existing_username:
        raise HTTPException(status_code=400, detail="用户名已被使用")
    
    # 创建用户对象
    db_obj = User(
        id=obj_in.id if hasattr(obj_in, 'id') else user_id(),
        email=obj_in.email,
        username=obj_in.username,
        hashed_password=get_password_hash(obj_in.password),
        phone=obj_in.phone,
        avatar=obj_in.avatar,
        is_active=obj_in.is_active
    )
    
    # 添加角色
    roles = []
    for role_name in obj_in.roles:
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(id=role_id(), name=role_name)
            db.add(role)
        roles.append(role)
    
    db_obj.roles = roles
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    # 添加扩展信息
    # 添加客户信息
    if "customer" in obj_in.roles and obj_in.customer_info:
        customer = Customer(
            user_id=db_obj.id,
            medical_history=obj_in.customer_info.medical_history,
            allergies=obj_in.customer_info.allergies,
            preferences=obj_in.customer_info.preferences
        )
        db.add(customer)
    
    # 添加医生信息
    if "doctor" in obj_in.roles and obj_in.doctor_info:
        doctor = Doctor(
            user_id=db_obj.id,
            specialization=obj_in.doctor_info.specialization,
            certification=obj_in.doctor_info.certification,
            license_number=obj_in.doctor_info.license_number
        )
        db.add(doctor)
    
    # 添加顾问信息
    if "consultant" in obj_in.roles and obj_in.consultant_info:
        consultant = Consultant(
            user_id=db_obj.id,
            expertise=obj_in.consultant_info.expertise,
            performance_metrics=obj_in.consultant_info.performance_metrics
        )
        db.add(consultant)
    
    # 添加运营人员信息
    if "operator" in obj_in.roles and obj_in.operator_info:
        operator = Operator(
            user_id=db_obj.id,
            department=obj_in.operator_info.department,
            responsibilities=obj_in.operator_info.responsibilities
        )
        db.add(operator)
    
    # 添加管理员信息
    if "admin" in obj_in.roles and obj_in.administrator_info:
        administrator = Administrator(
            user_id=db_obj.id,
            admin_level=obj_in.administrator_info.admin_level,
            access_permissions=obj_in.administrator_info.access_permissions
        )
        db.add(administrator)
    
    db.commit()
    db.refresh(db_obj)
    
    return db_obj

async def update(
    db: Session, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
) -> User:
    """更新用户信息"""
    update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
    
    # 如果包含密码，需要哈希处理
    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        update_data["hashed_password"] = hashed_password
        del update_data["password"]
    
    # 处理角色 - 如果提供了角色信息
    if "roles" in update_data and update_data["roles"]:
        roles = []
        for role_name in update_data["roles"]:
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = Role(id=role_id(), name=role_name)
                db.add(role)
            roles.append(role)
        db_obj.roles = roles
        del update_data["roles"]
    
    # 更新基本用户字段
    for key, value in update_data.items():
        if key not in ["customer_info", "doctor_info", "consultant_info", 
                      "operator_info", "administrator_info"] and value is not None:
            setattr(db_obj, key, value)
    
    # 处理扩展信息
    # 更新客户信息
    if "customer_info" in update_data and update_data["customer_info"]:
        customer_info = update_data["customer_info"]
        
        # 检查用户是否有客户角色
        if "customer" in [role.name for role in db_obj.roles]:
            # 获取用户的客户信息
            customer = db.query(Customer).filter(Customer.user_id == db_obj.id).first()
            
            if customer:
                # 更新现有客户信息
                fields = ["medical_history", "allergies", "preferences"]
                for field in fields:
                    if field in customer_info:
                        setattr(customer, field, customer_info[field])
                db.add(customer)
            else:
                # 创建新的客户信息
                customer = Customer(
                    user_id=db_obj.id,
                    **customer_info
                )
                db.add(customer)
    
    # 更新医生信息
    if "doctor_info" in update_data and update_data["doctor_info"]:
        doctor_info = update_data["doctor_info"]
        
        if "doctor" in [role.name for role in db_obj.roles]:
            if db_obj.doctor:
                fields = ["specialization", "certification", "license_number"]
                for field in fields:
                    if field in doctor_info:
                        setattr(db_obj.doctor, field, doctor_info[field])
                db.add(db_obj.doctor)
            else:
                doctor = Doctor(
                    user_id=db_obj.id,
                    **doctor_info
                )
                db.add(doctor)
    
    # 更新顾问信息
    if "consultant_info" in update_data and update_data["consultant_info"]:
        consultant_info = update_data["consultant_info"]
        
        if "consultant" in [role.name for role in db_obj.roles]:
            if db_obj.consultant:
                fields = ["expertise", "performance_metrics"]
                for field in fields:
                    if field in consultant_info:
                        setattr(db_obj.consultant, field, consultant_info[field])
                db.add(db_obj.consultant)
            else:
                consultant = Consultant(
                    user_id=db_obj.id,
                    **consultant_info
                )
                db.add(consultant)
    
    # 更新运营信息
    if "operator_info" in update_data and update_data["operator_info"]:
        operator_info = update_data["operator_info"]
        
        if "operator" in [role.name for role in db_obj.roles]:
            if db_obj.operator:
                fields = ["department", "responsibilities"]
                for field in fields:
                    if field in operator_info:
                        setattr(db_obj.operator, field, operator_info[field])
                db.add(db_obj.operator)
            else:
                operator = Operator(
                    user_id=db_obj.id,
                    **operator_info
                )
                db.add(operator)
    
    # 更新管理员信息
    if "administrator_info" in update_data and update_data["administrator_info"]:
        administrator_info = update_data["administrator_info"]
        
        if "admin" in [role.name for role in db_obj.roles]:
            if db_obj.administrator:
                fields = ["admin_level", "access_permissions"]
                for field in fields:
                    if field in administrator_info:
                        setattr(db_obj.administrator, field, administrator_info[field])
                db.add(db_obj.administrator)
            else:
                administrator = Administrator(
                    user_id=db_obj.id,
                    **administrator_info
                )
                db.add(administrator)
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

async def remove(db: Session, *, id: str) -> Optional[User]:
    """删除用户"""
    user = db.query(User).filter(User.id == id).first()
    if user:
        db.delete(user)
        db.commit()
    return user

async def authenticate(db: Session, username_or_email: str, password: str) -> Optional[User]:
    """验证用户身份"""
    # 检查输入是邮箱还是用户名
    is_email = "@" in username_or_email
    
    if is_email:
        user = await get_by_email(db, email=username_or_email)
    else:
        user = await get_by_username(db, username=username_or_email)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user

async def get_user_roles(db: Session, *, user_id: str) -> List[str]:
    """获取用户角色名列表"""
    user = await get(db, id=user_id)
    if not user:
        return []
    return [role.name for role in user.roles]

async def add_role_to_user(db: Session, *, user_id: str, role_name: str) -> Optional[User]:
    """为用户添加角色"""
    user = await get(db, id=user_id)
    if not user:
        return None
    
    # 检查用户是否已有该角色
    if role_name in [role.name for role in user.roles]:
        return user
    
    # 获取角色对象
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        return None
    
    # 添加角色给用户
    user.roles.append(role)
    db.commit()
    db.refresh(user)
    
    # 如果是添加新角色，需要同时创建扩展表记录
    if role_name == "customer" and not user.customer:
        customer = Customer(user_id=user.id)
        db.add(customer)
    elif role_name == "doctor" and not user.doctor:
        doctor = Doctor(user_id=user.id)
        db.add(doctor)
    elif role_name == "consultant" and not user.consultant:
        consultant = Consultant(user_id=user.id)
        db.add(consultant)
    elif role_name == "operator" and not user.operator:
        operator = Operator(user_id=user.id)
        db.add(operator)
    elif role_name == "admin" and not user.administrator:
        administrator = Administrator(user_id=user.id)
        db.add(administrator)
    
    db.commit()
    db.refresh(user)
    return user

async def remove_role_from_user(db: Session, *, user_id: str, role_name: str) -> Optional[User]:
    """从用户中移除角色"""
    user = await get(db, id=user_id)
    if not user:
        return None
    
    # 获取角色对象
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        return None
    
    # 检查用户是否有该角色
    if role not in user.roles:
        return user
    
    # 移除用户角色
    user.roles.remove(role)
    
    # 如果移除角色，同时删除对应的扩展表记录
    if role_name == "customer" and user.customer:
        db.delete(user.customer)
    elif role_name == "doctor" and user.doctor:
        db.delete(user.doctor)
    elif role_name == "consultant" and user.consultant:
        db.delete(user.consultant)
    elif role_name == "operator" and user.operator:
        db.delete(user.operator)
    elif role_name == "admin" and user.administrator:
        db.delete(user.administrator)
    
    db.commit()
    db.refresh(user)
    return user 