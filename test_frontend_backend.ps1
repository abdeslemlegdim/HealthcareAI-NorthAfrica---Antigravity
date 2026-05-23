# ========================================
# MaghrebCare AI - System Test Script
# ========================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "MaghrebCare AI - System Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Test 1: Backend Health
Write-Host "[1/4] Testing Backend Health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8001/health" -Method GET
    Write-Host "   ✓ Backend Status: $($health.status)" -ForegroundColor Green
    Write-Host "   ✓ Services:" -ForegroundColor Green
    $health.services.PSObject.Properties | ForEach-Object {
        Write-Host "      - $($_.Name): $($_.Value)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ✗ Backend health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: RAG Query Endpoint
Write-Host "`n[2/4] Testing RAG Query Endpoint..." -ForegroundColor Yellow
try {
    $body = @{
        question = "What are the symptoms of COVID-19?"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Method POST -Uri "http://localhost:8001/api/v1/rag/query" -ContentType "application/json" -Body $body
    
    Write-Host "   ✓ Question: $($response.question)" -ForegroundColor Green
    Write-Host "   ✓ Language: $($response.language)" -ForegroundColor Green
    Write-Host "   ✓ Confidence: $($response.confidence)" -ForegroundColor Green
    Write-Host "   ✓ Sources Retrieved: $($response.sources.Count)" -ForegroundColor Green
    Write-Host "   ✓ Answer Preview: $($response.answer.Substring(0, [Math]::Min(100, $response.answer.Length)))..." -ForegroundColor Gray
} catch {
    Write-Host "   ✗ RAG query failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Frontend Accessibility
Write-Host "`n[3/4] Testing Frontend Accessibility..." -ForegroundColor Yellow
try {
    $frontend = Invoke-WebRequest -Uri "http://localhost:8080" -Method GET -UseBasicParsing
    Write-Host "   ✓ Frontend Status: $($frontend.StatusCode) $($frontend.StatusDescription)" -ForegroundColor Green
    Write-Host "   ✓ Content Length: $($frontend.Content.Length) bytes" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Frontend not accessible: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: API Documentation
Write-Host "`n[4/4] Testing API Documentation..." -ForegroundColor Yellow
try {
    $docs = Invoke-WebRequest -Uri "http://localhost:8001/docs" -Method GET -UseBasicParsing
    Write-Host "   ✓ API Docs Available: http://localhost:8001/docs" -ForegroundColor Green
} catch {
    Write-Host "   ✗ API docs not accessible: $($_.Exception.Message)" -ForegroundColor Red
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nURLs:" -ForegroundColor White
Write-Host "   • Frontend UI:       http://localhost:8080" -ForegroundColor White
Write-Host "   • Backend API:       http://localhost:8001" -ForegroundColor White
Write-Host "   • API Docs:          http://localhost:8001/docs" -ForegroundColor White
Write-Host "   • ReDoc:             http://localhost:8001/redoc" -ForegroundColor White

Write-Host "`nQuick Tests:" -ForegroundColor White
Write-Host "   1. Open http://localhost:8080 in your browser" -ForegroundColor Gray
Write-Host "   2. Try the Chat Assistant tab with a medical question" -ForegroundColor Gray
Write-Host "   3. View System Status tab to see backend health" -ForegroundColor Gray

Write-Host "`n========================================`n" -ForegroundColor Cyan
