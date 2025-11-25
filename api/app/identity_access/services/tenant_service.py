from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.identity_access.models.user import Tenant, User
from app.identity_access.schemas.tenant_schemas import TenantCreate, TenantUpdate
from app.identity_access.enums import TenantStatus
from app.core.api import BusinessException, ErrorCode

class TenantService:
    def __init__(self, db: Session):
        self.db = db

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        
    def list_tenants(self, status: Optional[str] = None) -> List[Tenant]:
        query = self.db.query(Tenant)
        if status:
            # 将字符串状态转换为枚举值
            # 处理大小写不匹配：枚举值是小写，但允许传入大写或小写
            status_lower = status.lower()
            try:
                # 先尝试通过枚举值匹配（小写）
                tenant_status = TenantStatus(status_lower)
                query = query.filter(Tenant.status == tenant_status)
            except ValueError:
                # 如果通过值匹配失败，尝试通过枚举名匹配（大写）
                try:
                    tenant_status = TenantStatus[status.upper()]
                    query = query.filter(Tenant.status == tenant_status)
                except KeyError:
                    # 如果都不匹配，抛出业务异常
                    raise BusinessException(
                        f"无效的租户状态: {status}。有效值: {', '.join([e.value for e in TenantStatus])}",
                        code=ErrorCode.INVALID_PARAMETER
                    )
        return query.all()
        
    def create_tenant(self, tenant_in: TenantCreate) -> Tenant:
        if self.db.query(Tenant).filter(Tenant.name == tenant_in.name).first():
            raise BusinessException("租户名称已存在", code=ErrorCode.RESOURCE_ALREADY_EXISTS)
            
        tenant_data = tenant_in.model_dump()
        tenant = Tenant(**tenant_data)
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant
        
    def update_tenant(self, tenant_id: str, tenant_in: TenantUpdate) -> Tenant:
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            raise BusinessException("租户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
            
        update_data = tenant_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)
            
        self.db.commit()
        self.db.refresh(tenant)
        return tenant
        
    def delete_tenant(self, tenant_id: str) -> bool:
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            raise BusinessException("租户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
            
        self.db.delete(tenant)
        self.db.commit()
        return True
        
    def activate_tenant(self, tenant_id: str) -> bool:
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            raise BusinessException("租户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
            
        tenant.status = TenantStatus.ACTIVE
        self.db.commit()
        return True

    def deactivate_tenant(self, tenant_id: str) -> bool:
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            raise BusinessException("租户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
            
        tenant.status = TenantStatus.INACTIVE
        self.db.commit()
        return True

    def get_tenant_statistics(self, tenant_id: str) -> Dict[str, Any]:
        tenant = self.get_tenant(tenant_id)
        if not tenant:
             raise BusinessException("租户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
             
        user_count = self.db.query(User).filter(User.tenant_id == tenant_id).count()
        return {
            "tenant_id": tenant_id,
            "user_count": user_count,
            # 其他统计...
        }

