#!/usr/bin/env python3
"""
Script de prueba para el endpoint /extract-tdr.

Uso:
    python test_extract.py
    python test_extract.py /path/to/your/tdr.pdf
"""
import json
import sys
from pathlib import Path

import requests

# Configuración
API_URL = "http://localhost:8000"
DEFAULT_PDF = "samples/tdr1.pdf"


def test_health():
    """Verifica que el servicio esté corriendo."""
    print("🔍 Verificando servicio...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Servicio activo: {data['status']}")
        print(f"   LLM: {'Ollama local' if data['config']['use_local_llm'] else 'DeepSeek API'}")
        if data['config'].get('ollama_model'):
            print(f"   Modelo: {data['config']['ollama_model']}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servicio")
        print("   Asegúrate de que el servidor esté corriendo:")
        print("   poetry run uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_extract_tdr(pdf_path: str):
    """Prueba la extracción de un TDR."""
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"❌ Error: No se encontró el archivo {pdf_path}")
        print("   Coloca un PDF de prueba en: samples/tdr1.pdf")
        return None
    
    print(f"\n📄 Procesando: {pdf_path.name}")
    print(f"   Tamaño: {pdf_path.stat().st_size / 1024:.1f} KB")
    print("   Enviando al servidor...")
    
    try:
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path.name, f, "application/pdf")}
            response = requests.post(
                f"{API_URL}/extract-tdr",
                files=files,
                params={"save_pdf": False},
                timeout=300,  # 5 minutos para documentos grandes
            )
        
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            print(f"✅ Extracción exitosa!")
            print(f"   Método: {data['extraction_method']}")
            print(f"   Páginas: {data['page_count']}")
            print(f"   Campos detectados: {len(data['fields'])}")
            
            print("\n📋 Campos extraídos:")
            print("-" * 50)
            print(json.dumps(data["fields"], indent=2, ensure_ascii=False))
            
            return data
        else:
            print(f"⚠️ Extracción sin resultados: {data.get('error', 'Sin detalles')}")
            return data
            
    except requests.exceptions.Timeout:
        print("❌ Error: Timeout - El procesamiento tomó demasiado tiempo")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error HTTP: {e.response.status_code}")
        try:
            error_detail = e.response.json()
            print(f"   Detalle: {error_detail.get('detail', 'Sin detalles')}")
        except:
            print(f"   Respuesta: {e.response.text[:200]}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_extract_text(pdf_path: str):
    """Prueba solo la extracción de texto (sin LLM)."""
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"❌ Error: No se encontró el archivo {pdf_path}")
        return None
    
    print(f"\n📄 Extrayendo texto de: {pdf_path.name}")
    
    try:
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path.name, f, "application/pdf")}
            response = requests.post(
                f"{API_URL}/extract-text",
                files=files,
                timeout=60,
            )
        
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Texto extraído!")
        print(f"   Método: {data['method']}")
        print(f"   Páginas: {data['page_count']}")
        print(f"   Caracteres: {len(data['text'])}")
        
        # Mostrar preview del texto
        preview = data['text'][:500] + "..." if len(data['text']) > 500 else data['text']
        print(f"\n📝 Preview del texto:")
        print("-" * 50)
        print(preview)
        
        return data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    """Función principal."""
    print("=" * 60)
    print("🧪 Test del TDR Extractor")
    print("=" * 60)
    
    # Determinar qué PDF usar
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = DEFAULT_PDF
    
    # Verificar servicio
    if not test_health():
        sys.exit(1)
    
    # Probar extracción
    result = test_extract_tdr(pdf_path)
    
    if result and result.get("success"):
        # Guardar resultado en archivo
        output_file = Path(pdf_path).stem + "_extracted.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Resultado guardado en: {output_file}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

