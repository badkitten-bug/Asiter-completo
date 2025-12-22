# TDR Extractor 📄🔍

Microservicio para extracción automática de campos desde PDFs de Términos de Referencia (TDR) usando OCR y LLM.

## 🎯 Características

- **Extracción inteligente**: Detecta automáticamente si el PDF es digital o escaneado
- **OCR integrado**: Usa Tesseract para PDFs escaneados
- **LLM flexible**: Soporta Ollama (local) o DeepSeek API
- **Esquema dinámico**: El JSON de salida se adapta al contenido del documento
- **API REST**: Endpoints fáciles de integrar con cualquier frontend

## 📁 Estructura del Proyecto

```
tdr-extractor/
├── app/
│   ├── __init__.py
│   ├── config.py      # Configuración con Pydantic Settings
│   ├── main.py        # FastAPI endpoints
│   ├── ocr.py         # Módulo de OCR
│   └── extractor.py   # Módulo de extracción con LLM
├── models/
│   ├── __init__.py
│   └── responses.py   # Modelos Pydantic para respuestas
├── uploads/           # PDFs subidos (temporal)
├── samples/           # PDFs de prueba
├── .env               # Variables de entorno
├── pyproject.toml     # Dependencias (Poetry)
├── run.sh             # Script de inicio (Linux/Mac)
├── run.ps1            # Script de inicio (Windows)
└── test_extract.py    # Script de prueba
```

## 🚀 Instalación

### Requisitos Previos

1. **Python 3.11+**
2. **Poetry** (gestor de dependencias)
3. **Ollama** (para LLM local) o API key de DeepSeek
4. **Tesseract OCR** (opcional, para PDFs escaneados)

### Pasos de Instalación

```bash
# 1. Navegar al directorio
cd tdr-extractor

# 2. Instalar dependencias con Poetry
poetry install

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu configuración

# 4. Si usas Ollama, descargar el modelo
ollama pull deepseek-r1:8b
```

### Instalación de Tesseract (Opcional)

**Windows:**
```powershell
# Con Chocolatey
choco install tesseract

# O descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
```

**Linux:**
```bash
sudo apt install tesseract-ocr tesseract-ocr-spa
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

## ⚙️ Configuración

Edita el archivo `.env`:

```env
# Usar LLM local (Ollama) o remoto (DeepSeek)
USE_LOCAL_LLM=true

# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:8b

# DeepSeek API (si USE_LOCAL_LLM=false)
DEEPSEEK_API_KEY=tu-api-key
DEEPSEEK_MODEL=deepseek-chat

# OCR
OCR_LANGUAGE=spa
```

## 🏃 Ejecución

### Windows
```powershell
# Con Poetry
poetry run uvicorn app.main:app --reload

# O con el script
.\run.ps1
```

### Linux/Mac
```bash
# Con Poetry
poetry run uvicorn app.main:app --reload

# O con el script
./run.sh
```

El servidor estará disponible en: `http://localhost:8000`

## 📚 API Endpoints

### POST `/extract-tdr`

Extrae campos de un PDF de TDR.

**Request:**
```bash
curl -X POST "http://localhost:8000/extract-tdr" \
  -F "file=@mi_tdr.pdf"
```

**Response:**
```json
{
  "success": true,
  "filename": "mi_tdr.pdf",
  "extraction_method": "digital",
  "page_count": 10,
  "fields": {
    "objeto_contratacion": "...",
    "plazo_ejecucion": "...",
    "entregables": [...],
    ...
  },
  "metadata": {
    "processed_at": "2024-11-26T...",
    "text_length": 15000
  }
}
```

### POST `/extract-text`

Extrae solo el texto del PDF (sin procesamiento LLM).

### GET `/health`

Verifica el estado del servicio.

### GET `/docs`

Documentación interactiva (Swagger UI).

## 🧪 Pruebas

```bash
# Colocar un PDF de prueba
cp tu_tdr.pdf samples/tdr1.pdf

# Ejecutar test
poetry run python test_extract.py

# O con un PDF específico
poetry run python test_extract.py path/to/your.pdf
```

## 📋 Campos Detectados

El extractor busca automáticamente estos campos (solo incluye los que encuentra):

| Campo | Descripción |
|-------|-------------|
| `objeto_contratacion` | Descripción del objeto |
| `denominacion_servicio` | Nombre del servicio |
| `finalidad_publica` | Finalidad pública |
| `alcance` | Alcance del servicio |
| `servicios_requeridos` | Lista de servicios |
| `actividades` | Actividades a realizar |
| `entregables` | Entregables con plazos |
| `plazo_ejecucion` | Plazo total |
| `lugar_prestacion` | Lugar de prestación |
| `perfil_profesional` | Requisitos del profesional |
| `requisitos_tecnicos_minimos` | Requisitos técnicos |
| `penalidades` | Penalidades |
| `forma_pago` | Forma de pago |
| `monto_referencial` | Presupuesto |
| `normativa_aplicable` | Marco legal |
| ... | Y más según el documento |

## 🔗 Integración con Frontend

```typescript
// Ejemplo en Next.js/React
const extractTdr = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/extract-tdr', {
    method: 'POST',
    body: formData,
  });
  
  const data = await response.json();
  return data.fields;
};
```

## 🛠️ Siguiente Fase

Este microservicio es la **Fase 1** del sistema completo:

1. ✅ **Fase 1**: Extracción de PDFs (este microservicio)
2. ⏳ **Fase 2**: Base de datos flexible (MongoDB/PostgreSQL)
3. ⏳ **Fase 3**: Backend de almacenamiento
4. ⏳ **Fase 4**: Integración con Next.js
5. ⏳ **Fase 5**: Implementación RAG (búsqueda vectorial)

## 📄 Licencia

MIT

