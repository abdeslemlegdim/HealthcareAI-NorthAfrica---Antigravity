from fastapi import FastAPI, Depends, HTTPException
import asyncio
import os

try:
    import asyncpg
except Exception:
    asyncpg = None

try:
    from src.auth.middleware import get_current_user
except Exception:
    get_current_user = None

app = FastAPI()


async def get_conn():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL not set")
    if asyncpg is None:
        raise RuntimeError("asyncpg not available")
    return await asyncpg.connect(dsn)


def _summary_zero(account_id: str | None = None) -> dict:
    return {
        "account_id": account_id,
        "available_credits": 0,
        "reserved_credits": 0,
        "lifetime_earned": 0,
        "lifetime_spent": 0,
    }


async def _query_with_sqlalchemy_by_account_id(account_id: str):
    """Try to fetch account summary by account id through SQLAlchemy SessionLocal."""
    try:
        from src import database as app_db
        from sqlalchemy import text
    except Exception:
        return None

    def _sync_query():
        session = app_db.SessionLocal()
        try:
            # v1 ledger schema (event_type/final_cost, account UUID in `id`)
            q_v1 = text(
                """
                SELECT CAST(a.id AS TEXT) AS account_id, a.available_credits, a.reserved_credits,
                  COALESCE(lifetime.lifetime_earned,0) AS lifetime_earned,
                  COALESCE(lifetime.lifetime_spent,0) AS lifetime_spent
                FROM credit_accounts a
                LEFT JOIN (
                  SELECT account_id,
                    SUM(CASE WHEN event_type = 'grant' THEN final_cost ELSE 0 END) AS lifetime_earned,
                    SUM(CASE WHEN event_type IN ('charge','settle') THEN final_cost ELSE 0 END) AS lifetime_spent
                  FROM credit_ledger
                  GROUP BY account_id
                ) lifetime ON lifetime.account_id = a.id
                WHERE CAST(a.id AS TEXT) = :account_id
                """
            )
            result = session.execute(q_v1, {"account_id": account_id}).fetchone()
            if result:
                return dict(result._mapping)

            # legacy example schema (entry_type/amount, account key in `account_id`)
            q_legacy = text(
                """
                SELECT CAST(a.account_id AS TEXT) AS account_id, a.available_credits, a.reserved_credits,
                  COALESCE(lifetime.lifetime_earned,0) AS lifetime_earned,
                  COALESCE(lifetime.lifetime_spent,0) AS lifetime_spent
                FROM credit_accounts a
                LEFT JOIN (
                  SELECT account_id,
                    SUM(CASE WHEN entry_type = 'grant' THEN amount ELSE 0 END) AS lifetime_earned,
                    SUM(CASE WHEN entry_type IN ('charge','settle') THEN amount ELSE 0 END) AS lifetime_spent
                  FROM credit_ledger
                  GROUP BY account_id
                ) lifetime ON lifetime.account_id = a.account_id
                WHERE CAST(a.account_id AS TEXT) = :account_id
                """
            )
            result = session.execute(q_legacy, {"account_id": account_id}).fetchone()
            if result:
                return dict(result._mapping)

            return None
        except Exception:
            return None
        finally:
            session.close()

    return await asyncio.to_thread(_sync_query)


async def _query_with_sqlalchemy_by_user_id(user_id: str):
    """Try to fetch latest account summary for a user through SQLAlchemy SessionLocal."""
    try:
        from src import database as app_db
        from sqlalchemy import text
    except Exception:
        return None

    def _sync_query():
        session = app_db.SessionLocal()
        try:
            q = text(
                """
                SELECT CAST(a.id AS TEXT) AS account_id, a.available_credits, a.reserved_credits,
                  COALESCE(lifetime.lifetime_earned,0) AS lifetime_earned,
                  COALESCE(lifetime.lifetime_spent,0) AS lifetime_spent
                FROM credit_accounts a
                LEFT JOIN (
                  SELECT account_id,
                    SUM(CASE WHEN event_type = 'grant' THEN final_cost ELSE 0 END) AS lifetime_earned,
                    SUM(CASE WHEN event_type IN ('charge','settle') THEN final_cost ELSE 0 END) AS lifetime_spent
                  FROM credit_ledger
                  GROUP BY account_id
                ) lifetime ON lifetime.account_id = a.id
                WHERE CAST(a.user_id AS TEXT) = :user_id
                ORDER BY a.updated_at DESC
                LIMIT 1
                """
            )
            result = session.execute(q, {"user_id": user_id}).fetchone()
            if result:
                return dict(result._mapping)
            return None
        except Exception:
            return None
        finally:
            session.close()

    return await asyncio.to_thread(_sync_query)


async def _require_current_user_dep(current_user=Depends(get_current_user) if get_current_user else None):
    if get_current_user is None:
        raise HTTPException(status_code=503, detail="Authentication system is unavailable")
    return current_user


@app.get("/api/v1/accounts/me/summary")
async def my_account_summary(current_user=Depends(_require_current_user_dep)):
    """Return account summary for the authenticated user."""
    user_id = getattr(current_user, "id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Unauthenticated")

    normalized_user_id = str(user_id)

    row = await _query_with_sqlalchemy_by_user_id(normalized_user_id)
    if row is not None:
        return row

    try:
        conn = await get_conn()
    except Exception:
        conn = None

    if conn:
        try:
            row = await conn.fetchrow(
                """
                SELECT a.id::text AS account_id, a.available_credits, a.reserved_credits,
                  COALESCE(lifetime.lifetime_earned,0) AS lifetime_earned,
                  COALESCE(lifetime.lifetime_spent,0) AS lifetime_spent
                FROM credit_accounts a
                LEFT JOIN (
                  SELECT account_id,
                    SUM(CASE WHEN event_type = 'grant' THEN final_cost ELSE 0 END) AS lifetime_earned,
                    SUM(CASE WHEN event_type IN ('charge','settle') THEN final_cost ELSE 0 END) AS lifetime_spent
                  FROM credit_ledger
                  GROUP BY account_id
                ) lifetime ON lifetime.account_id = a.id
                WHERE a.user_id::text = $1
                ORDER BY a.updated_at DESC
                LIMIT 1
                """,
                normalized_user_id,
            )
            if row:
                return dict(row)
            return _summary_zero(None)
        finally:
            try:
                await conn.close()
            except Exception:
                pass

    return _summary_zero(None)


@app.get("/api/v1/accounts/{account_id}/summary")
async def account_summary(account_id: str):
    """Return account summary by account id, with SQLAlchemy-first and asyncpg fallback."""
    # SQLAlchemy-first (production integration path)
    row = await _query_with_sqlalchemy_by_account_id(account_id)
    if row is not None:
        return row

    # asyncpg fallback (kept for tests and lightweight standalone usage)
    try:
        conn = await get_conn()
    except Exception:
        conn = None

    if conn:
        try:
            row = await conn.fetchrow(
                """
                SELECT a.id::text AS account_id, a.available_credits, a.reserved_credits,
                  COALESCE(lifetime.lifetime_earned,0) AS lifetime_earned,
                  COALESCE(lifetime.lifetime_spent,0) AS lifetime_spent
                FROM credit_accounts a
                LEFT JOIN (
                  SELECT account_id,
                    SUM(CASE WHEN event_type = 'grant' THEN final_cost ELSE 0 END) AS lifetime_earned,
                    SUM(CASE WHEN event_type IN ('charge','settle') THEN final_cost ELSE 0 END) AS lifetime_spent
                  FROM credit_ledger
                  GROUP BY account_id
                ) lifetime ON lifetime.account_id = a.id
                WHERE a.id::text = $1
                """,
                account_id,
            )
            if row:
                return dict(row)
            return _summary_zero(account_id)
        finally:
            try:
                await conn.close()
            except Exception:
                pass

    # Local dev fallback when DB is unavailable
    return {
        "account_id": account_id,
        "available_credits": 1000,
        "reserved_credits": 0,
        "lifetime_earned": 1000,
        "lifetime_spent": 0,
    }
