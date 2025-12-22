# Script PowerShell para ejecutar el backend

Write-Host "🚀 TDR Generator Backend" -ForegroundColor Cyan
Write-Host ""

# Verificar ChromaDB
$chromaDir = ".\chroma_db"
if (-not (Test-Path $chromaDir)) {
    Write-Host "⚠️ Base de datos vacía. Ejecuta primero:" -ForegroundColor Yellow
    Write-Host "   python scripts/load_tdrs.py" -ForegroundColor White
    Write-Host ""
}

Write-Host "📚 Documentación: http://localhost:8001/docs" -ForegroundColor Green
Write-Host ""

# Iniciar servidor
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

