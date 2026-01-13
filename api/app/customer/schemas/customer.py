from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

# 客户基础信息
class CustomerBase(BaseModel):
    """客户信息基础模型"""
    # 移除旧字段
    pass

class CustomerCreate(CustomerBase):
    """创建客户信息的请求模型"""
    user_id: str

class CustomerUpdate(CustomerBase):
    """更新客户信息的请求模型"""
    pass

# --- 画像/洞察 Schema ---

class CustomerInsightBase(BaseModel):
    """客户洞察基础模型"""
    category: str = Field(..., description="维度分类: need, budget, authority, timeline, preference, risk, trait, background, other")
    content: str
    confidence: Optional[float] = 1.0

class CustomerInsightCreate(CustomerInsightBase):
    """创建客户洞察"""
    # 由后端根据 customer_id 路径参数自动解析/校验；允许前端不传
    profile_id: Optional[str] = None
    source: Optional[str] = "human"
    created_by_name: Optional[str] = None

class CustomerInsightInfo(CustomerInsightBase):
    """客户洞察完整信息"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    source: Optional[str] = None
    created_by_name: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None

# --- 客户档案 Schema ---

class CustomerProfileBase(BaseModel):
    """客户档案基础模型"""
    life_cycle_stage: Optional[str] = "lead"
    industry: Optional[str] = None
    company_scale: Optional[str] = None
    ai_summary: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

class CustomerProfileCreate(CustomerProfileBase):
    """创建客户档案的请求模型"""
    pass

class CustomerProfileUpdate(CustomerProfileBase):
    """更新客户档案的请求模型"""
    pass

class CustomerProfileInfo(CustomerProfileBase):
    """客户档案完整模型"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    # 包含洞察流 (通常只返回Active的)
    active_insights: Optional[List[CustomerInsightInfo]] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# --- 客户完整信息 ---

class CustomerInfo(CustomerBase):
    """客户完整信息模型，包含基本用户信息和档案"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    username: str
    email: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    status: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    
    profile: Optional[CustomerProfileInfo] = None
