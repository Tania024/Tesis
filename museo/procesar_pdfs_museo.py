"""
PROCESADOR DE PDFs DEL MUSEO PUMAPUNGO
Extrae información de los PDFs y la estructura por áreas usando IA local (Ollama)

INSTRUCCIONES:
1. Copia este archivo a: C:\\Users\\Tania\\Documents\\Tesis\\museo\\backend\\
2. Pon todos los PDFs en: C:\\Users\\Tania\\Documents\\Tesis\\museo\\pdfs_museo\\
3. Ejecuta: python procesar_pdfs_museo.py
4. Se generará: museo_knowledge.json
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any
import requests
from datetime import datetime

# Instalar si no tienes: pip install pypdf pdfplumber
try:
    import pdfplumber
    print("✅ pdfplumber disponible")
except ImportError:
    print("❌ Instala pdfplumber: pip install pdfplumber")
    exit(1)

# Configuración
CARPETA_PDFS = r"C:\Users\Tania\Documents\Tesis\museo\pdfs_museo"
OLLAMA_URL = "http://localhost:11434"
MODELO = "deepseek-r1:7b"
OUTPUT_FILE = "museo_knowledge.json"

# Áreas del Museo Pumapungo (basado en tu BD)
AREAS_MUSEO = {
    "ARQ-01": "Sala Arqueológica Cañari",
    "ETN-01": "Sala Etnográfica",
    "AVE-01": "Aviario de Aves Andinas",
    "BOT-01": "Jardín Botánico",
    "ART-01": "Sala de Arte Colonial",
    "RUIN-01": "Parque Arqueológico Pumapungo",
    "TEMP-01": "Exhibición Temporal"
}


def extraer_texto_pdf(ruta_pdf: str) -> str:
    """Extraer texto de un PDF"""
    try:
        print(f"  📄 Leyendo: {os.path.basename(ruta_pdf)}")
        texto_completo = []
        
        with pdfplumber.open(ruta_pdf) as pdf:
            print(f"     Páginas: {len(pdf.pages)}")
            
            for i, pagina in enumerate(pdf.pages, 1):
                texto = pagina.extract_text()
                if texto:
                    texto_completo.append(texto)
                
                # Mostrar progreso cada 10 páginas
                if i % 10 == 0:
                    print(f"     Procesadas {i}/{len(pdf.pages)} páginas...")
        
        texto_final = "\n\n".join(texto_completo)
        print(f"  ✅ Extraídos {len(texto_final)} caracteres")
        return texto_final
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return ""


def dividir_texto_en_chunks(texto: str, max_chars: int = 15000) -> List[str]:
    """Dividir texto largo en chunks manejables"""
    # Dividir por párrafos
    parrafos = texto.split('\n\n')
    chunks = []
    chunk_actual = ""
    
    for parrafo in parrafos:
        if len(chunk_actual) + len(parrafo) < max_chars:
            chunk_actual += parrafo + "\n\n"
        else:
            if chunk_actual:
                chunks.append(chunk_actual)
            chunk_actual = parrafo + "\n\n"
    
    if chunk_actual:
        chunks.append(chunk_actual)
    
    return chunks


def analizar_texto_con_ia(texto: str, nombre_pdf: str) -> Dict[str, Any]:
    """Usar Ollama para extraer información estructurada del texto"""
    
    # Dividir si es muy largo
    chunks = dividir_texto_en_chunks(texto, max_chars=15000)
    
    if len(chunks) > 1:
        print(f"  🔍 Analizando {len(chunks)} secciones con IA...")
    else:
        print(f"  🔍 Analizando texto con IA...")
    
    # Lista de áreas para el prompt
    areas_lista = "\n".join([f"- {codigo}: {nombre}" for codigo, nombre in AREAS_MUSEO.items()])
    
    informacion_extraida = {
        "areas": {},
        "general": []
    }
    
    for i, chunk in enumerate(chunks, 1):
        if len(chunks) > 1:
            print(f"     Sección {i}/{len(chunks)}...")
        
        prompt = f"""Eres un experto analizando documentación del Museo Pumapungo de Cuenca, Ecuador.

ÁREAS DEL MUSEO:
{areas_lista}

TEXTO A ANALIZAR:
{chunk[:12000]}  # Limitar tamaño

TAREA: Extrae información relevante y clasifícala por área del museo.

RESPONDE SOLO CON JSON VÁLIDO (sin texto adicional):

{{
  "areas_identificadas": [
    {{
      "area_codigo": "SPN",
      "segmentos_texto": [
        "Texto relevante encontrado sobre esta área...",
        "Otro segmento relevante..."
      ],
      "temas": ["tema1", "tema2"],
      "objetos_mencionados": ["objeto1", "objeto2"],
      "datos_historicos": ["dato1", "dato2"]
    }}
  ],
  "informacion_general": [
    "Información que no corresponde a ningún área específica"
  ]
}}

REGLAS:
1. Solo JSON válido, sin texto antes o después
2. Solo incluye información que realmente aparece en el texto
3. Identifica claramente a qué área pertenece cada información
4. Si no estás seguro del área, ponlo en "informacion_general"
"""
        
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODELO,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Más determinístico
                        "num_predict": 4000
                    }
                },
                timeout=300  # 5 minutos
            )
            
            if response.status_code == 200:
                resultado = response.json()
                respuesta_ia = resultado.get("response", "")
                
                # Extraer JSON
                try:
                    # Intentar parsear directamente
                    data = json.loads(respuesta_ia)
                except:
                    # Buscar JSON dentro del texto
                    match = re.search(r'\{.*\}', respuesta_ia, re.DOTALL)
                    if match:
                        data = json.loads(match.group(0))
                    else:
                        print(f"     ⚠️ No se pudo extraer JSON de la sección {i}")
                        continue
                
                # Agregar información extraída
                if "areas_identificadas" in data:
                    for area_info in data["areas_identificadas"]:
                        codigo = area_info.get("area_codigo")
                        if codigo in AREAS_MUSEO:
                            if codigo not in informacion_extraida["areas"]:
                                informacion_extraida["areas"][codigo] = {
                                    "nombre": AREAS_MUSEO[codigo],
                                    "segmentos": [],
                                    "temas": [],
                                    "objetos": [],
                                    "datos_historicos": []
                                }
                            
                            # Agregar información
                            informacion_extraida["areas"][codigo]["segmentos"].extend(
                                area_info.get("segmentos_texto", [])
                            )
                            informacion_extraida["areas"][codigo]["temas"].extend(
                                area_info.get("temas", [])
                            )
                            informacion_extraida["areas"][codigo]["objetos"].extend(
                                area_info.get("objetos_mencionados", [])
                            )
                            informacion_extraida["areas"][codigo]["datos_historicos"].extend(
                                area_info.get("datos_historicos", [])
                            )
                
                if "informacion_general" in data:
                    informacion_extraida["general"].extend(data["informacion_general"])
                
                print(f"     ✅ Sección {i} analizada")
            
            else:
                print(f"     ❌ Error en API: {response.status_code}")
        
        except Exception as e:
            print(f"     ❌ Error analizando sección {i}: {e}")
            continue
    
    return informacion_extraida


def procesar_todos_los_pdfs():
    """Procesar todos los PDFs de la carpeta"""
    
    print("=" * 80)
    print("🏛️  PROCESADOR DE PDFs - MUSEO PUMAPUNGO")
    print("=" * 80)
    print()
    
    # Verificar carpeta
    if not os.path.exists(CARPETA_PDFS):
        print(f"❌ La carpeta no existe: {CARPETA_PDFS}")
        print(f"   Crea la carpeta y pon los PDFs ahí")
        return
    
    # Buscar PDFs
    pdfs = list(Path(CARPETA_PDFS).glob("*.pdf"))
    
    if not pdfs:
        print(f"❌ No se encontraron PDFs en: {CARPETA_PDFS}")
        return
    
    print(f"📚 Encontrados {len(pdfs)} PDFs")
    print()
    
    # Verificar Ollama
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code != 200:
            print("❌ Ollama no está corriendo")
            print("   Inicia Ollama primero")
            return
        print("✅ Ollama conectado")
    except:
        print("❌ No se puede conectar con Ollama")
        print("   Asegúrate de que Ollama esté corriendo")
        return
    
    print()
    print("🚀 Iniciando procesamiento...")
    print()
    
    # Base de conocimiento
    knowledge_base = {
        "museo": "Museo Pumapungo",
        "ubicacion": "Cuenca, Ecuador",
        "fecha_procesamiento": datetime.now().isoformat(),
        "total_pdfs": len(pdfs),
        "areas": {}
    }
    
    # Inicializar áreas
    for codigo, nombre in AREAS_MUSEO.items():
        knowledge_base["areas"][codigo] = {
            "codigo": codigo,
            "nombre": nombre,
            "descripcion": "",
            "historia": "",
            "objetos_destacados": [],
            "datos_curiosos": [],
            "temas_principales": [],
            "informacion_detallada": []
        }
    
    # Procesar cada PDF
    for i, pdf_path in enumerate(pdfs, 1):
        print(f"📖 PDF {i}/{len(pdfs)}: {pdf_path.name}")
        print("-" * 80)
        
        # Extraer texto
        texto = extraer_texto_pdf(str(pdf_path))
        
        if not texto or len(texto) < 100:
            print("  ⚠️ PDF vacío o sin texto extraíble")
            print()
            continue
        
        # Analizar con IA
        info_extraida = analizar_texto_con_ia(texto, pdf_path.name)
        
        # Agregar a knowledge base
        for codigo, area_info in info_extraida["areas"].items():
            if codigo in knowledge_base["areas"]:
                knowledge_base["areas"][codigo]["informacion_detallada"].extend(
                    area_info["segmentos"]
                )
                knowledge_base["areas"][codigo]["objetos_destacados"].extend(
                    area_info["objetos"]
                )
                knowledge_base["areas"][codigo]["datos_curiosos"].extend(
                    area_info["datos_historicos"]
                )
                knowledge_base["areas"][codigo]["temas_principales"].extend(
                    area_info["temas"]
                )
        
        print()
    
    # Limpiar duplicados
    print("🧹 Limpiando duplicados...")
    for codigo in knowledge_base["areas"]:
        area = knowledge_base["areas"][codigo]
        area["objetos_destacados"] = list(set(area["objetos_destacados"]))
        area["datos_curiosos"] = list(set(area["datos_curiosos"]))
        area["temas_principales"] = list(set(area["temas_principales"]))
    
    # Guardar resultado
    print(f"💾 Guardando resultado en: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 80)
    print("✅ PROCESAMIENTO COMPLETADO")
    print("=" * 80)
    print()
    print(f"📊 Resumen:")
    print(f"   - PDFs procesados: {len(pdfs)}")
    print(f"   - Áreas con información:")
    for codigo, area in knowledge_base["areas"].items():
        total_info = (
            len(area["informacion_detallada"]) +
            len(area["objetos_destacados"]) +
            len(area["datos_curiosos"])
        )
        if total_info > 0:
            print(f"     • {codigo} - {area['nombre']}: {total_info} items")
    
    print()
    print(f"📁 Archivo generado: {OUTPUT_FILE}")
    print(f"   Cópialo a tu carpeta del backend para usarlo en el sistema")
    print()


if __name__ == "__main__":
    procesar_todos_los_pdfs()