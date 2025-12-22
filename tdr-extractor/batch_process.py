#!/usr/bin/env python3
"""
Script de procesamiento batch para 400+ PDFs de TDR.

Este script:
1. Lee todos los PDFs de la carpeta 'pdfs/'
2. Extrae el texto usando OCR (DeepSeek API o Tesseract local)
3. Extrae los campos usando LLM (Ollama local)
4. Guarda los resultados en JSON

Uso:
    python batch_process.py
    python batch_process.py --folder mi_carpeta
    python batch_process.py --resume  # Continuar desde donde se quedó
    python batch_process.py --limit 10  # Procesar solo 10 PDFs
"""
import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Agregar el directorio app al path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import get_settings
from app.ocr import extract_text
from app.extractor import extract_tdr_fields


class Colors:
    """Colores para output en terminal."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header():
    """Imprime el encabezado del script."""
    print(f"""
{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗
║                    TDR BATCH EXTRACTOR                       ║
║              Procesamiento masivo de PDFs                    ║
╚══════════════════════════════════════════════════════════════╝{Colors.RESET}
""")


def get_processed_files(output_dir: Path) -> set:
    """Obtiene la lista de archivos ya procesados (incluyendo subcarpetas)."""
    processed = set()
    if output_dir.exists():
        for json_file in output_dir.rglob("*.json"):  # rglob para subcarpetas
            # Usar ruta relativa completa como identificador
            try:
                rel_path = json_file.relative_to(output_dir)
                # Guardar tanto el nombre como la ruta relativa (sin extensión)
                processed.add(json_file.stem)
                processed.add(str(rel_path.with_suffix('')))
            except ValueError:
                processed.add(json_file.stem)
    return processed


async def process_single_pdf(
    pdf_path: Path,
    output_dir: Path,
    input_base_dir: Path,
    settings,
    use_deepseek_api: bool = False
) -> dict:
    """
    Procesa un único PDF y devuelve el resultado.
    
    Returns:
        dict con success, filename, fields, error, etc.
    """
    # Calcular ruta relativa para mantener estructura de carpetas
    try:
        relative_path = pdf_path.relative_to(input_base_dir)
        category = relative_path.parent.name if relative_path.parent != Path('.') else "general"
    except ValueError:
        relative_path = Path(pdf_path.name)
        category = "general"
    
    result = {
        "filename": pdf_path.name,
        "category": category,
        "relative_path": str(relative_path),
        "success": False,
        "error": None,
        "text_length": 0,
        "page_count": 0,
        "fields": {},
        "processed_at": datetime.now().isoformat()
    }
    
    try:
        # Paso 1: Extraer texto del PDF
        print(f"  {Colors.YELLOW}📄 Extrayendo texto...{Colors.RESET}", end=" ", flush=True)
        
        if use_deepseek_api and settings.deepseek_api_key:
            # Usar DeepSeek Vision API para OCR
            from app.deepseek_ocr_api import extract_text_with_deepseek
            text, page_count = await extract_text_with_deepseek(pdf_path=str(pdf_path))
            method = "deepseek_api"
        else:
            # Usar OCR local (PyPDF + Tesseract si es necesario)
            ocr_result = extract_text(str(pdf_path))
            text = ocr_result["text"]
            page_count = ocr_result["page_count"]
            method = ocr_result["method"]
        
        result["text_length"] = len(text)
        result["page_count"] = page_count
        result["extraction_method"] = method
        
        print(f"{Colors.GREEN}✓{Colors.RESET} ({len(text):,} chars, {page_count} páginas)")
        
        if not text.strip():
            result["error"] = "No se pudo extraer texto del PDF"
            print(f"  {Colors.RED}❌ Sin texto extraído{Colors.RESET}")
            return result
        
        # Paso 2: Extraer campos con LLM
        print(f"  {Colors.YELLOW}🧠 Analizando con LLM...{Colors.RESET}", end=" ", flush=True)
        
        fields = await extract_tdr_fields(text)
        result["fields"] = fields
        result["success"] = True
        
        print(f"{Colors.GREEN}✓{Colors.RESET} ({len(fields)} campos)")
        
        # Paso 3: Guardar resultado (manteniendo estructura de carpetas)
        output_subdir = output_dir / relative_path.parent
        output_subdir.mkdir(parents=True, exist_ok=True)
        output_file = output_subdir / f"{pdf_path.stem}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
    except Exception as e:
        result["error"] = str(e)
        print(f"{Colors.RED}❌ Error: {e}{Colors.RESET}")
    
    return result


async def batch_process(
    input_dir: Path,
    output_dir: Path,
    resume: bool = True,
    limit: Optional[int] = None,
    use_deepseek_api: bool = False
):
    """Procesa todos los PDFs en el directorio y subdirectorios."""
    settings = get_settings()
    
    # Crear directorio de salida
    output_dir.mkdir(exist_ok=True)
    
    # Obtener lista de PDFs (incluyendo subcarpetas)
    pdf_files = sorted(input_dir.rglob("*.pdf"))  # rglob busca recursivamente
    total_files = len(pdf_files)
    
    if total_files == 0:
        print(f"{Colors.RED}❌ No se encontraron archivos PDF en {input_dir}{Colors.RESET}")
        print(f"{Colors.YELLOW}   Coloca tus PDFs en la carpeta 'pdfs/' y ejecuta nuevamente.{Colors.RESET}")
        return
    
    print(f"{Colors.CYAN}📁 Directorio de entrada:{Colors.RESET} {input_dir}")
    print(f"{Colors.CYAN}📁 Directorio de salida:{Colors.RESET} {output_dir}")
    print(f"{Colors.CYAN}📊 Total de PDFs encontrados:{Colors.RESET} {total_files}")
    
    # Filtrar archivos ya procesados si resume=True
    if resume:
        processed = get_processed_files(output_dir)
        original_count = len(pdf_files)
        
        def is_processed(pdf_path: Path) -> bool:
            """Verifica si el PDF ya fue procesado."""
            try:
                rel = pdf_path.relative_to(input_dir)
                rel_no_ext = str(rel.with_suffix(''))
                return pdf_path.stem in processed or rel_no_ext in processed
            except ValueError:
                return pdf_path.stem in processed
        
        pdf_files = [p for p in pdf_files if not is_processed(p)]
        skipped = original_count - len(pdf_files)
        if skipped > 0:
            print(f"{Colors.GREEN}✓ Omitiendo {skipped} archivos ya procesados{Colors.RESET}")
    
    # Aplicar límite si se especificó
    if limit:
        pdf_files = pdf_files[:limit]
        print(f"{Colors.YELLOW}⚠ Limitado a {limit} archivos{Colors.RESET}")
    
    pending = len(pdf_files)
    print(f"{Colors.CYAN}📋 Archivos a procesar:{Colors.RESET} {pending}")
    
    # Mostrar configuración de OCR/LLM
    if use_deepseek_api and settings.deepseek_api_key:
        print(f"{Colors.MAGENTA}🔑 OCR: DeepSeek Vision API{Colors.RESET}")
    else:
        print(f"{Colors.MAGENTA}🔧 OCR: Local (PyPDF + Tesseract){Colors.RESET}")
    
    if settings.use_local_llm:
        print(f"{Colors.MAGENTA}🧠 LLM: Ollama ({settings.ollama_model}){Colors.RESET}")
    else:
        print(f"{Colors.MAGENTA}🧠 LLM: DeepSeek API{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    # Estadísticas
    stats = {
        "processed": 0,
        "success": 0,
        "failed": 0,
        "start_time": time.time(),
        "by_category": {}  # Estadísticas por carpeta/categoría
    }
    
    # Procesar cada PDF
    for i, pdf_path in enumerate(pdf_files, 1):
        # Mostrar categoría/carpeta del PDF
        try:
            rel = pdf_path.relative_to(input_dir)
            category = f"[{rel.parent}] " if rel.parent != Path('.') else ""
        except ValueError:
            category = ""
        
        print(f"{Colors.BOLD}[{i}/{pending}]{Colors.RESET} {Colors.MAGENTA}{category}{Colors.RESET}{Colors.BLUE}{pdf_path.name}{Colors.RESET}")
        
        result = await process_single_pdf(
            pdf_path, output_dir, input_dir, settings, use_deepseek_api
        )
        
        stats["processed"] += 1
        if result["success"]:
            stats["success"] += 1
        else:
            stats["failed"] += 1
        
        # Estadísticas por categoría
        cat = result.get("category", "general")
        if cat not in stats["by_category"]:
            stats["by_category"][cat] = {"success": 0, "failed": 0}
        if result["success"]:
            stats["by_category"][cat]["success"] += 1
        else:
            stats["by_category"][cat]["failed"] += 1
        
        # Mostrar progreso cada 10 archivos
        if i % 10 == 0:
            elapsed = time.time() - stats["start_time"]
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (pending - i) / rate if rate > 0 else 0
            print(f"\n{Colors.CYAN}📊 Progreso: {i}/{pending} ({i*100//pending}%)")
            print(f"   ⏱ Tiempo: {elapsed:.0f}s | Velocidad: {rate:.2f} PDF/s | ETA: {remaining:.0f}s{Colors.RESET}\n")
    
    # Resumen final
    elapsed = time.time() - stats["start_time"]
    
    # Construir tabla de categorías
    category_table = ""
    for cat, cat_stats in sorted(stats["by_category"].items()):
        total_cat = cat_stats["success"] + cat_stats["failed"]
        category_table += f"   {cat}: {cat_stats['success']}/{total_cat} exitosos\n"
    
    print(f"""
{Colors.BOLD}{'='*60}
                      RESUMEN FINAL
{'='*60}{Colors.RESET}

{Colors.GREEN}✓ Procesados exitosamente:{Colors.RESET} {stats['success']}
{Colors.RED}✗ Con errores:{Colors.RESET} {stats['failed']}
{Colors.CYAN}⏱ Tiempo total:{Colors.RESET} {elapsed:.1f} segundos

{Colors.MAGENTA}📊 Por categoría:{Colors.RESET}
{category_table}
{Colors.CYAN}📁 Resultados guardados en:{Colors.RESET} {output_dir}
""")


def main():
    parser = argparse.ArgumentParser(
        description="Procesa PDFs de TDR en batch y extrae campos con OCR+LLM"
    )
    parser.add_argument(
        "--folder", "-f",
        type=str,
        default="pdfs",
        help="Carpeta con los PDFs a procesar (default: pdfs/)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="output",
        help="Carpeta para guardar los JSON (default: output/)"
    )
    parser.add_argument(
        "--resume", "-r",
        action="store_true",
        default=True,
        help="Continuar desde donde se quedó (omite archivos ya procesados)"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Reprocesar todos los archivos"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Limitar número de archivos a procesar"
    )
    parser.add_argument(
        "--deepseek-api",
        action="store_true",
        help="Usar DeepSeek Vision API para OCR (requiere DEEPSEEK_API_KEY)"
    )
    
    args = parser.parse_args()
    
    # Rutas
    base_dir = Path(__file__).parent
    input_dir = base_dir / args.folder
    output_dir = base_dir / args.output
    
    print_header()
    
    # Verificar que existe la carpeta de entrada
    if not input_dir.exists():
        print(f"{Colors.YELLOW}📁 Creando carpeta {input_dir}...{Colors.RESET}")
        input_dir.mkdir(exist_ok=True)
        print(f"{Colors.GREEN}✓ Carpeta creada. Coloca tus PDFs ahí y ejecuta nuevamente.{Colors.RESET}")
        return
    
    # Ejecutar procesamiento
    resume = not args.no_resume
    asyncio.run(batch_process(
        input_dir=input_dir,
        output_dir=output_dir,
        resume=resume,
        limit=args.limit,
        use_deepseek_api=args.deepseek_api
    ))


if __name__ == "__main__":
    main()

