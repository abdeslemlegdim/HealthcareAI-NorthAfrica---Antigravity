-- v1_schema.sql
-- PostgreSQL DDL for subscriptions, credit ledger, usage metering, and rate limiting
-- Designed for Healthcare AI platform credit system (credits = internal unit)

-- NOTE: run this in a Postgres database. Adapt types and naming to your conventions.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Users
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT,
  full_name TEXT,
  locale TEXT DEFAULT 'en',
  role TEXT DEFAULT 'user',
  status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Organizations
CREATE TABLE IF NOT EXISTS organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE,
  plan_id UUID,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations (slug);

-- Organization members
CREATE TABLE IF NOT EXISTS organization_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  member_role TEXT DEFAULT 'member',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Plans
CREATE TABLE IF NOT EXISTS plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  tier TEXT NOT NULL,
  monthly_price_cents BIGINT DEFAULT 0,
  annual_price_cents BIGINT DEFAULT 0,
  monthly_credits BIGINT DEFAULT 0,
  daily_chat_limit INT DEFAULT 0,
  daily_imaging_limit INT DEFAULT 0,
  daily_vitals_limit INT DEFAULT 0,
  max_upload_mb INT DEFAULT 10,
  max_history_days INT DEFAULT 30,
  priority_level INT DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Entitlements (feature gates)
CREATE TABLE IF NOT EXISTS entitlements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id UUID REFERENCES plans(id) ON DELETE CASCADE,
  feature_key TEXT NOT NULL,
  allowed BOOLEAN DEFAULT TRUE,
  limit_value BIGINT,
  limit_period TEXT,
  priority_level INT DEFAULT 0,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_entitlements_plan_feature ON entitlements(plan_id, feature_key);

-- Subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
  plan_id UUID REFERENCES plans(id),
  provider TEXT,
  provider_customer_id TEXT,
  provider_subscription_id TEXT,
  billing_cycle TEXT,
  status TEXT,
  current_period_start TIMESTAMPTZ,
  current_period_end TIMESTAMPTZ,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  trial_ends_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);

-- Credit accounts (denormalized for fast checks)
CREATE TABLE IF NOT EXISTS credit_accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
  plan_id UUID REFERENCES plans(id),
  available_credits BIGINT DEFAULT 0,
  reserved_credits BIGINT DEFAULT 0,
  lifetime_earned BIGINT DEFAULT 0,
  lifetime_spent BIGINT DEFAULT 0,
  reset_at TIMESTAMPTZ,
  rollover_credits BIGINT DEFAULT 0,
  status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_credit_accounts_user_org ON credit_accounts(user_id, organization_id);

-- Credit ledger (source of truth)
CREATE TABLE IF NOT EXISTS credit_ledger (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID REFERENCES credit_accounts(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
  event_type TEXT NOT NULL,
  feature_key TEXT,
  request_id TEXT,
  estimated_cost BIGINT DEFAULT 0,
  final_cost BIGINT DEFAULT 0,
  status TEXT DEFAULT 'pending', -- pending, reserved, settled, reversed, refunded
  source TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_credit_ledger_account_request ON credit_ledger(account_id, request_id);
CREATE INDEX IF NOT EXISTS idx_credit_ledger_user ON credit_ledger(user_id);

-- Usage events for observability
CREATE TABLE IF NOT EXISTS usage_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
  request_id TEXT,
  feature_key TEXT,
  action_type TEXT,
  model_name TEXT,
  input_size_bytes BIGINT,
  output_size_bytes BIGINT,
  duration_ms INT,
  credits_estimated BIGINT DEFAULT 0,
  credits_charged BIGINT DEFAULT 0,
  status TEXT,
  ip_hash TEXT,
  device_hash TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_usage_events_request ON usage_events(request_id);

-- Rate limit events
CREATE TABLE IF NOT EXISTS rate_limit_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
  action_type TEXT,
  window_start TIMESTAMPTZ,
  window_end TIMESTAMPTZ,
  count INT DEFAULT 0,
  blocked_count INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Invoices
CREATE TABLE IF NOT EXISTS invoices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
  provider_invoice_id TEXT,
  total_amount_cents BIGINT,
  currency TEXT,
  status TEXT,
  period_start TIMESTAMPTZ,
  period_end TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Payment methods
CREATE TABLE IF NOT EXISTS payment_methods (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
  provider TEXT,
  provider_payment_method_id TEXT,
  brand TEXT,
  last4 TEXT,
  exp_month INT,
  exp_year INT,
  is_default BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
  action TEXT,
  target_type TEXT,
  target_id TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Feature usage rollups
CREATE TABLE IF NOT EXISTS feature_usage_rollups (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID REFERENCES credit_accounts(id) ON DELETE CASCADE,
  feature_key TEXT,
  period_start TIMESTAMPTZ,
  period_end TIMESTAMPTZ,
  usage_count BIGINT DEFAULT 0,
  credits_spent BIGINT DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Helper: atomic reserve and settle functions
-- reserve_credits: creates a ledger row with status 'reserved' and adjusts account balances
-- settle_credits: finalizes ledger for request_id and charges final_cost, releasing any extra reserved

-- Function: reserve_credits(account_id, user_id, org_id, request_id, feature_key, estimated_cost, metadata_json)
CREATE OR REPLACE FUNCTION reserve_credits(
  p_account_id UUID,
  p_user_id UUID,
  p_org_id UUID,
  p_request_id TEXT,
  p_feature_key TEXT,
  p_estimated_cost BIGINT,
  p_source TEXT DEFAULT 'api',
  p_metadata JSONB DEFAULT '{}'::jsonb
) RETURNS TABLE(ledger_id UUID, reserved BIGINT) AS $$
DECLARE
  acct RECORD;
  ledger_rec UUID;
BEGIN
  -- Lock the account row
  SELECT * INTO acct FROM credit_accounts WHERE id = p_account_id FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Account not found %', p_account_id;
  END IF;
  IF acct.available_credits < p_estimated_cost THEN
    RETURN QUERY SELECT NULL::UUID AS ledger_id, 0::BIGINT AS reserved;
    RETURN;
  END IF;
  -- insert ledger row
  INSERT INTO credit_ledger(account_id, user_id, organization_id, event_type, feature_key, request_id, estimated_cost, final_cost, status, source, metadata)
  VALUES (p_account_id, p_user_id, p_org_id, 'reserve', p_feature_key, p_request_id, p_estimated_cost, 0, 'reserved', p_source, p_metadata)
  RETURNING id INTO ledger_rec;

  -- update account balances
  UPDATE credit_accounts
  SET available_credits = available_credits - p_estimated_cost,
      reserved_credits = reserved_credits + p_estimated_cost,
      updated_at = now()
  WHERE id = p_account_id;

  RETURN QUERY SELECT ledger_rec, p_estimated_cost;
END;
$$ LANGUAGE plpgsql;

-- Function: settle_credits(account_id, request_id, final_cost)
CREATE OR REPLACE FUNCTION settle_credits(
  p_account_id UUID,
  p_request_id TEXT,
  p_final_cost BIGINT
) RETURNS TABLE(ledger_id UUID, charged BIGINT, refunded BIGINT) AS $$
DECLARE
  rec RECORD;
  delta BIGINT;
BEGIN
  -- Lock the ledger row for this request
  SELECT * INTO rec FROM credit_ledger WHERE account_id = p_account_id AND request_id = p_request_id FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Ledger entry not found for account % request %', p_account_id, p_request_id;
  END IF;
  IF rec.status != 'reserved' THEN
    RAISE EXCEPTION 'Ledger entry not in reserved state: %', rec.status;
  END IF;

  -- compute delta between reserved(estimated_cost) and final
  delta := rec.estimated_cost - p_final_cost; -- positive if we over-reserved

  -- update ledger
  UPDATE credit_ledger
  SET final_cost = p_final_cost,
      status = 'settled',
      metadata = metadata || jsonb_build_object('settled_at', now())
  WHERE id = rec.id;

  -- update account balances: reduce reserved_credits by estimated, then substract final from reserved or available as needed
  UPDATE credit_accounts
  SET reserved_credits = reserved_credits - rec.estimated_cost,
      lifetime_spent = lifetime_spent + p_final_cost,
      updated_at = now()
  WHERE id = p_account_id;

  IF delta > 0 THEN
    -- return delta back to available_credits
    UPDATE credit_accounts
    SET available_credits = available_credits + delta,
        updated_at = now()
    WHERE id = p_account_id;
  ELSIF delta < 0 THEN
    -- final cost exceeded estimate, need to deduct difference from available_credits
    UPDATE credit_accounts
    SET available_credits = available_credits + delta, -- delta negative
        updated_at = now()
    WHERE id = p_account_id;
  END IF;

  RETURN QUERY SELECT rec.id, p_final_cost, GREATEST(delta, 0);
END;
$$ LANGUAGE plpgsql;

-- Function: reverse_reservation(account_id, request_id)
CREATE OR REPLACE FUNCTION reverse_reservation(
  p_account_id UUID,
  p_request_id TEXT,
  p_reason TEXT DEFAULT NULL
) RETURNS TABLE(ledger_id UUID, reversed BIGINT) AS $$
DECLARE
  rec RECORD;
BEGIN
  SELECT * INTO rec FROM credit_ledger WHERE account_id = p_account_id AND request_id = p_request_id FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Ledger entry not found for account % request %', p_account_id, p_request_id;
  END IF;
  IF rec.status NOT IN ('reserved','pending') THEN
    RETURN QUERY SELECT rec.id, 0;
    RETURN;
  END IF;

  UPDATE credit_ledger
  SET status = 'reversed',
      metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object('reversed_at', now(), 'reason', p_reason)
  WHERE id = rec.id;

  -- restore reserved credits to available
  UPDATE credit_accounts
  SET reserved_credits = reserved_credits - rec.estimated_cost,
      available_credits = available_credits + rec.estimated_cost,
      updated_at = now()
  WHERE id = p_account_id;

  RETURN QUERY SELECT rec.id, rec.estimated_cost;
END;
$$ LANGUAGE plpgsql;

-- Helpful view for current balances
CREATE OR REPLACE VIEW account_balances AS
SELECT id as account_id, user_id, organization_id, available_credits, reserved_credits, lifetime_earned, lifetime_spent, (available_credits + reserved_credits) as total_allocated
FROM credit_accounts;

-- Recommended indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_credit_accounts_user ON credit_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_ledger_status ON credit_ledger(status);
CREATE INDEX IF NOT EXISTS idx_usage_events_user_feature ON usage_events(user_id, feature_key);

-- End of schema
