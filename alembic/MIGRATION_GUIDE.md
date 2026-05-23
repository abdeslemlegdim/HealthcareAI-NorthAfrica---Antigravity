Processed Webhooks Migration Guide
=================================

Purpose
-------
This document describes the `processed_webhooks` migration that was added to persist Stripe event idempotency markers. The table prevents replayed Stripe events from being processed multiple times and is used by the webhook handler in `backend_examples/subscriptions_api.py`.

Migration
---------
- Migration file: `alembic/versions/1c4b53d9f7a1_add_processed_webhooks_table.py`
- Table schema (conceptual):

  - `id` (serial / bigint primary key)
  - `stripe_event_id` (string, unique) — the Stripe `event.id` value
  - `received_at` (timestamp with timezone) — when the webhook was recorded
  - `payload` (json / text) — optional raw event payload for debugging

How to run
----------
1. Ensure your `DATABASE_URL` environment variable points to the target database.
2. From the repository root, run:

```bash
alembic upgrade head
```

Verify the table
--------------
You can confirm the table exists and inspect rows with a psql session or any SQL client. Example SQL:

```sql
-- list tables
\dt

-- inspect recent processed webhooks
SELECT stripe_event_id, received_at FROM processed_webhooks ORDER BY received_at DESC LIMIT 50;
```

Operational notes
-----------------
- The webhook handler attempts to verify signatures when `STRIPE_SIGNING_SECRET` is configured. Set `STRIPE_SIGNING_SECRET` in your environment to enable signature verification.
- The webhook handler will insert into `processed_webhooks` inside a transaction when processing an event; if insertion fails due to a unique constraint, the webhook is considered already-processed.
- Keep an eye on table growth; you may want a TTL / archival strategy for older processed event records.

Live webhook replay test
------------------------
1. Configure `STRIPE_SIGNING_SECRET` in your environment and restart the backend.
2. Use Stripe CLI or dashboard to send a real or test webhook to your `/webhook/stripe` endpoint.
3. Verify the webhook created a `processed_webhooks` row and that credits were applied exactly once.

Contact
-------
If you need assistance running the migration or verifying webhooks in production, tell me which DB connection to use or provide access details and I can run the verification steps for you.
