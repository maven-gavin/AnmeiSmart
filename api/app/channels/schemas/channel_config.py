from typing import Any, Optional
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class ChannelConfigBase(BaseModel):
    channel_type: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    config: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class ChannelConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    config: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class ChannelConfigInfo(ChannelConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
