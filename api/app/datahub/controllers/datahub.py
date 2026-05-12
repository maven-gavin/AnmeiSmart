from fastapi import APIRouter, Depends, Query, status

from app.core.api import ApiResponse
from app.identity_access.deps import get_current_admin
from app.identity_access.models.user import User
from app.datahub.deps import get_datahub_metadata_service, get_datahub_service
from app.datahub.schemas.datahub import (
    DatahubDatasetInfo,
    DatahubJobTaskInfo,
    DatahubJobRunInfo,
    DatahubObjectIndexInfo,
    DatahubQualityReportInfo,
    DatahubWorkerHeartbeatInfo,
    TriggerBackfillRequest,
    TriggerDailyIncrementalRequest,
)
from app.datahub.services import DatahubMetadataService, DatahubService

router = APIRouter()


@router.get("/health", response_model=ApiResponse[dict[str, str]])
def health_check() -> ApiResponse[dict[str, str]]:
    return ApiResponse.success(data={"status": "ok"}, message="datahub healthy")


@router.post("/datasets/seed", response_model=ApiResponse[int], status_code=status.HTTP_201_CREATED)
def seed_dataset_catalog(
    service: DatahubMetadataService = Depends(get_datahub_metadata_service),
    _: User = Depends(get_current_admin),
) -> ApiResponse[int]:
    created = service.seed_dataset_catalog()
    return ApiResponse.success(data=created, message="seed dataset catalog done")


@router.get("/datasets", response_model=ApiResponse[list[DatahubDatasetInfo]])
def list_datasets(
    service: DatahubService = Depends(get_datahub_service),
    _: User = Depends(get_current_admin),
) -> ApiResponse[list[DatahubDatasetInfo]]:
    return ApiResponse.success(data=service.list_datasets(), message="list datasets success")


@router.get("/jobs/runs", response_model=ApiResponse[list[DatahubJobRunInfo]])
def list_job_runs(
    limit: int = Query(20, ge=1, le=100, description="返回条数"),
    service: DatahubService = Depends(get_datahub_service),
    _: User = Depends(get_current_admin),
) -> ApiResponse[list[DatahubJobRunInfo]]:
    return ApiResponse.success(data=service.list_job_runs(limit=limit), message="list job runs success")


@router.post("/jobs/backfill", response_model=ApiResponse[DatahubJobRunInfo], status_code=status.HTTP_201_CREATED)
def trigger_backfill(
    payload: TriggerBackfillRequest,
    service: DatahubService = Depends(get_datahub_service),
    _: User = Depends(get_current_admin),
) -> ApiResponse[DatahubJobRunInfo]:
    run = service.create_backfill_job(payload)
    return ApiResponse.success(data=run, message="backfill job created")


@router.post("/jobs/daily-incremental", response_model=ApiResponse[DatahubJobRunInfo], status_code=status.HTTP_201_CREATED)
def trigger_daily_incremental(
    payload: TriggerDailyIncrementalRequest,
    service: DatahubService = Depends(get_datahub_service),
    _: User = Depends(get_current_admin),
) -> ApiResponse[DatahubJobRunInfo]:
    run = service.create_daily_incremental_job(payload)
    return ApiResponse.success(data=run, message="daily incremental job created")


@router.post("/jobs/backfill/run", response_model=ApiResponse[DatahubJobRunInfo], status_code=status.HTTP_201_CREATED)
def run_backfill_now(
    payload: TriggerBackfillRequest,
    service: DatahubService = Depends(get_datahub_service),
    _: User = Depends(get_current_admin),
) -> ApiResponse[DatahubJobRunInfo]:
    run = service.create_backfill_job(payload)
    return ApiResponse.success(data=run, message="backfill job queued")


@router.post("/jobs/daily-incremental/run", response_model=ApiResponse[DatahubJobRunInfo], status_code=status.HTTP_201_CREATED)
def run_daily_incremental_now(
    payload: TriggerDailyIncrementalRequest,
    service: DatahubService = Depends(get_datahub_service),
    _: User = Depends(get_current_admin),
) -> ApiResponse[DatahubJobRunInfo]:
    run = service.create_daily_incremental_job(payload)
    return ApiResponse.success(data=run, message="daily incremental job queued")


@router.get("/jobs/runs/{run_id}", response_model=ApiResponse[DatahubJobRunInfo | None])
def get_job_run(
    run_id: str,
    service: DatahubService = Depends(get_datahub_service),
    _: User = Depends(get_current_admin),
) -> ApiResponse[DatahubJobRunInfo | None]:
    return ApiResponse.success(data=service.get_job_run(run_id), message="get job run success")


@router.get("/jobs/runs/{run_id}/tasks", response_model=ApiResponse[list[DatahubJobTaskInfo]])
def list_job_tasks(
    run_id: str,
    service: DatahubService = Depends(get_datahub_service),
    _: User = Depends(get_current_admin),
) -> ApiResponse[list[DatahubJobTaskInfo]]:
    return ApiResponse.success(data=service.list_job_tasks(run_id), message="list job tasks success")


@router.get("/quality/reports", response_model=ApiResponse[list[DatahubQualityReportInfo]])
def list_quality_reports(
    dataset: str | None = Query(None),
    symbol: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    service: DatahubService = Depends(get_datahub_service),
    _: User = Depends(get_current_admin),
) -> ApiResponse[list[DatahubQualityReportInfo]]:
    data = service.list_quality_reports(dataset=dataset, symbol=symbol, limit=limit)
    return ApiResponse.success(data=data, message="list quality reports success")


@router.get("/objects/indexes", response_model=ApiResponse[list[DatahubObjectIndexInfo]])
def list_object_indexes(
    dataset: str | None = Query(None),
    symbol: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    service: DatahubService = Depends(get_datahub_service),
    _: User = Depends(get_current_admin),
) -> ApiResponse[list[DatahubObjectIndexInfo]]:
    data = service.list_object_indexes(dataset=dataset, symbol=symbol, limit=limit)
    return ApiResponse.success(data=data, message="list object indexes success")


@router.get("/worker/heartbeat", response_model=ApiResponse[DatahubWorkerHeartbeatInfo | None])
def get_worker_heartbeat(
    worker_name: str = Query("datahub-default-worker"),
    offline_threshold_seconds: int = Query(30, ge=5, le=300),
    service: DatahubService = Depends(get_datahub_service),
    _: User = Depends(get_current_admin),
) -> ApiResponse[DatahubWorkerHeartbeatInfo | None]:
    data = service.get_worker_heartbeat(
        worker_name=worker_name,
        offline_threshold_seconds=offline_threshold_seconds,
    )
    return ApiResponse.success(data=data, message="get worker heartbeat success")
