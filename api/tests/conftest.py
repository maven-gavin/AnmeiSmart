import pytest
import sys
import os
from typing import Generator, Dict
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 创建测试应用，不带启动事件
from main import app 
from app.db.base import get_db, SessionLocal, engine
from app.core.config import get_settings

# 禁用startup事件中的数据库初始化
app.router.on_startup = []

settings = get_settings()

pytest_plugins = ("pytest_asyncio",)

# 使用应用中已配置的数据库
# TestingSessionLocal = SessionLocal

# @pytest.fixture(scope="session")
# def db() -> Generator[Session, None, None]:
#     """测试数据库会话"""
#     # 我们使用已有的数据库，不创建新表
#     db = TestingSessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """带事务的测试数据库会话，每个测试后自动回滚"""
    # 创建会话，开始事务
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    
    try:
        yield session
    finally:
        # 测试结束后回滚事务
        session.close()
        transaction.rollback()
        connection.close()
        

# @pytest.fixture(scope="module")
# def client(db: Session) -> Generator[TestClient, None, None]:
#     """测试客户端"""
#     def override_get_db():
#         try:
#             yield db
#         finally:
#             db.close()
    
#     app.dependency_overrides[get_db] = override_get_db
#     with TestClient(app) as c:
#         yield c

@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """使用事务数据库的测试客户端"""
    def override_get_db():
        try:
            yield db
        finally:
            pass  # 不关闭会话，由db fixture处理
    
    # 保存原始依赖
    original_dependency = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    # 恢复原始依赖
    app.dependency_overrides = original_dependency
            
@pytest.fixture(scope="function")
def test_user() -> Dict[str, str]:
    """使用已存在的顾问用户"""
    return {
        "email": "li@example.com",
        "username": "李顾问",
        "password": "123456@Test"
    } 

@pytest.fixture(scope="function")
def get_token(client: TestClient, test_user: Dict[str, str]) -> str:
    """测试获取当前用户信息"""
    # 先登录获取token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]