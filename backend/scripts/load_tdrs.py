#!/usr/bin/env python3
"""
Script para cargar los JSONs de TDR a ChromaDB.

Uso:
    python scripts/load_tdrs.py
    python scripts/load_tdrs.py --clear  # Limpiar BD antes de cargar
"""
import argparse
import json
import sys
import time
from pathlib import Path

# Agregar el directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.db.chroma import chroma_client
from app.db.models import TdrTipo
from app.services.embeddings import embedding_service


# Mapeo de categorías de carpetas a tipos de TDR
CATEGORY_TO_TIPO = {
    "Bien": TdrTipo.BIEN,
    "Servicio": TdrTipo.SERVICIO,
    "Consultoria de obra": TdrTipo.CONSULTORIA_OBRA,
    "Obra": TdrTipo.OBRA,
    "Archivos de distintos tipos": TdrTipo.SERVICIO,  # Default
}


class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def detect_tipo(fields: dict, category: str) -> TdrTipo:
    """Detecta el tipo de TDR basándose en los campos y categoría."""
    # Primero intentar por categoría
    if category in CATEGORY_TO_TIPO:
        return CATEGORY_TO_TIPO[category]
    
    # Luego analizar campos
    text = json.dumps(fields, ensure_ascii=False).lower()
    
    if "bien" in text or "adquisición" in text or "suministro" in text:
        return TdrTipo.BIEN
    elif "obra" in text and "consultoría" in text:
        return TdrTipo.CONSULTORIA_OBRA
    elif "obra" in text or "construcción" in text:
        return TdrTipo.OBRA
    else:
        return TdrTipo.SERVICIO


def load_json_file(json_path: Path) -> dict:
    """Carga un archivo JSON."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def process_tdr(json_path: Path, base_dir: Path) -> tuple:
    """
    Procesa un archivo JSON de TDR.
    
    Returns:
        tuple: (id, embedding, metadata, document)
    """
    data = load_json_file(json_path)
    
    # Extraer información
    filename = data.get("filename", json_path.name)
    category = data.get("category", json_path.parent.name)
    fields = data.get("fields", {})
    
    # Detectar tipo
    tipo = detect_tipo(fields, category)
    
    # Crear texto para embedding
    text_for_embedding = embedding_service.create_tdr_text(fields, tipo.value)
    
    # Generar ID único
    tdr_id = f"{category}_{json_path.stem}".replace(" ", "_").replace(".", "_")
    
    # Crear metadata (ChromaDB solo acepta strings, números y booleanos)
    metadata = {
        "filename": filename,
        "category": category,
        "tipo": tipo.value,
        "fields_json": json.dumps(fields, ensure_ascii=False)[:10000]  # Limitar tamaño
    }
    
    return tdr_id, text_for_embedding, metadata


def main():
    parser = argparse.ArgumentParser(description="Carga TDRs a ChromaDB")
    parser.add_argument("--clear", action="store_true", help="Limpiar BD antes de cargar")
    parser.add_argument("--limit", type=int, help="Limitar número de TDRs a cargar")
    args = parser.parse_args()
    
    settings = get_settings()
    
    print(f"""
{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗
║              CARGA DE TDRs A CHROMADB                        ║
╚══════════════════════════════════════════════════════════════╝{Colors.RESET}
""")
    
    # Directorio de JSONs
    jsons_dir = Path(settings.tdr_jsons_dir).resolve()
    print(f"{Colors.CYAN}📁 Directorio de JSONs:{Colors.RESET} {jsons_dir}")
    
    if not jsons_dir.exists():
        print(f"{Colors.RED}❌ Directorio no existe{Colors.RESET}")
        return
    
    # Limpiar BD si se solicita
    if args.clear:
        print(f"{Colors.YELLOW}🗑️ Limpiando base de datos...{Colors.RESET}")
        chroma_client.clear()
        print(f"{Colors.GREEN}✓ Base de datos limpiada{Colors.RESET}")
    
    # Obtener lista de JSONs
    json_files = list(jsons_dir.rglob("*.json"))
    total_files = len(json_files)
    
    if args.limit:
        json_files = json_files[:args.limit]
    
    print(f"{Colors.CYAN}📊 Total de JSONs encontrados:{Colors.RESET} {total_files}")
    print(f"{Colors.CYAN}📋 A procesar:{Colors.RESET} {len(json_files)}")
    print()
    
    # Procesar en batches
    batch_size = 50
    all_ids = []
    all_embeddings = []
    all_metadatas = []
    all_documents = []
    
    stats = {"processed": 0, "errors": 0, "por_tipo": {}}
    start_time = time.time()
    
    print(f"{Colors.BOLD}Procesando...{Colors.RESET}")
    
    for i, json_path in enumerate(json_files, 1):
        try:
            tdr_id, text, metadata = process_tdr(json_path, jsons_dir)
            
            all_ids.append(tdr_id)
            all_documents.append(text)
            all_metadatas.append(metadata)
            
            tipo = metadata["tipo"]
            stats["por_tipo"][tipo] = stats["por_tipo"].get(tipo, 0) + 1
            stats["processed"] += 1
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error en {json_path.name}: {e}{Colors.RESET}")
            stats["errors"] += 1
        
        # Mostrar progreso cada 50
        if i % 50 == 0:
            print(f"  {Colors.CYAN}[{i}/{len(json_files)}]{Colors.RESET} procesados...")
    
    print()
    print(f"{Colors.YELLOW}🔄 Generando embeddings...{Colors.RESET}")
    
    # Generar embeddings en batch
    all_embeddings = embedding_service.get_embeddings_batch(all_documents)
    
    print(f"{Colors.GREEN}✓ Embeddings generados{Colors.RESET}")
    print()
    print(f"{Colors.YELLOW}💾 Guardando en ChromaDB...{Colors.RESET}")
    
    # Guardar en batches
    for i in range(0, len(all_ids), batch_size):
        batch_ids = all_ids[i:i+batch_size]
        batch_embeddings = all_embeddings[i:i+batch_size]
        batch_metadatas = all_metadatas[i:i+batch_size]
        batch_documents = all_documents[i:i+batch_size]
        
        chroma_client.add_tdrs_batch(
            ids=batch_ids,
            embeddings=batch_embeddings,
            metadatas=batch_metadatas,
            documents=batch_documents
        )
        print(f"  {Colors.GREEN}✓{Colors.RESET} Guardados {min(i+batch_size, len(all_ids))}/{len(all_ids)}")
    
    elapsed = time.time() - start_time
    
    # Resumen
    print(f"""
{Colors.BOLD}{'='*60}
                      RESUMEN
{'='*60}{Colors.RESET}

{Colors.GREEN}✓ TDRs cargados:{Colors.RESET} {stats['processed']}
{Colors.RED}✗ Errores:{Colors.RESET} {stats['errors']}
{Colors.CYAN}⏱ Tiempo total:{Colors.RESET} {elapsed:.1f} segundos

{Colors.MAGENTA}📊 Por tipo:{Colors.RESET}
""")
    for tipo, count in sorted(stats["por_tipo"].items()):
        print(f"   {tipo}: {count}")
    
    # Verificar estadísticas de la BD
    db_stats = chroma_client.get_stats()
    print(f"""
{Colors.CYAN}📦 Total en ChromaDB:{Colors.RESET} {db_stats['total_tdrs']}
""")


if __name__ == "__main__":
    main()

