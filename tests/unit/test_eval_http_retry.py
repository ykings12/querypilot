import httpx

from eval.http_retry import (
    is_transient_http_response,
    is_transient_transport_error,
    post_json_with_retry,
)


def test_transient_502_dns():
    body = '{"detail":"Query failed: [Errno -3] Temporary failure in name resolution"}'
    assert is_transient_http_response(502, body) is True


def test_non_transient_404():
    assert is_transient_http_response(404, "not found") is False


def test_transport_errors():
    assert is_transient_transport_error(httpx.ConnectError("fail")) is True
    assert is_transient_transport_error(httpx.RemoteProtocolError("disc")) is True
    assert is_transient_transport_error(ValueError("nope")) is False


class _FakeClient:
    def __init__(self, responses: list[httpx.Response | Exception]) -> None:
        self._responses = list(responses)
        self.calls = 0

    def post(self, path: str, json: dict) -> httpx.Response:
        self.calls += 1
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def test_post_retries_transient_502(monkeypatch):
    monkeypatch.setenv("EVAL_HTTP_RETRIES", "1")
    bad = httpx.Response(502, text='{"detail":"name resolution"}')
    ok = httpx.Response(200, json={"sql": "select 1", "columns": [], "rows": []})
    client = _FakeClient([bad, ok])
    response, err, attempts = post_json_with_retry(client, "/query", {"q": "x"})
    assert err is None
    assert response is not None
    assert response.status_code == 200
    assert attempts == 2
    assert client.calls == 2
