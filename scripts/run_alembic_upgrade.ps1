<#
Run Alembic upgrade head using the project's virtualenv python if present.

Usage:
  .\scripts\run_alembic_upgrade.ps1

This will use venv\Scripts\python.exe if it exists; otherwise it will use `python` on PATH.
#>

Write-Host "Running Alembic upgrade head..."
cd "$(Split-Path -Path $PSScriptRoot -Parent)"
$venvPython = Join-Path -Path (Get-Location) -ChildPath "venv\Scripts\python.exe"
if (Test-Path $venvPython) { $python = $venvPython } else { $python = "python" }

Write-Host "Using python: $python"
& $python -m alembic upgrade head

if ($LASTEXITCODE -eq 0) { Write-Host "Alembic upgrade completed successfully." } else { Write-Error "Alembic upgrade failed with exit code $LASTEXITCODE" }
