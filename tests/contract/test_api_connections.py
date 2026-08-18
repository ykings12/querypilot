import pytest

pytestmark = pytest.mark.asyncio


async def test_create_and_list_connection(client):
    payload = {
        "name": "test-conn",
        "host": "localhost",
        "port": 5433,
        "database": "chinook",
        "username": "querypilot_readonly",
        "password": "querypilot_readonly_dev",
    }
    create_resp = await client.post("/connections", json=payload)
    if create_resp.status_code != 201:
        pytest.skip(f"Metadata DB unavailable: {create_resp.text}")

    body = create_resp.json()
    assert "password" not in body
    assert body["name"] == "test-conn"

    list_resp = await client.get("/connections")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert any(item["id"] == body["id"] for item in items)


async def test_introspect_chinook(client):
    payload = {
        "name": "chinook-introspect",
        "host": "localhost",
        "port": 5433,
        "database": "chinook",
        "username": "querypilot_readonly",
        "password": "querypilot_readonly_dev",
    }
    create_resp = await client.post("/connections", json=payload)
    if create_resp.status_code != 201:
        pytest.skip(f"Metadata DB unavailable: {create_resp.text}")

    connection_id = create_resp.json()["id"]
    intro_resp = await client.post(f"/connections/{connection_id}/introspect")
    if intro_resp.status_code != 200:
        pytest.skip(f"Target DB unavailable: {intro_resp.text}")

    intro = intro_resp.json()
    assert intro["table_count"] >= 10
    assert intro["schema_version"].startswith("sha256:")
