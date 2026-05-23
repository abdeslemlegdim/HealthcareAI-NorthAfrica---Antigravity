# Postgres schema and ledger flow for Healthcare AI credit system

This folder contains the v1 SQL DDL and guidance for implementing a reliable credit ledger, subscriptions, and usage metering for the platform.

Files:

- `v1_schema.sql` — PostgreSQL DDL creating tables, indexes, and PL/pgSQL helper functions for reserve/settle flows.

Design principles

- Credits are accounted in a ledger (`credit_ledger`) not a single mutable balance.
- `credit_accounts` stores derived balances (available, reserved) for fast checks; the ledger is the source of truth.
- Reserve → run job → settle pattern ensures failed jobs can release reserved credits.
- Use transactions when reserving/settling credits.
- Keep events auditable with `usage_events` and `audit_logs`.

Quick start

1. Apply `v1_schema.sql` to a Postgres instance.
2. Use the `reserve_credits` and `settle_credits` functions to perform credit operations atomically.

Notes

- The functions assume `credit_accounts.available_credits` and `credit_accounts.reserved_credits` are maintained.
- For high throughput, consider sharding accounts by organization or using lightweight caches with strong reconciliation.
