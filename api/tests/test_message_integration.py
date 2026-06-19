"""
项目已从旧 DDD 目录结构重构，本测试文件更新为“关键能力单测”。
"""


def test_channel_service_imports() -> None:
    from app.channels.services.channel_service import ChannelService

    assert ChannelService is not None
