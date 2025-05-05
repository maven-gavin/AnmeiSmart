from sqlalchemy.orm import Session

from app.crud import crud_user
from app.core.config import get_settings
from app.models.user import UserCreate
from app.db.base import Base, engine

settings = get_settings()

def init_db(db: Session) -> None:
    """初始化数据库"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 创建初始管理员用户
    user = crud_user.get_by_email(db, email="admin@example.com")
    if not user:
        user_in = UserCreate(
            email="admin@example.com",
            username="admin",
            password="admin123",
            is_active=True
        )
        user = crud_user.create(db, obj_in=user_in)

if __name__ == "__main__":
    from app.db.base import SessionLocal
    db = SessionLocal()
    init_db(db) 