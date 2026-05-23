import pytest
from httpx import AsyncClient, ASGITransport
from backend_examples.subscriptions_api import app


@pytest.mark.asyncio
async def test_create_subscription_plan_not_found(monkeypatch):
    async def fake_connect():
        class C:
            async def fetchrow(self, *a, **k):
                return None
            async def execute(self, *a, **k):
                return
            async def close(self):
                return
        return C()

    monkeypatch.setattr('backend_examples.subscriptions_api.get_conn', fake_connect)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        resp = await ac.post('/api/v1/subscriptions/create', json={'user_id': 'u1', 'plan_code': 'nope'})
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_stripe_webhook_idempotent_replay(monkeypatch):
    class Tx:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeConn:
        def __init__(self):
            self.processed_events = set()

        def transaction(self):
            return Tx()

        async def fetchrow(self, query, *args):
            if 'FROM processed_webhooks' in query:
                event_id = args[0]
                return {'stripe_event_id': event_id} if event_id in self.processed_events else None

            if 'FROM subscriptions WHERE provider_subscription_id' in query:
                return {'plan_id': 10, 'user_id': 'u1', 'organization_id': None}

            if 'FROM plans WHERE id' in query:
                return {'monthly_credits': 100, 'code': 'starter'}

            if 'FROM credit_accounts WHERE user_id' in query:
                return {'id': 'acct-1'}

            if "FROM audit_logs WHERE metadata->>'stripe_event_id'" in query:
                return None

            return None

        async def execute(self, query, *args):
            if 'INSERT INTO processed_webhooks' in query:
                self.processed_events.add(args[0])
            return

        async def close(self):
            return

    fake_conn = FakeConn()

    async def fake_connect():
        return fake_conn

    async def fake_grant_credits(*args, **kwargs):
        return

    monkeypatch.setattr('backend_examples.subscriptions_api.get_conn', fake_connect)
    monkeypatch.setattr('backend_examples.subscriptions_api.grant_credits', fake_grant_credits)

    payload = {
        'id': 'evt_123',
        'type': 'invoice.paid',
        'data': {
            'object': {
                'id': 'in_123',
                'subscription': 'sub_123'
            }
        }
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        first = await ac.post('/webhook/stripe', json=payload)
        assert first.status_code == 200
        assert first.json()['status'] == 'ok'

        second = await ac.post('/webhook/stripe', json=payload)
        assert second.status_code == 200
        assert second.json()['status'] == 'ignored'
        assert second.json()['reason'] == 'already_processed'
