"""FastAPI examples showing how to call the Postgres ledger functions.

This is illustrative code — adapt to your project's DB layer and error handling.
Requires: fastapi, uvicorn, asyncpg, pydantic
"""
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import asyncio
import os
import asyncpg

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/healthcare')

app = FastAPI()


class RunRequest(BaseModel):
    user_id: str
    account_id: str
    organization_id: str | None = None
    feature_key: str
    request_id: str
    payload: dict


async def get_conn():
    return await asyncpg.connect(DATABASE_URL)


async def run_inference_simulation(payload: dict) -> dict:
    # Replace with real inference call — this simulates runtime and cost
    await asyncio.sleep(0.2)
    # Example inference output and computed cost
    return {"diagnosis": "normal", "confidence": 0.92, "_final_cost": 10}


@app.post('/api/v1/ai/run')
async def run_ai(req: RunRequest):
    conn = await get_conn()
    try:
        # Estimate cost server-side based on feature and payload
        estimated_cost = 12  # implement your estimator here

        # Reserve credits using the DB function
        row = await conn.fetchrow('SELECT * FROM reserve_credits($1,$2,$3,$4,$5,$6,$7,$8)',
                                  req.account_id, req.user_id, req.organization_id, req.request_id,
                                  req.feature_key, estimated_cost, 'api', '{}')
        ledger_id = row['ledger_id'] if row else None
        reserved = row['reserved'] if row else 0
        if not reserved or reserved == 0:
            raise HTTPException(status_code=402, detail='Not enough credits')

        # Run the inference (could be sync or enqueued to a worker)
        result = await run_inference_simulation(req.payload)

        final_cost = int(result.get('_final_cost', estimated_cost))

        # Settle reservation
        settle_row = await conn.fetchrow('SELECT * FROM settle_credits($1,$2,$3)', req.account_id, req.request_id, final_cost)

        # Insert usage_events record for analytics
        await conn.execute('''
            INSERT INTO usage_events(user_id, organization_id, request_id, feature_key, action_type, model_name, input_size_bytes, output_size_bytes, duration_ms, credits_estimated, credits_charged, status, created_at)
            VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,'completed', now())
        ''', req.user_id, req.organization_id, req.request_id, req.feature_key, 'inference', 'sim-model', 0, 0, 200, estimated_cost, final_cost)

        return {"result": result, "credits_charged": final_cost}

    except HTTPException:
        raise
    except Exception as exc:
        # On error, reverse reservation
        try:
            await conn.fetchrow('SELECT * FROM reverse_reservation($1,$2,$3)', req.account_id, req.request_id, str(exc))
        except Exception:
            pass
        raise HTTPException(status_code=500, detail='Internal error')
    finally:
        await conn.close()


class RefundRequest(BaseModel):
    ledger_id: str
    reason: str | None = None


@app.post('/api/v1/admin/refund')
async def refund(req: RefundRequest):
    conn = await get_conn()
    try:
        async with conn.transaction():
            # Lock and insert refund entry and update balances (basic flow)
            # The SQL snippet in database/sql_samples.sql can be used; here we show a simplified flow
            ledger = await conn.fetchrow('SELECT id, account_id, final_cost FROM credit_ledger WHERE id=$1 FOR UPDATE', req.ledger_id)
            if not ledger:
                raise HTTPException(status_code=404, detail='Ledger entry not found')
            if ledger['status'] != 'settled':
                raise HTTPException(status_code=400, detail='Can only refund settled charges')

            refund_amount = -ledger['final_cost']
            await conn.execute('''
                INSERT INTO credit_ledger(account_id, user_id, organization_id, event_type, feature_key, request_id, estimated_cost, final_cost, status, source, metadata, created_at)
                SELECT account_id, user_id, organization_id, 'refund', feature_key, request_id, 0, $1, 'refunded', 'admin', jsonb_build_object('refund_of', id, 'note', $2), now()
                FROM credit_ledger WHERE id = $3
            ''', refund_amount, req.reason, req.ledger_id)

            await conn.execute('UPDATE credit_accounts SET available_credits = available_credits + $1, updated_at = now() WHERE id = $2', -refund_amount, ledger['account_id'])

        return {"status": "ok", "refunded": -refund_amount}
    finally:
        await conn.close()


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8002)
