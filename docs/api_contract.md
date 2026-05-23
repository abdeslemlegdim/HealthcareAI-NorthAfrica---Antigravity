# Billing & Subscription API contract (summary)

- POST /api/v1/ai/run
  - Purpose: Reserve credits and trigger inference in a single client flow.
  - Flow: server validates account, calls `reserve_credits(account_id, amount, request_id)`, returns reservation id and pre-flight result. Client runs model; server calls `settle_credits(reservation_id, final_cost, metadata)`.

- POST /api/v1/subscriptions/create
  - Purpose: Create a subscription record and grant initial credits according to plan.
  - Idempotency: Accept `request_id` to dedupe.

- POST /webhook/stripe
  - Purpose: Receive Stripe invoice / subscription events. MUST verify `Stripe-Signature` header with `STRIPE_SIGNING_SECRET` and persist `stripe_event_id` for idempotency.
  - On `invoice.paid` → grant credits via ledger `grant` entry in a DB transaction.

- POST /api/v1/admin/refund
  - Purpose: Admin-triggered refund that inserts a ledger `refund` row and adjusts `credit_accounts` atomically.

- GET /api/v1/accounts/{accountId}/summary
  - Purpose: Dashboard UI reads current `available_credits`, `reserved_credits`, and lifetime stats.

Notes

- All money or credit-affecting operations are written as opaque ledger rows in `credit_ledger`.
- Use `request_id` and `stripe_event_id` to ensure idempotent processing.
- Do not trust client-provided cost estimates; always reconcile with `settle_credits`.
