# services/ia_service.py

import requests
import json
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class IAGenerativaService:
    """
    Servicio para generar itinerarios personalizados con CONTENIDO EXTENSO
    """
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self.temperature = getattr(settings, 'OLLAMA_TEMPERATURE', 0.7)
        
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
        Construir prompt para generar itinerario con CONTENIDO EXTENSO
        """
        # Formatear áreas
        areas_lista = []
        for area in areas_disponibles:
            areas_lista.append(
                f"{area['codigo']}: {area['nombre']} "
                f"({area['tiempo_minimo']}-{area['tiempo_maximo']}min, "
                f"Piso {area.get('piso', 1)})"
            )
        
        areas_texto = "\n".join(areas_lista)
        
        # Determinar instrucciones
        if tiempo_disponible is None:
            cantidad_areas = len(areas_disponibles)
            tiempo_instruccion = f"Incluye las {cantidad_areas} áreas disponibles"
            tiempo_total = sum(area['tiempo_maximo'] for area in areas_disponibles)
        else:
            cantidad_areas = "3-4"
            tiempo_instruccion = f"Selecciona {cantidad_areas} áreas que se ajusten a {tiempo_disponible} minutos"
            tiempo_total = tiempo_disponible
        
        # Determinar nivel de detalle
        if nivel_detalle == "profundo":
            detalle_texto = "MUY DETALLADO con MÁXIMA información"
            lineas_historia = "7-10 líneas"
            num_datos = 5
            num_observar = 5
        else:  # normal o rápido
            detalle_texto = "DETALLADO con BUENA información"
            lineas_historia = "5-7 líneas"
            num_datos = 4
            num_observar = 4
        
        # 🔥 PROMPT MEJORADO para contenido EXTENSO
        prompt = f"""Eres un guía experto del Museo Pumapungo. Crea un itinerario EXTENSO para {visitante_nombre}.

INFORMACIÓN:
- Intereses: {', '.join(intereses)}
- Nivel: {detalle_texto}

ÁREAS DISPONIBLES:
{areas_texto}

TAREA: {tiempo_instruccion}

IMPORTANTE - RESPONDE SOLO CON JSON VÁLIDO (sin texto adicional):

{{
  "titulo": "Título atractivo del itinerario",
  "descripcion": "Descripción del recorrido en 4-5 oraciones completas que enganche al visitante. Explica qué verá y por qué es especial.",
  "duracion_total": {tiempo_total},
  "areas": [
    {{
      "area_codigo": "codigo_del_area",
      "orden": 1,
      "tiempo_sugerido": minutos_recomendados,
      "introduccion": "Introducción de 2-3 oraciones sobre esta área",
      "historia_contextual": "Párrafo EXTENSO de {lineas_historia} sobre la historia y contexto. Explica la época, la cultura, fechas importantes, y por qué es significativa. Usa narrativa envolvente que transporte al visitante.",
      "datos_curiosos": [
        "Primer dato curioso de 2-3 líneas con información fascinante y específica",
        "Segundo dato curioso de 2-3 líneas sobre algo sorprendente",
        "Tercer dato curioso de 2-3 líneas de anécdota memorable",
        "Cuarto dato curioso de 2-3 líneas de contexto interesante"{"," if num_datos > 4 else ""}
        {"Quinto dato curioso de 2-3 líneas si el nivel es profundo" if num_datos > 4 else ""}
      ],
      "que_observar": [
        "Primera cosa específica que observar con 2-3 líneas explicando qué buscar y por qué es importante",
        "Segunda observación específica con 2-3 líneas de detalles técnicos o artísticos",
        "Tercera observación con 2-3 líneas sobre elementos únicos",
        "Cuarta observación con 2-3 líneas de contexto visual"{"," if num_observar > 4 else ""}
        {"Quinta observación con 2-3 líneas si el nivel es profundo" if num_observar > 4 else ""}
      ],
      "recomendacion": "Consejo específico de 2-3 líneas para aprovechar mejor esta área"
    }}
  ]
}}

REGLAS CRÍTICAS:
1. NO escribas texto antes del JSON
2. NO escribas texto después del JSON
3. NO uses ```json o ```
4. SOLO el objeto JSON puro
5. historia_contextual debe ser un párrafo LARGO de {lineas_historia}
6. datos_curiosos y que_observar deben tener {num_datos} y {num_observar} items respectivamente
7. Cada item debe tener 2-3 líneas de contenido REAL (no genérico)
8. NO uses saltos de línea dentro de los strings"""

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
        Generar itinerario personalizado con CONTENIDO EXTENSO
        """
        try:
            tiempo_inicio = datetime.now()
            
            # Construir prompt
            prompt = self._construir_prompt_itinerario(
                visitante_nombre,
                intereses,
                tiempo_disponible,
                nivel_detalle,
                areas_disponibles,
                incluir_descansos
            )
            
            logger.info(f"🤖 Generando itinerario EXTENSO para {visitante_nombre}...")
            logger.info(f"⏱️ Timeout: {self.timeout}s")
            
            # Llamar a Ollama con más tokens

            num_areas = len(areas_disponibles)
            if tiempo_disponible is None:
                # Sin límite: todas las áreas (8), necesita más tokens
                num_predict = 16000  # Suficiente para 8 áreas con contenido extenso
                temperature = 0.3    # Más consistente
            else:
                # Con límite: 3-4 áreas
                num_predict = 6000   # Suficiente para 3-4 áreas
                temperature = 0.2
            
            logger.info(f"🎯 Configuración: {num_areas} áreas, {num_predict} tokens, temp={temperature}")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": num_predict,  
                        "top_p": 0.9,
                        "top_k": 40,
                        "repeat_penalty": 1.1
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
            
            logger.info(f"📄 Respuesta recibida en {tiempo_generacion:.1f}s ({len(respuesta_ia)} chars)")
            
            # 🔥 GUARDAR RESPUESTA CRUDA PARA DEBUG
            logger.info("=" * 80)
            logger.info("📄 RESPUESTA CRUDA DE LA IA:")
            logger.info(respuesta_ia[:500] + "..." if len(respuesta_ia) > 500 else respuesta_ia)
            logger.info("=" * 80)
            
            # Extraer JSON
            itinerario_json = self._extraer_json(respuesta_ia)
            
            # Validar estructura
            if not self._validar_itinerario(itinerario_json):
                raise ValueError("El itinerario generado no tiene la estructura correcta")
            
            # Agregar metadata
            itinerario_json["metadata"] = {
                "prompt": prompt,
                "modelo": self.model,
                "respuesta_cruda": respuesta_ia,
                "temperature": self.temperature,
                "tiempo_generacion": f"{tiempo_generacion:.2f}s",
                "timestamp": tiempo_fin.isoformat()
            }
            
            logger.info(f"✅ Itinerario generado: {itinerario_json['titulo']} ({len(itinerario_json['areas'])} áreas)")
            
            return itinerario_json
        
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout después de {self.timeout}s")
            raise Exception(f"El servicio de IA tardó más de {self.timeout} segundos")
        
        except requests.exceptions.ConnectionError:
            logger.error("❌ No se pudo conectar con Ollama")
            raise Exception(f"No se pudo conectar con Ollama en {self.base_url}")
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error al parsear JSON: {e}")
            logger.error(f"📄 Respuesta problemática: {respuesta_ia[:1000]}")
            raise Exception("La IA no generó un JSON válido. Revisa los logs del backend.")
        
        except Exception as e:
            logger.error(f"❌ Error al generar itinerario: {e}")
            raise
    
    def _extraer_json(self, respuesta: str) -> Dict[str, Any]:
        """
        Extraer JSON con múltiples estrategias robustas
        """
        logger.debug(f"🔍 Extrayendo JSON ({len(respuesta)} chars)...")
        
        # Estrategia 1: Parsear directamente
        try:
            resultado = json.loads(respuesta)
            logger.info("✅ JSON parseado directamente")
            return resultado
        except:
            pass
        
        # Estrategia 2: Limpiar espacios
        try:
            respuesta_limpia = respuesta.strip()
            resultado = json.loads(respuesta_limpia)
            logger.info("✅ JSON parseado después de strip()")
            return resultado
        except:
            pass
        
        # Estrategia 3: Buscar entre ```json y ```
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', respuesta, re.DOTALL | re.IGNORECASE)
            if json_match:
                json_str = json_match.group(1).strip()
                resultado = json.loads(json_str)
                logger.info("✅ JSON extraído de ```json")
                return resultado
        except Exception as e:
            logger.debug(f"Estrategia 3 falló: {e}")
        
        # Estrategia 4: Buscar entre { y }
        try:
            inicio = respuesta.find('{')
            fin = respuesta.rfind('}')
            if inicio != -1 and fin != -1 and fin > inicio:
                json_str = respuesta[inicio:fin+1]
                resultado = json.loads(json_str)
                logger.info("✅ JSON extraído buscando { y }")
                return resultado
        except Exception as e:
            logger.debug(f"Estrategia 4 falló: {e}")
        
        # Si TODO falla
        logger.error("=" * 80)
        logger.error("❌ NO SE PUDO EXTRAER JSON")
        logger.error("=" * 80)
        logger.error("📄 RESPUESTA COMPLETA:")
        logger.error(respuesta)
        logger.error("=" * 80)
        
        raise ValueError("No se pudo extraer JSON de la respuesta de la IA")
    
    def _validar_itinerario(self, itinerario: Dict[str, Any]) -> bool:
        """
        Validar estructura del itinerario con campos EXTENSOS
        """
        campos_requeridos = ["titulo", "descripcion", "duracion_total", "areas"]
        
        for campo in campos_requeridos:
            if campo not in itinerario:
                logger.error(f"❌ Falta campo requerido: {campo}")
                return False
        
        if not isinstance(itinerario["areas"], list) or len(itinerario["areas"]) == 0:
            logger.error("❌ El campo 'areas' debe ser una lista no vacía")
            return False
        
        # Validar cada área
        for i, area in enumerate(itinerario["areas"]):
            campos_basicos = ["area_codigo", "orden", "tiempo_sugerido", "introduccion"]
            for campo in campos_basicos:
                if campo not in area:
                    logger.error(f"❌ Falta campo básico en área {i+1}: {campo}")
                    return False
            
            # Validar campos extendidos
            campos_extendidos = ["historia_contextual", "datos_curiosos", "que_observar", "recomendacion"]
            campos_presentes = sum(1 for campo in campos_extendidos if campo in area)
            
            if campos_presentes < 2:
                logger.warning(f"⚠️ Área {i+1} tiene poco contenido extendido ({campos_presentes}/4 campos)")
            
            # Validar tipos
            if "datos_curiosos" in area:
                if not isinstance(area["datos_curiosos"], list):
                    logger.error(f"❌ 'datos_curiosos' debe ser lista en área {i+1}")
                    return False
                elif len(area["datos_curiosos"]) < 3:
                    logger.warning(f"⚠️ 'datos_curiosos' tiene pocos items en área {i+1}")
            
            if "que_observar" in area:
                if not isinstance(area["que_observar"], list):
                    logger.error(f"❌ 'que_observar' debe ser lista en área {i+1}")
                    return False
                elif len(area["que_observar"]) < 3:
                    logger.warning(f"⚠️ 'que_observar' tiene pocos items en área {i+1}")
        
        logger.info(f"✅ Itinerario validado: {len(itinerario['areas'])} áreas")
        return True
    
    def verificar_conexion(self) -> Dict[str, Any]:
        """
        Verificar conexión con Ollama
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            response.raise_for_status()
            
            modelos = response.json().get("models", [])
            modelos_nombres = [m.get("name") for m in modelos]
            
            modelo_disponible = self.model in modelos_nombres
            
            return {
                "conectado": True,
                "url": self.base_url,
                "modelo_configurado": self.model,
                "modelo_disponible": modelo_disponible,
                "modelos_instalados": modelos_nombres
            }
        
        except Exception as e:
            return {
                "conectado": False,
                "error": str(e),
                "url": self.base_url
            }


# Instancia global del servicio
ia_service = IAGenerativaService()