# API examples — using the ledger functions

This file shows minimal, production-oriented pseudocode and HTTP endpoints for using the `reserve_credits`, `settle_credits`, and `reverse_reservation` functions defined in `v1_schema.sql`.

Assumptions
- Backend uses Postgres and can call the PL/pgSQL functions via a DB client.
- Use transactions for safety when performing reserve and settle operations.

Examples

1) FastAPI-style endpoint: reserve before running an inference

POST /api/v1/ai/run

Request body:
{
  "user_id": "...",
  "account_id": "...",
  "feature_key": "imaging_classify",
  "request_id": "uuid-client-generated",
  "estimated_cost": 12,
  "payload": { ... }
}

Handler (pseudocode):

def run_ai_endpoint(req):
    # 1. authenticate + authorize
    account_id = req.account_id
    # 2. estimate cost server-side (based on feature, model, size)
    estimated = req.estimated_cost

    # 3. call reserve_credits (atomic)
    ledger_id, reserved = db.call('select * from reserve_credits($1,$2,$3,$4,$5,$6,$7,$8)',
                                  [account_id, user_id, org_id, req.request_id, req.feature_key, estimated, 'api', json_metadata])
    if reserved == 0:
        return 402, {"error":"Not enough credits"}

    # 4. enqueue or run the job
    try:
       result = run_inference(req.payload)
    except Exception as err:
       # Release reservation
       db.call('select * from reverse_reservation($1,$2,$3)', [account_id, req.request_id, str(err)])
       raise

    # 5. compute actual cost (final_cost)
    final_cost = compute_final_cost(result)

    # 6. settle reservation
    ledger_id, charged, refunded = db.call('select * from settle_credits($1,$2,$3)', [account_id, req.request_id, final_cost])

    # 7. write usage_events row for analytics (credits_charged etc.)
    db.insert('usage_events', {...})

    return 200, {"result": result, "credits_charged": charged}

Notes:
- The backend should never rely on client-provided estimates for authorization; compute server-side.
- Use `reverse_reservation` on errors or cancellations.
- Log the full request_id in `usage_events` and `credit_ledger` to correlate logs and allow reconciliation.

2) Quick refund flow (admin endpoint)

POST /api/v1/admin/refund
{
  "ledger_id":"...",
  "reason":"incorrect charge"
}

Handler:
def refund_handler(req):
    ledger = db.fetch_one('select * from credit_ledger where id=$1', [req.ledger_id])
    if not ledger or ledger.status != 'settled':
        return 400
    -- create a reversing ledger entry
    db.insert('credit_ledger', {account_id: ledger.account_id, event_type:'refund', estimated_cost:0, final_cost:-ledger.final_cost, status:'refunded', metadata:{reason:req.reason}})
    -- add back credits
    db.update('credit_accounts', {available_credits: available_credits + ledger.final_cost, updated_at: now()}, where id=ledger.account_id)
    -- insert invoice/adjustment record as needed

3) Monthly refill (cron job)

Run by scheduler at billing renewal time for each account:
- Find accounts with plan.monthly_credits > 0
- Create a credit_ledger row of type 'grant' with estimated_cost = monthly_credits
- Update credit_accounts.available_credits += monthly_credits
- Optionally set reset_at to next renewal date

This file provides examples—adapt to your framework and language.
