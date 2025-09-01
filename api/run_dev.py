import uvicorn
import os
import sys
from app.common.infrastructure.db.base import init_db, create_initial_roles

def run_dev_server():
    """
    运行开发服务器，初始化数据库和角色
    """
    # 初始化数据库
    print("初始化数据库...")
    init_db()
    
    # 创建初始角色
    print("创建初始角色...")
    create_initial_roles()
    
    # 启动服务器
    print("启动开发服务器...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    # 添加当前目录到系统路径
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    run_dev_server() 