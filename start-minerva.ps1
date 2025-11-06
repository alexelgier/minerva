# Minerva Full Stack Startup Script
# This script starts all required services for the Minerva application

Write-Host "🚀 Starting Minerva Full Stack..." -ForegroundColor Green

# Function to start a process in a new window
function Start-Service {
    param(
        [string]$Name,
        [string]$Command,
        [string]$WorkingDir = $PWD,
        [string]$Arguments = ""
    )
    
    Write-Host "Starting $Name..." -ForegroundColor Yellow
    if ($Arguments) {
        Start-Process -FilePath $Command -ArgumentList $Arguments -WorkingDirectory $WorkingDir -WindowStyle Normal
    } else {
        Start-Process -FilePath $Command -WorkingDirectory $WorkingDir -WindowStyle Normal
    }
}

# Start Temporal Server
Start-Service -Name "Temporal Server" -Command "temporal" -Arguments "server start-dev"

# Wait a moment for Temporal to start
Start-Sleep -Seconds 3

# Start Ollama Server  
Start-Service -Name "Ollama Server" -Command "ollama" -Arguments "serve"

# Wait a moment for Ollama to start
Start-Sleep -Seconds 3

# Start Backend API
Start-Service -Name "Backend API" -Command "uvicorn" -Arguments "src.minerva_backend.api.main:backend_app --host 0.0.0.0 --port 8000 --reload --log-level debug" -WorkingDir "backend"

# Start Temporal Worker
Start-Service -Name "Temporal Worker" -Command "python" -Arguments "src/minerva_backend/processing/temporal_orchestrator.py" -WorkingDir "backend"

# Start Frontend
Start-Service -Name "Frontend Dev Server" -Command "npm" -Arguments "run dev" -WorkingDir "frontend"

# Open Minerva log in VS Code
Write-Host "Opening Minerva log..." -ForegroundColor Yellow
Start-Process -FilePath "code" -ArgumentList "backend/logs/minerva.log" -WindowStyle Normal

Write-Host "✅ All Minerva services started!" -ForegroundColor Green
Write-Host "Services running:" -ForegroundColor Cyan
Write-Host "  • Temporal Server: http://localhost:7233" -ForegroundColor White
Write-Host "  • Ollama Server: http://localhost:11434" -ForegroundColor White  
Write-Host "  • Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  • Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  • Minerva Log: backend/logs/minerva.log" -ForegroundColor White
