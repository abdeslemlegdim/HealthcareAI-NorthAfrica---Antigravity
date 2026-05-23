# Migration helper notes

Apply the schema using the supplied PowerShell script on Windows or use `psql` directly.

PowerShell (Windows):

```powershell
$env:DATABASE_URL = 'postgresql://user:pass@host:5432/dbname'
cd migrations
.\apply_schema.ps1
```

psql (Linux/macOS/WSL):

```bash
psql $DATABASE_URL -f database/v1_schema.sql
```

Verify that the `credit_accounts`, `credit_ledger`, and helper functions exist after running.
