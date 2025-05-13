#!/usr/bin/env python
"""
MongoDB连接测试脚本
"""
import sys
import os
import traceback

try:
    import pymongo
    from pymongo import MongoClient
    print(f"✓ 已安装pymongo版本: {pymongo.__version__}")
except ImportError:
    print("✗ 未安装pymongo模块")
    print("请使用以下命令安装: pip install pymongo")
    sys.exit(1)

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 尝试从配置中获取MongoDB连接信息
mongo_url = None
try:
    from app.core.config import get_settings
    settings = get_settings()
    mongo_url = settings.MONGODB_URL
    print(f"✓ 从配置中获取到MongoDB连接URL: {mongo_url}")
except Exception as e:
    print(f"✗ 无法从配置中获取MongoDB连接信息: {str(e)}")
    mongo_url = "mongodb://localhost:27017"
    print(f"使用默认连接URL: {mongo_url}")

# 测试MongoDB连接
print("\n正在测试MongoDB连接...")
try:
    client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
    # 使用服务器信息来验证连接
    server_info = client.server_info()
    print(f"✓ 成功连接到MongoDB!")
    print(f"MongoDB版本: {server_info.get('version', 'unknown')}")
    
    # 列出所有数据库
    print("\n可用数据库:")
    for db_name in client.list_database_names():
        print(f" - {db_name}")
    
    # 创建/获取我们的数据库
    db = client.medical_beauty
    print(f"\n已选择数据库: medical_beauty")
    
    # 列出集合
    print("当前集合:")
    for collection_name in db.list_collection_names():
        print(f" - {collection_name}")
        # 显示集合中的文档数量
        count = db[collection_name].count_documents({})
        print(f"   文档数量: {count}")
    
    # 添加一个测试文档
    test_collection = db.test_collection
    test_id = test_collection.insert_one({"test": True, "message": "MongoDB连接测试成功", "timestamp": pymongo.datetime.datetime.utcnow()}).inserted_id
    print(f"\n✓ 成功插入测试文档，ID: {test_id}")
    
    # 检索测试文档
    test_doc = test_collection.find_one({"_id": test_id})
    print(f"✓ 成功检索测试文档: {test_doc}")
    
    # 删除测试文档
    test_collection.delete_one({"_id": test_id})
    print(f"✓ 成功删除测试文档")
    
    print("\n✓ MongoDB连接和基本操作测试通过!")
    
except pymongo.errors.ServerSelectionTimeoutError as e:
    print(f"✗ 无法连接到MongoDB服务器: {str(e)}")
    print("\n可能的原因:")
    print(" - MongoDB服务未运行")
    print(" - 连接URL不正确")
    print(" - 网络问题")
    print("\n请确保MongoDB服务已启动，并检查连接URL。")
    
except pymongo.errors.OperationFailure as e:
    print(f"✗ 操作失败: {str(e)}")
    print("\n可能是身份验证失败，请检查用户名和密码。")
    
except Exception as e:
    print(f"✗ 发生未知错误: {str(e)}")
    print("\n堆栈跟踪:")
    traceback.print_exc()
    
finally:
    if 'client' in locals():
        client.close()
        print("MongoDB连接已关闭")

print("\n如需更多帮助，请查阅MongoDB文档: https://docs.mongodb.com/") 