#!/usr/bin/env pwsh
# Employee Assistant Admin UI - Build and Deploy Script
# Aisin Purchase Order Design Update

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Aisin PO Design Update - Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if npm is available
Write-Host "[1/5] Checking environment..." -ForegroundColor Yellow
try {
    $npmVersion = npm --version 2>$null
    Write-Host "✓ npm found (version $npmVersion)" -ForegroundColor Green
} catch {
    Write-Host "✗ npm not found. Please install Node.js" -ForegroundColor Red
    exit 1
}

# Navigate to admin-ui directory
Write-Host ""
Write-Host "[2/5] Navigating to admin-ui directory..." -ForegroundColor Yellow
if (-not (Test-Path "admin-ui")) {
    Write-Host "✗ admin-ui directory not found" -ForegroundColor Red
    exit 1
}

Set-Location admin-ui
Write-Host "✓ Changed to admin-ui directory" -ForegroundColor Green

# Build the frontend
Write-Host ""
Write-Host "[3/5] Building React application..." -ForegroundColor Yellow
Write-Host "    This may take 30-60 seconds..." -ForegroundColor Gray

try {
    $buildOutput = npm run build 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Build completed successfully" -ForegroundColor Green
    } else {
        Write-Host "✗ Build failed" -ForegroundColor Red
        Write-Host $buildOutput -ForegroundColor Red
        Set-Location ..
        exit 1
    }
} catch {
    Write-Host "✗ Build error: $_" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# Navigate back to root
Set-Location ..

# Check if dist folder exists
Write-Host ""
Write-Host "[4/5] Verifying build output..." -ForegroundColor Yellow
if (-not (Test-Path "admin-ui\dist")) {
    Write-Host "✗ Build output (dist folder) not found" -ForegroundColor Red
    exit 1
}

$distFiles = Get-ChildItem -Path "admin-ui\dist" -Recurse | Measure-Object
Write-Host "✓ Found $($distFiles.Count) files in dist folder" -ForegroundColor Green

# Copy to static directory
Write-Host ""
Write-Host "[5/5] Deploying to api/static..." -ForegroundColor Yellow

if (-not (Test-Path "api\static")) {
    Write-Host "! Creating api/static directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "api\static" -Force | Out-Null
}

try {
    Copy-Item -Path "admin-ui\dist\*" -Destination "api\static\" -Recurse -Force
    Write-Host "✓ Files copied to api/static" -ForegroundColor Green
} catch {
    Write-Host "✗ Copy failed: $_" -ForegroundColor Red
    exit 1
}

# Verify deployment
$staticFiles = Get-ChildItem -Path "api\static" -Recurse | Measure-Object
Write-Host "✓ Deployment verified ($($staticFiles.Count) files in api/static)" -ForegroundColor Green

# Success message
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  ✓ Deployment Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Restart your API server" -ForegroundColor White
Write-Host "  2. Clear your browser cache (Ctrl+Shift+R)" -ForegroundColor White
Write-Host "  3. Open the admin UI in your browser" -ForegroundColor White
Write-Host ""
Write-Host "Expected changes:" -ForegroundColor Yellow
Write-Host "  • Navy blue (#001A71) primary color" -ForegroundColor White
Write-Host "  • Light blue-grey (#EDF3FF) page background" -ForegroundColor White
Write-Host "  • Large rounded corners (22-28px)" -ForegroundColor White
Write-Host "  • Enhanced card shadows" -ForegroundColor White
Write-Host "  • 48px form input height" -ForegroundColor White
Write-Host "  • Button hover lift effects" -ForegroundColor White
Write-Host "  • Refined table styling" -ForegroundColor White
Write-Host ""
Write-Host "See AISIN_PO_DESIGN_UPDATE.md for details" -ForegroundColor Gray
Write-Host ""
