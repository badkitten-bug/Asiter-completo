# Script PowerShell para levantar el servidor TDR Extractor

Write-Host "🚀 TDR Extractor API" -ForegroundColor Cyan
Write-Host ""

# Verificar que Ollama esté corriendo
$envContent = Get-Content .env -ErrorAction SilentlyContinue
if ($envContent -match "USE_LOCAL_LLM=true") {
    Write-Host "🔍 Verificando Ollama..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✅ Ollama está corriendo" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Ollama no está corriendo. Inicia Ollama primero:" -ForegroundColor Red
        Write-Host "   ollama serve" -ForegroundColor White
        Write-Host ""
        Write-Host "   Y asegúrate de tener el modelo:" -ForegroundColor White
        Write-Host "   ollama pull deepseek-r1:8b" -ForegroundColor White
        Write-Host ""
    }
}

# Crear directorio de uploads si no existe
if (-not (Test-Path "uploads")) {
    New-Item -ItemType Directory -Path "uploads" | Out-Null
}

Write-Host "📚 Documentación: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Iniciar servidor con uvicorn
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

