"""Subscription management and Stripe webhook handler examples.

This FastAPI app demonstrates:
- creating a local subscription record
- granting credits on payment events
- a webhook endpoint to process Stripe events idempotently

Adapt and integrate into your real backend. Use secure signature verification in production.
"""

import json
import os
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

try:
    import asyncpg
except Exception:
    asyncpg = None

try:
    import stripe
except Exception:
    stripe = None

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/healthcare")
STRIPE_SIGNING_SECRET = os.getenv("STRIPE_SIGNING_SECRET")

app = FastAPI()


class CreateSubscriptionRequest(BaseModel):
    user_id: str
    organization_id: str | None = None
    plan_code: str
    provider: str = "stripe"
    provider_customer_id: str | None = None
    provider_subscription_id: str | None = None


async def get_conn():
    """Return asyncpg connection (kept as a stable seam for tests)."""
    if asyncpg is None:
        raise RuntimeError("asyncpg not available")
    return await asyncpg.connect(DATABASE_URL)


async def grant_credits(account_id: str, amount: int, source: str = "manual", metadata: dict | None = None):
    """Grant credits atomically: insert ledger grant and update credit_accounts."""
    conn = await get_conn()
    try:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO credit_ledger(account_id, event_type, final_cost, status, source, metadata, created_at)
                VALUES($1, 'grant', $2, 'settled', $3, $4::jsonb, now())
                """,
                account_id,
                amount,
                source,
                json.dumps(metadata or {}),
            )
            await conn.execute(
                """
                UPDATE credit_accounts
                SET available_credits = available_credits + $1,
                    lifetime_earned = COALESCE(lifetime_earned, 0) + $1,
                    updated_at = now()
                WHERE id = $2
                """,
                amount,
                account_id,
            )
    finally:
        await conn.close()


@app.post("/api/v1/subscriptions/create")
async def create_subscription(req: CreateSubscriptionRequest):
    conn = await get_conn()
    try:
        plan = await conn.fetchrow("SELECT id, monthly_credits FROM plans WHERE code=$1", req.plan_code)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        async with conn.transaction():
            sub = await conn.fetchrow(
                """
                INSERT INTO subscriptions(user_id, organization_id, plan_id, provider, provider_customer_id, provider_subscription_id, status, created_at, updated_at)
                VALUES($1,$2,$3,$4,$5,$6,'active', now(), now())
                RETURNING id
                """,
                req.user_id,
                req.organization_id,
                plan["id"],
                req.provider,
                req.provider_customer_id,
                req.provider_subscription_id,
            )

            acct = await conn.fetchrow(
                "SELECT id FROM credit_accounts WHERE user_id=$1 AND organization_id IS NOT DISTINCT FROM $2",
                req.user_id,
                req.organization_id,
            )
            if not acct:
                acct = await conn.fetchrow(
                    """
                    INSERT INTO credit_accounts(user_id, organization_id, plan_id, available_credits, created_at, updated_at)
                    VALUES($1,$2,$3,$4, now(), now())
                    RETURNING id
                    """,
                    req.user_id,
                    req.organization_id,
                    plan["id"],
                    0,
                )

            monthly = plan["monthly_credits"] or 0
            if monthly > 0:
                await grant_credits(acct["id"], monthly, source="creation_grant", metadata={"plan": req.plan_code})

        return {"status": "ok", "subscription_id": str(sub["id"])}
    finally:
        await conn.close()


@app.get("/api/v1/subscriptions/{subscription_id}")
async def get_subscription(subscription_id: str):
    conn = await get_conn()
    try:
        sub = await conn.fetchrow("SELECT * FROM subscriptions WHERE id=$1", subscription_id)
        if not sub:
            raise HTTPException(status_code=404, detail="Subscription not found")
        return dict(sub)
    finally:
        await conn.close()


def _parse_stripe_event(payload: bytes, sig_header: str | None):
    """Parse/verify Stripe event payload.

    If STRIPE_SIGNING_SECRET and stripe SDK are available, verify signature.
    Otherwise parse JSON for local/dev usage.
    """
    if STRIPE_SIGNING_SECRET and stripe is not None:
        try:
            return stripe.Webhook.construct_event(payload, sig_header, STRIPE_SIGNING_SECRET)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid Stripe signature: {exc}")
    try:
        return json.loads(payload)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")


@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    data = _parse_stripe_event(payload, sig)

    event_id = data.get("id")
    event_type = data.get("type")
    if not event_id or not event_type:
        raise HTTPException(status_code=400, detail="Missing event id/type")

    conn = await get_conn()
    try:
        async with conn.transaction():
            # Prefer dedicated idempotency table if available.
            processed_exists = False
            try:
                processed = await conn.fetchrow("SELECT 1 FROM processed_webhooks WHERE stripe_event_id = $1", event_id)
                processed_exists = bool(processed)
            except Exception:
                # Fall back to audit log based check if table doesn't exist yet.
                processed = await conn.fetchrow("SELECT 1 FROM audit_logs WHERE metadata->>'stripe_event_id' = $1", event_id)
                processed_exists = bool(processed)

            if processed_exists:
                return {"status": "ignored", "reason": "already_processed"}

            if event_type == "invoice.paid":
                invoice = data.get("data", {}).get("object", {})
                stripe_sub_id = invoice.get("subscription")
                local = await conn.fetchrow(
                    "SELECT * FROM subscriptions WHERE provider_subscription_id=$1",
                    stripe_sub_id,
                )
                if local:
                    plan = await conn.fetchrow("SELECT monthly_credits, code FROM plans WHERE id = $1", local["plan_id"])
                    if plan and (plan["monthly_credits"] or 0) > 0:
                        acct = await conn.fetchrow(
                            "SELECT id FROM credit_accounts WHERE user_id=$1 AND organization_id IS NOT DISTINCT FROM $2",
                            local["user_id"],
                            local["organization_id"],
                        )
                        if acct:
                            await grant_credits(
                                acct["id"],
                                plan["monthly_credits"],
                                source="stripe_invoice",
                                metadata={"stripe_invoice_id": invoice.get("id")},
                            )

            elif event_type == "customer.subscription.deleted":
                sub = data.get("data", {}).get("object", {})
                stripe_sub_id = sub.get("id")
                await conn.execute(
                    "UPDATE subscriptions SET status=$1, updated_at=now() WHERE provider_subscription_id=$2",
                    "canceled",
                    stripe_sub_id,
                )

            # Record idempotency marker in whichever table is available.
            wrote_marker = False
            try:
                await conn.execute(
                    "INSERT INTO processed_webhooks(stripe_event_id, payload, processed_at) VALUES($1, $2::jsonb, now())",
                    event_id,
                    json.dumps(data),
                )
                wrote_marker = True
            except Exception:
                wrote_marker = False

            await conn.execute(
                "INSERT INTO audit_logs(actor_user_id, organization_id, action, target_type, target_id, metadata, created_at) VALUES($1,$2,$3,$4,$5,$6,now())",
                None,
                None,
                "stripe_webhook",
                event_type,
                event_id,
                json.dumps({"stripe_event_id": event_id, "processed_webhooks": wrote_marker}),
            )

            return {"status": "ok"}
    finally:
        await conn.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
