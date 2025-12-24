FROM python:3.11-slim

WORKDIR /app

# Deshabilitar optimizaciones de NumPy para CPUs sin AVX2/SSE
ENV NPY_DISABLE_CPU_FEATURES="AVX2 AVX512F AVX512CD AVX512_SKX"
ENV OPENBLAS_CORETYPE=ARMV8

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (para cache de Docker)
COPY requirements.txt .

# Instalar NumPy 1.x PRIMERO (antes de chromadb) para CPUs sin AVX2
RUN pip install --no-cache-dir "numpy<2.0.0"

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Crear directorio para ChromaDB
RUN mkdir -p /app/chroma_db

# Puerto
EXPOSE 8001

# Comando
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
