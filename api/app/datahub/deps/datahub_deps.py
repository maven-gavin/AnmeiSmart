from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.datahub.services import DatahubMetadataService, DatahubService, DatahubWatchlistService, MarketDailyReadService


def get_datahub_service(db: Session = Depends(get_db)) -> DatahubService:
    return DatahubService(db)


def get_datahub_metadata_service(db: Session = Depends(get_db)) -> DatahubMetadataService:
    return DatahubMetadataService(db)


def get_datahub_watchlist_service(db: Session = Depends(get_db)) -> DatahubWatchlistService:
    return DatahubWatchlistService(db)


def get_market_daily_read_service(db: Session = Depends(get_db)) -> MarketDailyReadService:
    return MarketDailyReadService(db)
