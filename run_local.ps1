Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Debate Voting System v2.0" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Backend Setup
Write-Host "Setting up Backend..." -ForegroundColor Yellow
Set-Location backend

# Create venv if not exists
if (-not (Test-Path venv)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Gray
    python -m venv venv
}

# Install requirements
Write-Host "Installing backend dependencies..." -ForegroundColor Gray
.\venv\Scripts\python -m pip install -r requirements.txt

# Init DB
Write-Host "Initializing Database..." -ForegroundColor Gray
.\venv\Scripts\python init_db.py --data

# Start Backend
Write-Host "Starting Backend Server..." -ForegroundColor Green
$backendCmd = "cd /d `"$PWD\..`" & cd backend & venv\Scripts\activate & uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Start-Process cmd -ArgumentList "/k", "title Backend-Server &", $backendCmd

# 2. Frontend Setup
Write-Host "Setting up Frontend..." -ForegroundColor Yellow
Set-Location ../frontend

# Install node_modules if not exists
if (-not (Test-Path node_modules)) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Gray
    npm install
}

# Start Frontend
Write-Host "Starting Frontend Server..." -ForegroundColor Green
$frontendCmd = "cd /d `"$PWD\..`" & cd frontend & npm run dev"
Start-Process cmd -ArgumentList "/k", "title Frontend-Server &", $frontendCmd

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Yellow
Write-Host "  Frontend:    http://localhost:3000" -ForegroundColor White
Write-Host "  Backend API: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Login Pages:" -ForegroundColor Yellow
Write-Host "  Admin:       http://localhost:3000/admin/login" -ForegroundColor White
Write-Host "  Judge/Audience: http://localhost:3000/login" -ForegroundColor White
Write-Host "  Screen:      http://localhost:3000/screen" -ForegroundColor White
Write-Host ""
Write-Host "Default Account:" -ForegroundColor Yellow
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: 123456" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
