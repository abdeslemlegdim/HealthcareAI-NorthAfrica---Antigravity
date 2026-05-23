# Stripe Webhook Mapping — Recommended handlers and mapping to ledger

This document describes which Stripe events to handle and how to map them into subscription and credit flows. Use Stripe Billing + Metered usage if you intend to bill overages; otherwise use subscription-based refill grants.

Important events to subscribe to:
- `checkout.session.completed` — initial checkout finished, create local subscription record and grant trial/refill if applicable.
- `invoice.paid` — payment succeeded; ensure credits are refilled and subscription is active.
- `invoice.payment_failed` — start grace period and notify the user.
- `customer.subscription.created` — create subscription row and schedule refill.
- `customer.subscription.updated` — update local plan/entitlements if changed.
- `customer.subscription.deleted` — mark subscription canceled.
- `payment_method.attached` — update default payment method.

Design patterns
- Use idempotency: store `stripe_event_id` in a table to avoid double-processing.
- Verify signatures using `STRIPE_SIGNING_SECRET` on every webhook.
- Use webhooks to drive authoritative state (payment succeeded, canceled, etc.).

Example handler pseudocode (fast path):

POST /webhook/stripe
  raw_body = request.body
  sig_header = request.headers['stripe-signature']
  event = stripe.Webhook.construct_event(raw_body, sig_header, STRIPE_SIGNING_SECRET)

  if already_processed(event.id): return 200

  switch event.type:
    case 'checkout.session.completed':
      customer_id = event.data.object.customer
      subscription_id = event.data.object.subscription
      # link to local user and create subscription row
      create_local_subscription(customer_id, subscription_id, event.data.object)
      if event contains trial or immediate grant:
        grant_trial_credits(local_account_id, trial_amount)
      break

    case 'invoice.paid':
      subscription = event.data.object.subscription
      # refill credits on successful payment
      local_sub = find_local_subscription(subscription)
      if local_sub:
         refill_amount = local_sub.plan.monthly_credits
         grant_credits(local_sub.account_id, refill_amount, source='stripe_invoice')
      break

    case 'invoice.payment_failed':
      # set grace/past_due state, notify user via email
      mark_subscription_past_due(local_sub)
      notify_user_payment_failed(local_sub.user_id)
      break

    case 'customer.subscription.updated':
      # if plan changed, update plan_id and optionally prorate credits
      update_local_subscription(...)
      break

    case 'customer.subscription.deleted':
      cancel_local_subscription(...)
      break

  store_processed_event(event.id)
  return 200

How to grant credits safely on `invoice.paid`:
1. Begin DB transaction
2. Insert a `credit_ledger` row with event_type = 'grant' and final_cost = monthly_credits
3. Update `credit_accounts.available_credits` and `lifetime_earned`
4. Commit

Notes on metered usage with Stripe:
- If you use Stripe usage records, you can report usage for metered subscription items. This is useful for per-call billing for enterprise.
- For hybrid credit + subscription models, use Stripe for subscription payments and maintain internal credits for metering. Use Stripe usage only if you want per-call billing visible on Stripe invoices.

Retries and idempotency
- Stripe will retry webhooks; ensure handlers are idempotent.
- Persist event IDs and ignore duplicates.

Security
- Verify `stripe-signature`.
- Use a separate webhook endpoint for sensitive admin events.

Testing
- Use the Stripe CLI to send test events during development.
