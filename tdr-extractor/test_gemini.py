#!/usr/bin/env python3
"""
Script de prueba para extracción con Gemini.
"""
import json
import sys
from pathlib import Path

# Tu API key de Gemini
GEMINI_API_KEY = "AIzaSyA7Lniit_f8Dq9lvxJSCZBwzNhOXdlc4BQ"

# Agregar el directorio app al path
sys.path.insert(0, str(Path(__file__).parent))

from app.gemini_extractor import GeminiExtractor

def test_single_pdf():
    """Prueba con un solo PDF."""
    
    # Buscar el primer PDF disponible
    pdfs_dir = Path("pdfs")
    pdf_files = list(pdfs_dir.rglob("*.pdf"))
    
    if not pdf_files:
        print("❌ No se encontraron PDFs en la carpeta 'pdfs/'")
        return
    
    # Usar el primer PDF
    pdf_path = pdf_files[0]
    print(f"📄 Probando con: {pdf_path.name}")
    print(f"   Ruta: {pdf_path}")
    print()
    
    # Crear extractor
    extractor = GeminiExtractor(GEMINI_API_KEY)
    
    print("🔄 Convirtiendo PDF a imágenes...")
    images = extractor.pdf_to_images(str(pdf_path), dpi=120, max_pages=10)
    print(f"   ✓ {len(images)} páginas convertidas")
    print()
    
    print("🧠 Enviando a Gemini para análisis...")
    try:
        result = extractor.extract_from_pdf_sync(str(pdf_path), max_pages=10)
        
        print()
        print("=" * 60)
        print("                    RESULTADO")
        print("=" * 60)
        print()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()
        
        # Guardar resultado
        output_file = Path("output") / f"{pdf_path.stem}_gemini.json"
        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Guardado en: {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_single_pdf()

