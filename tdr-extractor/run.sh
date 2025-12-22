#!/bin/bash
# Script para levantar el servidor TDR Extractor

# Activar entorno virtual de Poetry si existe
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Verificar que Ollama esté corriendo (si se usa LLM local)
if grep -q "USE_LOCAL_LLM=true" .env 2>/dev/null; then
    echo "🔍 Verificando Ollama..."
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "⚠️  Ollama no está corriendo. Inicia Ollama primero:"
        echo "   ollama serve"
        echo ""
        echo "   Y asegúrate de tener el modelo:"
        echo "   ollama pull deepseek-r1:8b"
        echo ""
    else
        echo "✅ Ollama está corriendo"
    fi
fi

# Crear directorio de uploads si no existe
mkdir -p uploads

echo "🚀 Iniciando TDR Extractor API..."
echo "📚 Documentación: http://localhost:8000/docs"
echo ""

# Iniciar servidor con uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

