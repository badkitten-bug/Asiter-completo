#!/usr/bin/env python3
"""
Script de procesamiento batch para PDFs de TDR usando Google Gemini.

Uso:
    python batch_gemini.py
    python batch_gemini.py --limit 10
    python batch_gemini.py --resume
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Agregar el directorio app al path
sys.path.insert(0, str(Path(__file__).parent))

from app.gemini_extractor import GeminiExtractor

# Tu API key de Gemini
GEMINI_API_KEY = "AIzaSyA7Lniit_f8Dq9lvxJSCZBwzNhOXdlc4BQ"


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
║            TDR BATCH EXTRACTOR - GEMINI PRO                  ║
║              Procesamiento masivo con IA                     ║
╚══════════════════════════════════════════════════════════════╝{Colors.RESET}
""")


def get_processed_files(output_dir: Path) -> set:
    """Obtiene la lista de archivos ya procesados."""
    processed = set()
    if output_dir.exists():
        for json_file in output_dir.rglob("*.json"):
            try:
                rel_path = json_file.relative_to(output_dir)
                processed.add(json_file.stem)
                processed.add(str(rel_path.with_suffix('')))
            except ValueError:
                processed.add(json_file.stem)
    return processed


def process_single_pdf(
    extractor: GeminiExtractor,
    pdf_path: Path,
    output_dir: Path,
    input_base_dir: Path,
    max_pages: int = 30
) -> dict:
    """Procesa un único PDF con Gemini."""
    
    # Calcular ruta relativa
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
        "page_count": 0,
        "fields": {},
        "processed_at": datetime.now().isoformat(),
        "extraction_method": "gemini"
    }
    
    try:
        # Paso 1: Convertir PDF a imágenes
        print(f"  {Colors.YELLOW}📄 Convirtiendo PDF...{Colors.RESET}", end=" ", flush=True)
        images = extractor.pdf_to_images(str(pdf_path), dpi=120, max_pages=max_pages)
        result["page_count"] = len(images)
        print(f"{Colors.GREEN}✓{Colors.RESET} ({len(images)} páginas)")
        
        # Paso 2: Enviar a Gemini
        print(f"  {Colors.YELLOW}🧠 Analizando con Gemini...{Colors.RESET}", end=" ", flush=True)
        fields = extractor.extract_from_pdf_sync(str(pdf_path), max_pages=max_pages)
        
        result["fields"] = fields
        result["success"] = True
        
        # Contar campos extraídos
        field_count = len([k for k in fields.keys() if not k.startswith('_')])
        print(f"{Colors.GREEN}✓{Colors.RESET} ({field_count} campos)")
        
        # Guardar resultado
        output_subdir = output_dir / relative_path.parent
        output_subdir.mkdir(parents=True, exist_ok=True)
        output_file = output_subdir / f"{pdf_path.stem}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
    except Exception as e:
        result["error"] = str(e)
        print(f"{Colors.RED}❌ Error: {e}{Colors.RESET}")
        
        # Esperar si es rate limit
        if "429" in str(e) or "rate" in str(e).lower():
            print(f"  {Colors.YELLOW}⏳ Rate limit - esperando 60s...{Colors.RESET}")
            time.sleep(60)
    
    return result


def batch_process(
    input_dir: Path,
    output_dir: Path,
    resume: bool = True,
    limit: Optional[int] = None,
    max_pages: int = 30
):
    """Procesa todos los PDFs con Gemini."""
    
    # Crear extractor
    extractor = GeminiExtractor(GEMINI_API_KEY)
    
    # Crear directorio de salida
    output_dir.mkdir(exist_ok=True)
    
    # Obtener lista de PDFs
    pdf_files = sorted(input_dir.rglob("*.pdf"))
    total_files = len(pdf_files)
    
    if total_files == 0:
        print(f"{Colors.RED}❌ No se encontraron PDFs en {input_dir}{Colors.RESET}")
        return
    
    print(f"{Colors.CYAN}📁 Directorio de entrada:{Colors.RESET} {input_dir}")
    print(f"{Colors.CYAN}📁 Directorio de salida:{Colors.RESET} {output_dir}")
    print(f"{Colors.CYAN}📊 Total de PDFs:{Colors.RESET} {total_files}")
    print(f"{Colors.MAGENTA}🧠 Motor: Google Gemini Pro{Colors.RESET}")
    
    # Filtrar archivos ya procesados
    if resume:
        processed = get_processed_files(output_dir)
        original_count = len(pdf_files)
        
        def is_processed(pdf_path: Path) -> bool:
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
    
    # Aplicar límite
    if limit:
        pdf_files = pdf_files[:limit]
        print(f"{Colors.YELLOW}⚠ Limitado a {limit} archivos{Colors.RESET}")
    
    pending = len(pdf_files)
    print(f"{Colors.CYAN}📋 Archivos a procesar:{Colors.RESET} {pending}")
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    # Estadísticas
    stats = {
        "processed": 0,
        "success": 0,
        "failed": 0,
        "start_time": time.time(),
        "by_category": {}
    }
    
    # Procesar cada PDF
    for i, pdf_path in enumerate(pdf_files, 1):
        try:
            rel = pdf_path.relative_to(input_dir)
            category = f"[{rel.parent}] " if rel.parent != Path('.') else ""
        except ValueError:
            category = ""
        
        print(f"{Colors.BOLD}[{i}/{pending}]{Colors.RESET} {Colors.MAGENTA}{category}{Colors.RESET}{Colors.BLUE}{pdf_path.name}{Colors.RESET}")
        
        result = process_single_pdf(
            extractor, pdf_path, output_dir, input_dir, max_pages
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
        
        # Progreso cada 10 archivos
        if i % 10 == 0:
            elapsed = time.time() - stats["start_time"]
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (pending - i) / rate if rate > 0 else 0
            print(f"\n{Colors.CYAN}📊 Progreso: {i}/{pending} ({i*100//pending}%)")
            print(f"   ⏱ Tiempo: {elapsed:.0f}s | Velocidad: {rate:.2f} PDF/s | ETA: {remaining/60:.1f}min{Colors.RESET}\n")
        
        # Pequeña pausa para no saturar la API (rate limiting)
        time.sleep(1)
    
    # Resumen final
    elapsed = time.time() - stats["start_time"]
    
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
{Colors.CYAN}⏱ Tiempo total:{Colors.RESET} {elapsed/60:.1f} minutos

{Colors.MAGENTA}📊 Por categoría:{Colors.RESET}
{category_table}
{Colors.CYAN}📁 Resultados en:{Colors.RESET} {output_dir}
""")


def main():
    parser = argparse.ArgumentParser(
        description="Procesa PDFs de TDR con Google Gemini"
    )
    parser.add_argument(
        "--folder", "-f",
        type=str,
        default="pdfs",
        help="Carpeta con PDFs (default: pdfs/)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="output_gemini",
        help="Carpeta de salida (default: output_gemini/)"
    )
    parser.add_argument(
        "--resume", "-r",
        action="store_true",
        default=True,
        help="Continuar desde donde se quedó"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Reprocesar todos"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Limitar número de PDFs"
    )
    parser.add_argument(
        "--max-pages", "-p",
        type=int,
        default=30,
        help="Máximo de páginas por PDF (default: 30)"
    )
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent
    input_dir = base_dir / args.folder
    output_dir = base_dir / args.output
    
    print_header()
    
    if not input_dir.exists():
        print(f"{Colors.RED}❌ Carpeta no existe: {input_dir}{Colors.RESET}")
        return
    
    resume = not args.no_resume
    batch_process(
        input_dir=input_dir,
        output_dir=output_dir,
        resume=resume,
        limit=args.limit,
        max_pages=args.max_pages
    )


if __name__ == "__main__":
    main()

