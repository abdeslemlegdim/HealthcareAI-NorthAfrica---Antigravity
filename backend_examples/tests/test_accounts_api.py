import pytest
from httpx import AsyncClient, ASGITransport

from backend_examples import accounts_api


@pytest.mark.asyncio
async def test_account_summary_mock(monkeypatch):
    # Force get_conn to raise so the endpoint returns mock data
    async def fake_get_conn():
        raise RuntimeError("no db")

    monkeypatch.setattr(accounts_api, "get_conn", fake_get_conn)

    transport = ASGITransport(app=accounts_api.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/accounts/test-account/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["account_id"] == "test-account"
        assert "available_credits" in data


@pytest.mark.asyncio
async def test_account_summary_db_row(monkeypatch):
    class FakeConn:
        async def fetchrow(self, *a, **k):
            return {
                "account_id": "acct-1",
                "available_credits": 42,
                "reserved_credits": 2,
                "lifetime_earned": 1000,
                "lifetime_spent": 958,
            }
        async def close(self):
            return

    async def fake_get_conn():
        return FakeConn()

    monkeypatch.setattr(accounts_api, "get_conn", fake_get_conn)

    transport = ASGITransport(app=accounts_api.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/accounts/acct-1/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["available_credits"] == 42
        assert data["reserved_credits"] == 2


@pytest.mark.asyncio
async def test_account_summary_me_fallback_zero(monkeypatch):
    class FakeUser:
        id = 123

    async def fake_get_conn():
        raise RuntimeError("no db")

    async def fake_current_user_dep():
        return FakeUser()

    monkeypatch.setattr(accounts_api, "get_conn", fake_get_conn)
    accounts_api.app.dependency_overrides[accounts_api._require_current_user_dep] = fake_current_user_dep

    try:
        transport = ASGITransport(app=accounts_api.app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/accounts/me/summary")
            assert resp.status_code == 200
            data = resp.json()
            assert data["available_credits"] == 0
            assert data["reserved_credits"] == 0
            assert data["lifetime_earned"] == 0
            assert data["lifetime_spent"] == 0
    finally:
        accounts_api.app.dependency_overrides.pop(accounts_api._require_current_user_dep, None)
