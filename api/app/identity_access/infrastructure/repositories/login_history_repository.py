"""
登录历史仓储实现

实现登录历史数据访问的具体逻辑。
"""

from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from app.identity_access.infrastructure.db.profile import LoginHistory as LoginHistoryModel
from ...interfaces.repository_interfaces import ILoginHistoryRepository
from ...domain.value_objects.login_history import LoginHistory


class LoginHistoryRepository(ILoginHistoryRepository):
    """登录历史仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, login_history: LoginHistory) -> LoginHistory:
        """创建登录历史记录"""
        login_history_model = LoginHistoryModel(
            user_id=login_history.user_id,
            ip_address=login_history.ip_address,
            user_agent=login_history.user_agent,
            login_role=login_history.login_role,
            location=login_history.location,
            login_time=login_history.login_time
        )
        
        self.db.add(login_history_model)
        self.db.commit()
        self.db.refresh(login_history_model)
        
        return LoginHistory.create(
            user_id=login_history_model.user_id,
            ip_address=login_history_model.ip_address,
            user_agent=login_history_model.user_agent,
            login_role=login_history_model.login_role,
            location=login_history_model.location,
            login_time=login_history_model.login_time
        )
    
    async def get_user_login_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[LoginHistory]:
        """获取用户登录历史"""
        login_histories = (
            self.db.query(LoginHistoryModel)
            .filter(LoginHistoryModel.user_id == user_id)
            .order_by(LoginHistoryModel.login_time.desc())
            .limit(limit)
            .all()
        )
        
        return [
            LoginHistory.create(
                user_id=history.user_id,
                ip_address=history.ip_address,
                user_agent=history.user_agent,
                login_role=history.login_role,
                location=history.location,
                login_time=history.login_time
            )
            for history in login_histories
        ]
    
    async def get_recent_logins(
        self,
        user_id: str,
        since: datetime,
        limit: int = 10
    ) -> List[LoginHistory]:
        """获取用户最近登录记录"""
        login_histories = (
            self.db.query(LoginHistoryModel)
            .filter(
                LoginHistoryModel.user_id == user_id,
                LoginHistoryModel.login_time >= since
            )
            .order_by(LoginHistoryModel.login_time.desc())
            .limit(limit)
            .all()
        )
        
        return [
            LoginHistory.create(
                user_id=history.user_id,
                ip_address=history.ip_address,
                user_agent=history.user_agent,
                login_role=history.login_role,
                location=history.location,
                login_time=history.login_time
            )
            for history in login_histories
        ]
