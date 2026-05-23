import asyncio
import pytest
from httpx import AsyncClient

from ledger_api_example import app


@pytest.mark.asyncio
async def test_run_ai_insufficient_credits(monkeypatch):
    async def fake_connect():
        class C:
            async def fetchrow(self, *a, **k):
                return {'ledger_id': None, 'reserved': 0}
            async def execute(self, *a, **k):
                return
            async def close(self):
                return
        return C()

    monkeypatch.setattr('ledger_api_example.get_conn', fake_connect)

    async with AsyncClient(app=app, base_url='http://test') as ac:
        resp = await ac.post('/api/v1/ai/run', json={
            'user_id': 'u1', 'account_id': 'a1', 'feature_key': 'imaging', 'request_id': 'r1', 'payload': {}
        })
        assert resp.status_code == 402
