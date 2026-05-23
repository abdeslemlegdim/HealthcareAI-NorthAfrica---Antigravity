<#
Set STRIPE_SIGNING_SECRET for current PowerShell session and restart backend.

Usage:
  .\scripts\set_stripe_signing_secret.ps1 -Secret "whsec_xxx"

This sets the env var for the current session and restarts the backend process
that listens on port 8001 (development server used throughout this project).
#>

param(
  [Parameter(Mandatory=$true)]
  [string]$Secret
)

Write-Host "Setting STRIPE_SIGNING_SECRET in this session..."
$env:STRIPE_SIGNING_SECRET = $Secret
Write-Host "STRIPE_SIGNING_SECRET set (session only)."

Write-Host "Restarting backend on port 8001..."
$backendPid = (Get-NetTCPConnection -LocalPort 8001 -State Listen | Select-Object -First 1 -ExpandProperty OwningProcess) ; if ($backendPid) { Stop-Process -Id $backendPid -Force; Write-Host "Stopped existing backend pid $backendPid" } ; Start-Sleep -Milliseconds 300
cd "$(Split-Path -Path $PSScriptRoot -Parent)"
# Try to locate project venv python; fallback to 'python' on PATH
$venvPython = Join-Path -Path (Get-Location) -ChildPath "venv\Scripts\python.exe"
if (Test-Path $venvPython) { $python = $venvPython } else { $python = "python" }
Start-Process -NoNewWindow -FilePath $python -ArgumentList 'main.py'
Write-Host "Backend restart command issued. Check logs for successful startup."
