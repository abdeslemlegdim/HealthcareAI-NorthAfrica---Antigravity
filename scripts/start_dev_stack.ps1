param(
    [int]$BackendPort = 8001,
    [int]$FrontendPort = 5175,
    [string]$BackendHost = "127.0.0.1",
    [switch]$UseTrainedApis,
    [string]$EmbeddingApiEndpoint = "",
    [string]$RerankApiEndpoint = "",
    [string]$LlmApiEndpoint = "",
    [string]$ImagingApiEndpoint = "",
    [string]$ImagingExplainApiEndpoint = "",
    [string]$HfToken = "",
    [string]$OpenAiBaseUrl = "",
    [string]$OpenAiApiKey = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Path $PSScriptRoot -Parent
$frontendRoot = Join-Path $projectRoot "frontend-react"

function Write-Info($msg) {
    Write-Host "[INFO] $msg" -ForegroundColor Cyan
}

function Write-Ok($msg) {
    Write-Host "[OK]   $msg" -ForegroundColor Green
}

function Write-WarnMsg($msg) {
    Write-Host "[WARN] $msg" -ForegroundColor Yellow
}

function Test-PortOpen {
    param(
        [string]$HostName,
        [int]$Port,
        [int]$TimeoutMs = 1200
    )

    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $iar = $client.BeginConnect($HostName, $Port, $null, $null)
        $success = $iar.AsyncWaitHandle.WaitOne($TimeoutMs, $false)
        if (-not $success) {
            return $false
        }
        $client.EndConnect($iar)
        return $true
    } catch {
        return $false
    } finally {
        $client.Dispose()
    }
}

function Test-HealthEndpoint {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 2
    )

    try {
        $handler = New-Object System.Net.Http.HttpClientHandler
        $client = New-Object System.Net.Http.HttpClient($handler)
        $client.Timeout = [TimeSpan]::FromSeconds($TimeoutSeconds)
        $response = $client.GetAsync($Url).GetAwaiter().GetResult()
        $status = [int]$response.StatusCode
        $client.Dispose()
        $handler.Dispose()
        return ($status -ge 200 -and $status -lt 300)
    } catch {
        return $false
    }
}

function Start-StackProcess {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string]$Command
    )

    Write-Info "Starting $Name"
    if ($DryRun) {
        Write-Host "        cd $WorkingDirectory; $Command" -ForegroundColor Gray
        return
    }

    $escapedWd = $WorkingDirectory.Replace("'", "''")
    $full = "Set-Location '$escapedWd'; $Command"
    Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", $full | Out-Null
}

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "Healthcare AI - Dev Stack Launcher" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

if (-not (Test-Path $projectRoot)) {
    throw "Project root not found: $projectRoot"
}
if (-not (Test-Path $frontendRoot)) {
    throw "Frontend folder not found: $frontendRoot"
}

$backendHealthUrl = "http://$BackendHost`:$BackendPort/health"
$backendBaseUrl = "http://$BackendHost`:$BackendPort"
$frontendUrl = "http://localhost:$FrontendPort"

$backendHealthy = Test-HealthEndpoint -Url $backendHealthUrl
if ($backendHealthy) {
    Write-Ok "Backend already healthy at $backendHealthUrl"
} elseif (Test-PortOpen -HostName $BackendHost -Port $BackendPort) {
    Write-WarnMsg "Port $BackendPort is open but /health failed. Reusing existing listener."
} else {
    if ($UseTrainedApis) {
        $backendCmd = "$env:LLM_ENABLED='true'; $env:USE_LLM_API='true'; $env:USE_EMBEDDING_API='true'; $env:USE_RERANK_API='true'; $env:USE_IMAGING_API='true'; python -m uvicorn main:app --host $BackendHost --port $BackendPort"
        if ($EmbeddingApiEndpoint) { $backendCmd = "$env:EMBEDDING_API_ENDPOINT='$EmbeddingApiEndpoint'; " + $backendCmd }
        if ($RerankApiEndpoint) { $backendCmd = "$env:RERANK_API_ENDPOINT='$RerankApiEndpoint'; " + $backendCmd }
        if ($LlmApiEndpoint) { $backendCmd = "$env:LLM_API_ENDPOINT='$LlmApiEndpoint'; " + $backendCmd }
        if ($ImagingApiEndpoint) { $backendCmd = "$env:IMAGING_API_ENDPOINT='$ImagingApiEndpoint'; " + $backendCmd }
        if ($ImagingExplainApiEndpoint) { $backendCmd = "$env:IMAGING_EXPLAIN_API_ENDPOINT='$ImagingExplainApiEndpoint'; " + $backendCmd }
        if ($HfToken) { $backendCmd = "$env:HUGGINGFACE_TOKEN='$HfToken'; " + $backendCmd }
        if ($OpenAiBaseUrl) { $backendCmd = "$env:OPENAI_BASE_URL='$OpenAiBaseUrl'; " + $backendCmd }
        if ($OpenAiApiKey) { $backendCmd = "$env:OPENAI_API_KEY='$OpenAiApiKey'; " + $backendCmd }
    } else {
        $backendCmd = "$env:LLM_ENABLED='false'; $env:USE_LLM_API='false'; $env:USE_EMBEDDING_API='false'; $env:USE_RERANK_API='false'; $env:USE_IMAGING_API='false'; python -m uvicorn main:app --host $BackendHost --port $BackendPort"
    }

    Start-StackProcess -Name "backend" -WorkingDirectory $projectRoot -Command $backendCmd
}

if (Test-PortOpen -HostName "127.0.0.1" -Port $FrontendPort) {
    Write-WarnMsg "Frontend port $FrontendPort already in use."
} else {
    $frontendCmd = "npm run dev -- --port $FrontendPort"
    Start-StackProcess -Name "frontend" -WorkingDirectory $frontendRoot -Command $frontendCmd
}

Write-Host ""
Write-Host "URLs" -ForegroundColor White
Write-Host "  Backend:  $backendBaseUrl" -ForegroundColor Gray
Write-Host "  Health:   $backendHealthUrl" -ForegroundColor Gray
Write-Host "  Frontend: $frontendUrl" -ForegroundColor Gray
Write-Host "  Mode:     $([string]::Copy($(if ($UseTrainedApis) { 'trained APIs' } else { 'local/demo fallback' })))" -ForegroundColor Gray
Write-Host ""

if ($DryRun) {
    Write-Ok "Dry run completed. No processes were started."
} else {
    Write-Ok "Launch commands dispatched in new PowerShell windows."
    Write-Host "Use the Chat page button 'Check API Health' to verify connectivity." -ForegroundColor Gray
}
