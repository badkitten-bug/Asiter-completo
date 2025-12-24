FROM python:3.11-slim

WORKDIR /app

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
