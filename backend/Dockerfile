FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema para compilar NumPy
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    libopenblas-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (para cache de Docker)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# FORZAR reinstalación de NumPy desde código fuente
# Esto sobrescribe el numpy precompilado que instaló chromadb
RUN pip uninstall -y numpy && \
    pip install --no-cache-dir --no-binary numpy "numpy<2.0.0"

# Copiar código
COPY . .

# Crear directorio para ChromaDB
RUN mkdir -p /app/chroma_db

# Puerto
EXPOSE 8001

# Comando
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
