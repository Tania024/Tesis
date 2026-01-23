# services/ia_service.py
# 🔥 VERSIÓN CON KNOWLEDGE BASE - USA INFORMACIÓN REAL DEL MUSEO

import requests
import json
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class IAGenerativaService:
    """
    Servicio para generar itinerarios con INFORMACIÓN REAL del museo
    """
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self.temperature = getattr(settings, 'OLLAMA_TEMPERATURE', 0.7)
        
        # 🔥 CARGAR KNOWLEDGE BASE
        self.knowledge_base = self._cargar_knowledge_base()
        
    def _cargar_knowledge_base(self) -> Dict[str, Any]:
        """
        Cargar información real del museo desde JSON
        """
        try:
            # Buscar en varias ubicaciones
            posibles_rutas = [
                Path("museo_knowledge.json"),
                Path("../museo_knowledge.json"),
                Path(__file__).parent.parent / "museo_knowledge.json",
            ]
            
            for ruta in posibles_rutas:
                if ruta.exists():
                    logger.info(f"📚 Cargando knowledge base: {ruta}")
                    with open(ruta, 'r', encoding='utf-8') as f:
                        kb = json.load(f)
                    
                    areas_count = len(kb.get('areas', {}))
                    logger.info(f"✅ Knowledge base cargada: {areas_count} areas")
                    return kb
            
            logger.warning("⚠️ No se encontro museo_knowledge.json")
            logger.warning("   El sistema usara modo SIN knowledge base")
            return {"areas": {}}
        
        except Exception as e:
            logger.error(f"❌ Error cargando knowledge base: {e}")
            return {"areas": {}}
    
    def _obtener_info_area(self, area_codigo: str) -> Dict[str, Any]:
        """
        Obtener información REAL de un área del museo
        """
        if not self.knowledge_base or "areas" not in self.knowledge_base:
            return {}
        
        # Buscar por código exacto
        area_info = self.knowledge_base["areas"].get(area_codigo, {})
        
        if area_info:
            logger.debug(f"✅ Info encontrada para {area_codigo}")
        else:
            logger.debug(f"⚠️ Sin info para {area_codigo}")
        
        return area_info
    
    def _construir_prompt_itinerario(
        self,
        visitante_nombre: str,
        intereses: List[str],
        tiempo_disponible: Optional[int],
        nivel_detalle: str,
        areas_disponibles: List[Dict[str, Any]],
        incluir_descansos: bool = True
    ) -> str:
        """
        Construir prompt CON INFORMACIÓN REAL del museo
        """
        # 🔥 ENRIQUECER ÁREAS CON INFO REAL
        areas_enriquecidas = []
        tiene_kb = bool(self.knowledge_base and self.knowledge_base.get("areas"))
        
        for area in areas_disponibles:
            info_real = self._obtener_info_area(area['codigo'])
            
            if info_real and tiene_kb:
                # Preparar información concisa
                objetos = info_real.get("objetos_destacados", [])[:3]
                objetos_texto = ", ".join(objetos) if objetos else "Coleccion variada"
                
                datos = info_real.get("datos_curiosos", [])[:2]
                datos_texto = ". ".join(datos) if datos else "Area importante del museo"
                
                temas = info_real.get("temas_principales", [])[:3]
                temas_texto = ", ".join(temas) if temas else "Historia y cultura"
                
                # Información detallada (primeros 200 chars de cada segmento)
                info_detallada = info_real.get("informacion_detallada", [])
                contexto = ""
                if info_detallada:
                    # Tomar primer segmento relevante
                    for segmento in info_detallada[:2]:
                        if len(segmento) > 50:  # Solo segmentos sustanciales
                            contexto += segmento[:200] + "... "
                            break
                
                area_texto = f"""{area['codigo']}: {area['nombre']}
   Tiempo: {area['tiempo_minimo']}-{area['tiempo_maximo']} min
   Objetos destacados: {objetos_texto}
   Temas: {temas_texto}
   Contexto: {contexto if contexto else datos_texto}"""
                
                areas_enriquecidas.append(area_texto)
            else:
                # Sin KB, usar info básica
                area_texto = f"{area['codigo']}: {area['nombre']} ({area['tiempo_minimo']}-{area['tiempo_maximo']}min)"
                areas_enriquecidas.append(area_texto)
        
        areas_texto = "\n\n".join(areas_enriquecidas)
        
        # Calcular tiempo
        if tiempo_disponible is None:
            tiempo_total = sum(area['tiempo_maximo'] for area in areas_disponibles)
            instruccion = f"Incluye todas las {len(areas_disponibles)} areas"
        else:
            tiempo_total = tiempo_disponible
            instruccion = "Selecciona 3-4 areas apropiadas"
        
        # Intereses
        intereses_texto = ", ".join(intereses)
        
        # 🔥 PROMPT CON INSTRUCCIONES PARA USAR INFO REAL
        if tiene_kb:
            instruccion_kb = """
IMPORTANTE: Usa la informacion REAL proporcionada arriba sobre cada area.
- Los objetos destacados, temas y contexto son REALES del museo
- Basa tus datos curiosos y observaciones en esta informacion VERIFICADA
- NO inventes objetos o datos que no aparecen en la informacion proporcionada
"""
        else:
            instruccion_kb = ""
        
        # Construir prompt
        prompt = """Eres guia experto del Museo Pumapungo en Cuenca, Ecuador.

Crea un itinerario personalizado para """ + visitante_nombre + """.

DATOS DEL VISITANTE:
- Intereses: """ + intereses_texto + """
- Nivel: medio

AREAS DISPONIBLES DEL MUSEO (CON INFORMACION REAL):
""" + areas_texto + """

TAREA: """ + instruccion + """
""" + instruccion_kb + """

RESPONDE SOLO CON JSON VALIDO (sin texto adicional):

{
  "titulo": "Titulo atractivo del itinerario",
  "descripcion": "Descripcion breve en 3-4 oraciones",
  "duracion_total": """ + str(tiempo_total) + """,
  "areas": [
    {
      "area_codigo": "codigo_area",
      "orden": 1,
      "tiempo_sugerido": 30,
      "introduccion": "Introduccion en 2-3 lineas",
      "historia_contextual": "Historia en 3-4 lineas BASADA en la info real proporcionada",
      "datos_curiosos": [
        "Dato 1 REAL basado en la informacion del area",
        "Dato 2 REAL basado en objetos o temas mencionados",
        "Dato 3 REAL del contexto historico proporcionado"
      ],
      "que_observar": [
        "Observacion 1 sobre objetos REALES mencionados",
        "Observacion 2 sobre elementos verificados",
        "Observacion 3 relacionada con los temas listados"
      ],
      "recomendacion": "Recomendacion practica en 1-2 lineas"
    }
  ]
}

REGLAS:
1. SOLO JSON sin texto extra
2. USA la informacion REAL proporcionada
3. NO inventes objetos o datos no mencionados
4. Contenido breve pero PRECISO
"""
        
        return prompt
    
    def generar_itinerario(
        self,
        visitante_nombre: str,
        intereses: List[str],
        tiempo_disponible: Optional[int],
        nivel_detalle: str,
        areas_disponibles: List[Dict[str, Any]],
        incluir_descansos: bool = True
    ) -> Dict[str, Any]:
        """
        Generar itinerario CON información REAL
        """
        try:
            tiempo_inicio = datetime.now()
            
            tiene_kb = bool(self.knowledge_base and self.knowledge_base.get("areas"))
            
            if tiene_kb:
                logger.info(f"🚀 Generando itinerario CON knowledge base para {visitante_nombre}")
            else:
                logger.info(f"🚀 Generando itinerario SIN knowledge base para {visitante_nombre}")
            
            # Construir prompt
            prompt = self._construir_prompt_itinerario(
                visitante_nombre,
                intereses,
                tiempo_disponible,
                nivel_detalle,
                areas_disponibles,
                incluir_descansos
            )
            
            logger.info(f"✅ Prompt construido: {len(prompt)} chars")
            
            # Configuracion
            if tiempo_disponible is None:
                num_predict = 3000
            else:
                num_predict = 2000
            
            logger.info(f"🎯 Config: {num_predict} tokens, temp=0.1")
            
            # Llamar a Ollama
            logger.info(f"📡 Enviando request a Ollama...")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.1,
                        "num_predict": num_predict,
                        "top_p": 0.9,
                        "top_k": 40
                    }
                },
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            # Extraer respuesta
            resultado = response.json()
            respuesta_ia = resultado.get("response", "")
            
            tiempo_fin = datetime.now()
            tiempo_generacion = (tiempo_fin - tiempo_inicio).total_seconds()
            
            logger.info(f"⚡ Respuesta en {tiempo_generacion:.1f}s")
            
            # Extraer JSON
            itinerario_json = self._extraer_json(respuesta_ia)
            
            # Validar
            if not self._validar_itinerario(itinerario_json):
                raise ValueError("Estructura incorrecta")
            
            # 🔥 METADATA CON INFO DE KNOWLEDGE BASE
            itinerario_json["metadata"] = {
                "prompt": prompt,
                "modelo": self.model,
                "respuesta_cruda": respuesta_ia,
                "temperature": 0.1,
                "tiempo_generacion": f"{tiempo_generacion:.2f}s",
                "timestamp": tiempo_fin.isoformat(),
                "usa_knowledge_base": tiene_kb,  # 🔥 NUEVO
                "areas_kb": len(self.knowledge_base.get("areas", {}))  # 🔥 NUEVO
            }
            
            logger.info(f"✅ Itinerario generado: {itinerario_json['titulo']}")
            if tiene_kb:
                logger.info(f"   📚 Usando informacion REAL de {len(self.knowledge_base.get('areas', {}))} areas")
            
            return itinerario_json
        
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _extraer_json(self, respuesta: str) -> Dict[str, Any]:
        """
        Extraer JSON de forma robusta
        """
        # Limpiar tags
        if '<think>' in respuesta:
            respuesta = re.sub(r'<think>.*?</think>', '', respuesta, flags=re.DOTALL | re.IGNORECASE)
        
        # Intentar parsear directo
        try:
            return json.loads(respuesta.strip())
        except:
            pass
        
        # Buscar entre llaves
        try:
            inicio = respuesta.find('{')
            fin = respuesta.rfind('}')
            if inicio != -1 and fin != -1:
                json_str = respuesta[inicio:fin+1]
                return json.loads(json_str)
        except:
            pass
        
        # Buscar en bloques
        try:
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', respuesta, re.DOTALL)
            if match:
                return json.loads(match.group(1).strip())
        except:
            pass
        
        logger.error(f"❌ No se pudo extraer JSON: {respuesta[:300]}")
        raise ValueError("No se pudo extraer JSON")
    
    def _validar_itinerario(self, itinerario: Dict[str, Any]) -> bool:
        """
        Validar estructura basica
        """
        campos = ["titulo", "descripcion", "duracion_total", "areas"]
        
        for campo in campos:
            if campo not in itinerario:
                logger.error(f"❌ Falta: {campo}")
                return False
        
        if not isinstance(itinerario["areas"], list) or len(itinerario["areas"]) == 0:
            logger.error("❌ Areas vacio")
            return False
        
        return True
    
    def verificar_conexion(self) -> Dict[str, Any]:
        """
        Verificar Ollama y Knowledge Base
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            modelos = response.json().get("models", [])
            modelos_nombres = [m.get("name") for m in modelos]
            
            tiene_kb = bool(self.knowledge_base and self.knowledge_base.get("areas"))
            num_areas_kb = len(self.knowledge_base.get("areas", {}))
            
            return {
                "conectado": True,
                "url": self.base_url,
                "modelo_configurado": self.model,
                "modelo_disponible": self.model in modelos_nombres,
                "modelos_instalados": modelos_nombres,
                "knowledge_base_cargada": tiene_kb,
                "areas_en_knowledge_base": num_areas_kb
            }
        except Exception as e:
            return {
                "conectado": False,
                "error": str(e),
                "url": self.base_url,
                "knowledge_base_cargada": False
            }


# Instancia global
ia_service = IAGenerativaService()