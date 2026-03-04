import hashlib
import hmac

from services.platform.douyin_client import DouyinClient


def test_sign_generation_hmac_sha256():
    client = DouyinClient(app_key="app_key_1", app_secret="secret_1")
    params = {
        "app_key": "app_key_1",
        "method": "order.searchList",
        "param_json": '{"page":1,"size":20}',
        "timestamp": "1700000000",
        "v": "2",
    }
    sign = client.sign_request(params, sign_method="hmac-sha256")
    assert isinstance(sign, str)
    assert len(sign) == 64


def test_sign_generation_md5():
    client = DouyinClient(app_key="app_key_1", app_secret="secret_1")
    params = {
        "app_key": "app_key_1",
        "method": "product.detail",
        "param_json": '{"product_id":"123"}',
        "timestamp": "1700000000",
        "v": "2",
    }
    sign = client.sign_request(params, sign_method="md5")
    assert isinstance(sign, str)
    assert len(sign) == 32


def test_verify_webhook_signature_md5():
    app_key = "test_app_key"
    app_secret = "test_app_secret"
    body = b'[{"tag":"100","msg_id":"1","data":{"shop_id":123}}]'
    sign_source = f"{app_key}{body.decode()}{app_secret}"
    signature = hashlib.md5(sign_source.encode("utf-8")).hexdigest()

    client = DouyinClient(app_key=app_key, app_secret=app_secret)
    assert client.verify_webhook_signature(
        body=body,
        signature=signature,
        app_id=app_key,
        sign_method="md5",
    )


def test_verify_webhook_signature_hmac_sha256():
    app_key = "test_app_key"
    app_secret = "test_app_secret"
    body = b'[{"tag":"100","msg_id":"1","data":{"shop_id":123}}]'
    sign_source = f"{app_key}{body.decode()}{app_secret}"
    signature = hmac.new(
        app_secret.encode("utf-8"),
        sign_source.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    client = DouyinClient(app_key=app_key, app_secret=app_secret)
    assert client.verify_webhook_signature(
        body=body,
        signature=signature,
        app_id=app_key,
        sign_method="hmac-sha256",
    )
