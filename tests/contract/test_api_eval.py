import pytest


@pytest.mark.asyncio
async def test_list_eval_runs_empty(client):
    response = await client.get("/eval/runs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
