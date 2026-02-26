import pytest
import hashlib
from services.pdd_channel import PddChannel

def test_verify_webhook_signature_valid():
    """合法签名应通过验证"""
    channel = PddChannel(webhook_token="my_token")
    body = b'{"type":"IM_NEW_MESSAGE","data":{}}'
    # 模拟拼多多签名：MD5(token + body)
    expected_sign = hashlib.md5(b"my_token" + body).hexdigest()
    assert channel.verify_signature(body, expected_sign) is True

def test_verify_webhook_signature_invalid():
    """非法签名应拒绝"""
    channel = PddChannel(webhook_token="my_token")
    body = b'{"type":"IM_NEW_MESSAGE"}'
    assert channel.verify_signature(body, "wrong_sign") is False

def test_parse_new_message_event():
    """解析新消息事件"""
    channel = PddChannel(webhook_token="my_token")
    payload = {
        "type": "IM_NEW_MESSAGE",
        "data": {
            "conversation_id": "conv_abc",
            "sender_id": "buyer_123",
            "content": "这个商品还有货吗",
            "msg_type": 1,
        }
    }
    msg = channel.parse_message(payload)
    assert msg["conversation_id"] == "conv_abc"
    assert msg["content"] == "这个商品还有货吗"
    assert msg["is_buyer"] is True

def test_should_transfer_to_human():
    """检测转人工关键词"""
    channel = PddChannel(webhook_token="my_token")
    assert channel.should_transfer_to_human("我要转人工") is True
    assert channel.should_transfer_to_human("这个多少钱") is False
    assert channel.should_transfer_to_human("我要投诉") is True
