"""
项目已从旧 DDD 目录结构重构，本测试文件更新为“关键能力单测”。
"""

from unittest.mock import MagicMock


def test_channel_identity_service_bind_calls_migrate() -> None:
    from app.channels.services.channel_identity_service import ChannelIdentityService
    from app.channels.models.channel_identity import ChannelIdentity

    db = MagicMock()
    # db.query(User).filter(...).first() -> user
    user = MagicMock()
    user.id = "usr_target"
    db.query.return_value.filter.return_value.first.return_value = user

    svc = ChannelIdentityService(db=db)
    identity = ChannelIdentity(channel_type="wechat_work_kf", peer_id="peer_x", user_id="usr_old")

    # 避免走真实查询：固定返回 existing identity
    svc.get_by_type_peer = MagicMock(return_value=identity)  # type: ignore
    svc._migrate_channel_conversations = MagicMock(return_value=1)  # type: ignore

    out = svc.bind_identity(
        channel_type="wechat_work_kf",
        peer_id="peer_x",
        customer_user_id="usr_target",
        peer_name="张三",
        extra_data={"peer_name": "张三"},
        migrate_conversations=True,
    )

    assert out.user_id == "usr_target"
    svc._migrate_channel_conversations.assert_called_once()
