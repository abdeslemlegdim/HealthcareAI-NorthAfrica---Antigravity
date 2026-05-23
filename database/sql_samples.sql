-- sql_samples.sql
-- Useful SQL snippets: reconciliation, refunds, monthly refill script

-- 1) Reconciliation: find accounts where ledger sums don't match account balances
-- Sum all settled + grant - refund for an account and compare to lifetime_spent/lifetime_earned

-- Sum credits granted and spent in ledger for an account
SELECT
  a.id as account_id,
  SUM(CASE WHEN l.event_type IN ('grant') THEN l.final_cost ELSE 0 END) as total_grants,
  SUM(CASE WHEN l.event_type IN ('settle','charge') THEN l.final_cost ELSE 0 END) as total_charged,
  a.available_credits,
  a.reserved_credits,
  a.lifetime_earned,
  a.lifetime_spent
FROM credit_accounts a
LEFT JOIN credit_ledger l ON l.account_id = a.id
GROUP BY a.id, a.available_credits, a.reserved_credits, a.lifetime_earned, a.lifetime_spent
HAVING (COALESCE(SUM(CASE WHEN l.event_type IN ('grant') THEN l.final_cost ELSE 0 END),0) - COALESCE(SUM(CASE WHEN l.event_type IN ('settle','charge') THEN l.final_cost ELSE 0 END),0)) IS DISTINCT FROM (a.available_credits + a.reserved_credits);

-- 2) Refund example: create a refund ledger entry and update balances atomically
BEGIN;
  -- find the settled ledger entry
  SELECT id, account_id, final_cost INTO TEMP TABLE tmp_ledger FROM credit_ledger WHERE id = '<<LEDGER_ID>>' FOR UPDATE;
  -- insert refund entry
  INSERT INTO credit_ledger(account_id, user_id, organization_id, event_type, feature_key, request_id, estimated_cost, final_cost, status, source, metadata)
    SELECT account_id, user_id, organization_id, 'refund', feature_key, request_id, 0, -final_cost, 'refunded', 'admin', jsonb_build_object('refund_of', id, 'note', 'manual refund')
    FROM credit_ledger WHERE id = '<<LEDGER_ID>>';
  -- add credits back
  UPDATE credit_accounts SET available_credits = available_credits + (SELECT -final_cost FROM tmp_ledger), updated_at = now() WHERE id = (SELECT account_id FROM tmp_ledger);
COMMIT;

-- 3) Monthly refill (example in SQL using plans.monthly_credits)
-- This should be executed by a scheduler keyed to billing cycle; here is a simple per-plan refill
BEGIN;
  INSERT INTO credit_ledger(account_id, user_id, organization_id, event_type, final_cost, status, source, metadata)
  SELECT ca.id, ca.user_id, ca.organization_id, 'grant', p.monthly_credits, 'settled', 'monthly_refill', jsonb_build_object('plan', p.code)
  FROM credit_accounts ca
  JOIN plans p ON p.id = ca.plan_id
  WHERE p.monthly_credits > 0;

  UPDATE credit_accounts ca
  SET available_credits = available_credits + p.monthly_credits,
      lifetime_earned = lifetime_earned + p.monthly_credits,
      reset_at = now() + interval '30 days',
      updated_at = now()
  FROM plans p
  WHERE ca.plan_id = p.id AND p.monthly_credits > 0;
COMMIT;

-- 4) Find recent overages: accounts that went negative after final settle (should be rare)
SELECT * FROM credit_accounts WHERE available_credits < 0 OR reserved_credits < 0;

-- 5) Quick stats: credits used per feature this month
SELECT feature_key, SUM(credits_charged) as credits_spent
FROM usage_events
WHERE created_at >= date_trunc('month', now())
GROUP BY feature_key
ORDER BY credits_spent DESC;
