"""
Script para importar TDRs desde JSONs a ChromaDB.
Recrea la base de datos vectorial con los 730+ TDRs.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any

# Agregar el directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.chroma import chroma_client
from app.services.embeddings import embedding_service

# Directorio con los JSONs
OUTPUT_DIR = Path("D:/Asiter-completo/tdr-extractor/output_gemini")

# Mapeo de carpetas a tipos de TDR
CATEGORY_TO_TIPO = {
    "Bien": "BIEN",
    "Servicio": "SERVICIO", 
    "Obra": "OBRA",
    "Consultoria de obra": "CONSULTORIA_OBRA",
    "Archivos de distintos tipos": "SERVICIO"  # Default
}


def load_json_file(filepath: Path) -> dict | None:
    """Carga un archivo JSON."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [WARN] Error leyendo {filepath.name}: {e}")
        return None


def process_tdr(data: dict, category: str) -> tuple[str, dict, str] | None:
    """Procesa un TDR y devuelve (id, metadata, document)."""
    if not data.get("success", False):
        return None
    
    fields = data.get("fields", {})
    if not fields:
        return None
    
    filename = data.get("filename", "unknown.pdf")
    tipo = CATEGORY_TO_TIPO.get(category, "SERVICIO")
    
    # Crear texto para embedding
    text = embedding_service.create_tdr_text(fields, tipo)
    
    # Metadata para ChromaDB (solo strings, números o booleans)
    metadata = {
        "filename": filename,
        "tipo": tipo,
        "category": category,
        "page_count": data.get("page_count", 0),
        "fields_json": json.dumps(fields, ensure_ascii=False)[:50000]  # Límite 
    }
    
    # ID único
    tdr_id = f"{tipo}_{filename.replace(' ', '_').replace('.pdf', '')}"
    
    return tdr_id, metadata, text


def import_all_tdrs():
    """Importa todos los TDRs a ChromaDB."""
    print("[START] Iniciando importacion de TDRs a ChromaDB...")
    print(f"[DIR] Directorio fuente: {OUTPUT_DIR}")
    
    all_tdrs = []
    
    # Recorrer cada categoría
    for category_dir in OUTPUT_DIR.iterdir():
        if not category_dir.is_dir():
            continue
        
        category = category_dir.name
        print(f"\n[CAT] Procesando categoria: {category}")
        
        json_files = list(category_dir.glob("*.json"))
        print(f"   Archivos encontrados: {len(json_files)}")
        
        for json_file in json_files:
            data = load_json_file(json_file)
            if not data:
                continue
            
            result = process_tdr(data, category)
            if result:
                all_tdrs.append(result)
    
    print(f"\n[OK] TDRs validos para importar: {len(all_tdrs)}")
    
    if not all_tdrs:
        print("[ERROR] No se encontraron TDRs validos")
        return
    
    # Generar embeddings en batch
    print("\n[*] Generando embeddings... (esto puede tomar unos minutos)")
    
    ids = [t[0] for t in all_tdrs]
    metadatas = [t[1] for t in all_tdrs]
    documents = [t[2] for t in all_tdrs]
    
    # Generar embeddings en batches de 50
    batch_size = 50
    embeddings = []
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        print(f"   Procesando batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}...")
        batch_embeddings = embedding_service.get_embeddings_batch(batch)
        embeddings.extend(batch_embeddings)
    
    # Insertar en ChromaDB en batches
    print("\n[*] Insertando en ChromaDB...")
    
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        print(f"   Insertando batch {i//batch_size + 1}/{(len(ids)-1)//batch_size + 1}...")
        
        chroma_client.add_tdrs_batch(
            ids=ids[i:end],
            embeddings=embeddings[i:end],
            metadatas=metadatas[i:end],
            documents=documents[i:end]
        )
    
    # Verificar
    stats = chroma_client.get_stats()
    print(f"\n[DONE] Importacion completada!")
    print(f"   Total TDRs en BD: {stats['total_tdrs']}")
    print(f"   Por tipo: {stats['por_tipo']}")


if __name__ == "__main__":
    import_all_tdrs()
