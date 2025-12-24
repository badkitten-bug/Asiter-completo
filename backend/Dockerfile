FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema para compilar NumPy
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (para cache de Docker)
COPY requirements.txt .

# Compilar NumPy desde código fuente para esta CPU específica
# Esto evita el error de optimizaciones X86_V2
RUN pip install --no-cache-dir --no-binary numpy "numpy<2.0.0"

# Instalar dependencias Python (chromadb no sobreescribirá numpy)
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Crear directorio para ChromaDB
RUN mkdir -p /app/chroma_db

# Puerto
EXPOSE 8001

# Comando
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
