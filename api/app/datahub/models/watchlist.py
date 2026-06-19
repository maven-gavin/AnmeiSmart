from sqlalchemy import Column, Date, Index, Integer, String, UniqueConstraint

from app.common.models.base_model import BaseModel


class DatahubWatchlistItem(BaseModel):
    __tablename__ = "datahub_watchlist_items"
    __table_args__ = (
        UniqueConstraint("symbol", name="uq_datahub_watchlist_items_symbol"),
        Index("idx_datahub_watchlist_items_sort_order", "sort_order"),
        {"comment": "DataHub 自选股列表"},
    )

    symbol = Column(String(32), nullable=False, comment="证券代码")
    name = Column(String(100), nullable=True, comment="证券名称")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序")
    note = Column(String(255), nullable=True, comment="备注")
    backfill_start_date = Column(Date, nullable=True, comment="回填开始日期偏好")
    backfill_end_date = Column(Date, nullable=True, comment="回填结束日期偏好")
    window_days = Column(Integer, nullable=True, comment="增量窗口天数偏好")
