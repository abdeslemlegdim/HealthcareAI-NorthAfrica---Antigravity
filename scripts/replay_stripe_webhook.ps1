<#
Replay a Stripe webhook locally using the Stripe CLI.

Usage:
  .\scripts\replay_stripe_webhook.ps1 -EventId evt_123 -ForwardTo "/api/v1/subscriptions/stripe/webhook"

Requires: Stripe CLI installed and authenticated (`stripe login`).
#>

param(
  [string]$EventId,
  [string]$ForwardTo = "/api/v1/subscriptions/stripe/webhook"
)

if (-not (Get-Command stripe -ErrorAction SilentlyContinue)) {
  Write-Error "Stripe CLI not found. Install from https://stripe.com/docs/stripe-cli"
  exit 1
}

if ($EventId) {
  Write-Host "Replaying event $EventId to localhost:8001$ForwardTo"
  stripe events replay $EventId --forward-to "http://localhost:8001$ForwardTo"
} else {
  Write-Host "Listening and forwarding all events to localhost:8001$ForwardTo"
  stripe listen --forward-to "http://localhost:8001$ForwardTo"
}
