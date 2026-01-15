"""
聊天服务模块 - 新架构
"""

# 注意：该包的 __init__ 不应做任何“导入控制器/服务”的副作用操作，
# 否则很容易在 channels/customer 等模块引入 ChatService 时触发循环导入。
# 路由注册请直接从 app.chat.controllers 引入，模型/服务请从对应子模块引入。

__all__ = []
