import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.channels.models.channel_config import ChannelConfig

logger = logging.getLogger(__name__)


class ChannelConfigService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_type(self, *, channel_type: str) -> Optional[ChannelConfig]:
        return (
            self.db.query(ChannelConfig)
            .filter(ChannelConfig.channel_type == channel_type)
            .order_by(ChannelConfig.created_at.desc())
            .first()
        )

    def upsert_config(
        self,
        *,
        channel_type: str,
        name: str,
        config: dict,
        is_active: bool = True,
    ) -> ChannelConfig:
        row = self.get_by_type(channel_type=channel_type)
        if row:
            row.name = name
            row.config = config
            row.is_active = is_active
        else:
            row = ChannelConfig(
                channel_type=channel_type,
                name=name,
                config=config,
                is_active=is_active,
            )
            self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
