from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class DatahubDatasetInfo(BaseModel):
    id: str
    dataset_key: str
    layer: str
    schema_version: str
    description: Optional[str] = None
    is_active: str
    updated_at: datetime


class DatahubJobRunInfo(BaseModel):
    id: str
    job_type: str
    dataset: Optional[str] = None
    status: str
    trigger_source: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    task_total: int
    task_success: int
    task_failed: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DatahubJobTaskInfo(BaseModel):
    id: str
    job_run_id: str
    dataset: str
    symbol: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str
    attempts: int
    last_error: Optional[str] = None
    locked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DatahubQualityReportInfo(BaseModel):
    id: str
    dataset: str
    symbol: Optional[str] = None
    biz_date: Optional[date] = None
    quality_score: float
    severity: str
    issues: Optional[list[dict]] = None
    object_key: Optional[str] = None
    checked_at: datetime
    created_at: datetime


class DatahubObjectIndexInfo(BaseModel):
    id: str
    bucket: str
    object_key: str
    dataset: str
    layer: str
    provider: Optional[str] = None
    symbol: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    row_count: int
    schema_version: str
    content_hash: Optional[str] = None
    quality_score: Optional[float] = None
    created_at: datetime


class DatahubWorkerHeartbeatInfo(BaseModel):
    worker_name: str
    status: str
    last_heartbeat_at: datetime
    last_run_id: Optional[str] = None
    processed_count: int
    last_error: Optional[str] = None
    is_online: bool
    offline_threshold_seconds: int


class TriggerBackfillRequest(BaseModel):
    dataset: str = Field(..., description="数据集")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    symbol: Optional[str] = Field(None, description="证券代码，可选")


class TriggerDailyIncrementalRequest(BaseModel):
    dataset: str = Field("market_daily", description="数据集")
    symbol: Optional[str] = Field(None, description="证券代码，可选")
    window_days: int = Field(7, ge=1, le=30, description="回溯窗口天数")
