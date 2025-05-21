from typing import Optional, Union, Dict, Any, List
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserCreate, UserUpdate
from app.db.models.user import User, Role, Customer, Doctor, Consultant, Operator, Administrator

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

async def create(db: Session, *, obj_in: UserCreate) -> User:
    """创建新用户"""
    # 创建基础用户对象
    db_obj = User(
        email=obj_in.email,
        username=obj_in.username,
        hashed_password=get_password_hash(obj_in.password),
        phone=obj_in.phone,
        avatar=obj_in.avatar,
        is_active=obj_in.is_active,
    )
    
    # 处理角色
    if obj_in.roles:
        roles = []
        for role_name in obj_in.roles:
            role = db.query(Role).filter(Role.name == role_name).first()
            if role:
                roles.append(role)
        db_obj.roles = roles
    
    # 提交基础用户以获取用户ID
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    # 处理顾客信息
    if "customer" in obj_in.roles and obj_in.customer_info:
        customer = Customer(
            user_id=db_obj.id,
            medical_history=obj_in.customer_info.medical_history,
            allergies=obj_in.customer_info.allergies,
            preferences=obj_in.customer_info.preferences
        )
        db.add(customer)
    
    # 处理医生信息
    if "doctor" in obj_in.roles and obj_in.doctor_info:
        doctor = Doctor(
            user_id=db_obj.id,
            specialization=obj_in.doctor_info.specialization,
            certification=obj_in.doctor_info.certification,
            license_number=obj_in.doctor_info.license_number
        )
        db.add(doctor)
    
    # 处理顾问信息
    if "consultant" in obj_in.roles and obj_in.consultant_info:
        consultant = Consultant(
            user_id=db_obj.id,
            expertise=obj_in.consultant_info.expertise,
            performance_metrics=obj_in.consultant_info.performance_metrics
        )
        db.add(consultant)
    
    # 处理运营人员信息
    if "operator" in obj_in.roles and obj_in.operator_info:
        operator = Operator(
            user_id=db_obj.id,
            department=obj_in.operator_info.department,
            responsibilities=obj_in.operator_info.responsibilities
        )
        db.add(operator)
    
    # 处理管理员信息
    if "admin" in obj_in.roles and obj_in.administrator_info:
        administrator = Administrator(
            user_id=db_obj.id,
            admin_level=obj_in.administrator_info.admin_level,
            access_permissions=obj_in.administrator_info.access_permissions
        )
        db.add(administrator)
    
    # 提交所有更改
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
    
    # 处理密码
    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        update_data["hashed_password"] = hashed_password
        del update_data["password"]
    
    # 处理基础用户信息更新
    for field in ["email", "username", "phone", "avatar", "is_active"]:
        if field in update_data:
            setattr(db_obj, field, update_data[field])
    
    # 处理角色更新
    if "roles" in update_data and update_data["roles"]:
        roles = []
        for role_name in update_data["roles"]:
            role = db.query(Role).filter(Role.name == role_name).first()
            if role:
                roles.append(role)
        db_obj.roles = roles
    
    # 提交基础用户更新
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    # 处理顾客信息更新
    if "customer_info" in update_data and update_data["customer_info"]:
        # 如果用户有顾客角色，更新顾客信息
        if "customer" in [role.name for role in db_obj.roles]:
            customer_info = update_data["customer_info"]
            
            # 如果已存在顾客记录，更新它
            if db_obj.customer:
                for field in ["medical_history", "allergies", "preferences"]:
                    if field in customer_info:
                        setattr(db_obj.customer, field, customer_info[field])
                db.add(db_obj.customer)
            # 否则创建新记录
            else:
                customer = Customer(
                    user_id=db_obj.id,
                    **customer_info
                )
                db.add(customer)
    
    # 处理医生信息更新
    if "doctor_info" in update_data and update_data["doctor_info"]:
        # 如果用户有医生角色，更新医生信息
        if "doctor" in [role.name for role in db_obj.roles]:
            doctor_info = update_data["doctor_info"]
            
            # 如果已存在医生记录，更新它
            if db_obj.doctor:
                for field in ["specialization", "certification", "license_number"]:
                    if field in doctor_info:
                        setattr(db_obj.doctor, field, doctor_info[field])
                db.add(db_obj.doctor)
            # 否则创建新记录
            else:
                doctor = Doctor(
                    user_id=db_obj.id,
                    **doctor_info
                )
                db.add(doctor)
    
    # 处理顾问信息更新
    if "consultant_info" in update_data and update_data["consultant_info"]:
        # 如果用户有顾问角色，更新顾问信息
        if "consultant" in [role.name for role in db_obj.roles]:
            consultant_info = update_data["consultant_info"]
            
            # 如果已存在顾问记录，更新它
            if db_obj.consultant:
                for field in ["expertise", "performance_metrics"]:
                    if field in consultant_info:
                        setattr(db_obj.consultant, field, consultant_info[field])
                db.add(db_obj.consultant)
            # 否则创建新记录
            else:
                consultant = Consultant(
                    user_id=db_obj.id,
                    **consultant_info
                )
                db.add(consultant)
    
    # 处理运营人员信息更新
    if "operator_info" in update_data and update_data["operator_info"]:
        # 如果用户有运营人员角色，更新运营人员信息
        if "operator" in [role.name for role in db_obj.roles]:
            operator_info = update_data["operator_info"]
            
            # 如果已存在运营人员记录，更新它
            if db_obj.operator:
                for field in ["department", "responsibilities"]:
                    if field in operator_info:
                        setattr(db_obj.operator, field, operator_info[field])
                db.add(db_obj.operator)
            # 否则创建新记录
            else:
                operator = Operator(
                    user_id=db_obj.id,
                    **operator_info
                )
                db.add(operator)
    
    # 处理管理员信息更新
    if "administrator_info" in update_data and update_data["administrator_info"]:
        # 如果用户有管理员角色，更新管理员信息
        if "admin" in [role.name for role in db_obj.roles]:
            administrator_info = update_data["administrator_info"]
            
            # 如果已存在管理员记录，更新它
            if db_obj.administrator:
                for field in ["admin_level", "access_permissions"]:
                    if field in administrator_info:
                        setattr(db_obj.administrator, field, administrator_info[field])
                db.add(db_obj.administrator)
            # 否则创建新记录
            else:
                administrator = Administrator(
                    user_id=db_obj.id,
                    **administrator_info
                )
                db.add(administrator)
    
    # 提交所有更改
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

async def authenticate(db: Session, *, email: str, password: str) -> Optional[User]:
    """验证用户"""
    user = await get_by_email(db, email=email)
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