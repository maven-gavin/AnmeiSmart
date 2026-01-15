"""
项目已从旧 DDD 目录结构重构，本测试文件更新为“冒烟导入测试”。

目标：确保核心模块可被导入（避免循环导入导致测试收集阶段失败）。
"""


def test_imports_smoke() -> None:
    import app.chat.models  # noqa: F401
    import app.channels.services.channel_service  # noqa: F401
    import app.channels.services.channel_identity_service  # noqa: F401
    import app.customer.services.customer_insight_ai_service  # noqa: F401
