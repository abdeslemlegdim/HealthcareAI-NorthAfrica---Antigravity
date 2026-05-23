param(
  [string]$DatabaseUrl = $env:DATABASE_URL,
  [string]$SchemaFile = "$PSScriptRoot\..\database\v1_schema.sql"
)

if (-not $DatabaseUrl) {
  Write-Error "DATABASE_URL environment variable is required (postgres://user:pass@host:port/db)"
  exit 1
}

Write-Host "Applying schema from $SchemaFile to $DatabaseUrl"

# Uses psql - ensure it's available in PATH
$psql = "psql"

$cmd = "$psql $DatabaseUrl -f `"$SchemaFile`""
Write-Host $cmd
Invoke-Expression $cmd