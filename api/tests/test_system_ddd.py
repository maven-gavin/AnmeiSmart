"""
项目已从旧 DDD 目录结构重构。

该测试保留为“系统模块可导入”与“模型存在性”检查，避免测试收集阶段因旧路径失败。
"""


def test_system_models_importable() -> None:
    import app.system.models  # noqa: F401
