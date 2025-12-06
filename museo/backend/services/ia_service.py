# services/ia_service.py
# Servicio de IA Generativa para itinerarios personalizados
# Sistema Museo Pumapungo

import requests
import json
import logging
from typing import List, Dict, Any, Optional
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class IAGenerativaService:
    """
    Servicio para generar itinerarios personalizados usando Ollama/DeepSeek
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
        tiempo_disponible: int,
        nivel_detalle: str,
        areas_disponibles: List[Dict[str, Any]],
        incluir_descansos: bool = True
    ) -> str:
        """
        Construir prompt personalizado para generar itinerario
        """
        # Formatear áreas disponibles
        areas_info = []
        for area in areas_disponibles:
            info = f"""
- {area['nombre']} ({area['codigo']})
  Categoría: {area['categoria']}
  Subcategoría: {area.get('subcategoria', 'N/A')}
  Descripción: {area.get('descripcion', 'Sin descripción')}
  Tiempo recomendado: {area['tiempo_minimo']}-{area['tiempo_maximo']} minutos
  Ubicación: Piso {area.get('piso', 1)}, Zona {area.get('zona', 'central')}
"""
            areas_info.append(info)
        
        areas_texto = "\n".join(areas_info)
        
        # Construir el prompt según nivel de detalle
        if nivel_detalle == "rapido":
            detalle_instruccion = "Crea un recorrido conciso y directo, priorizando las áreas más importantes."
        elif nivel_detalle == "profundo":
            detalle_instruccion = "Crea un recorrido detallado con contexto histórico, datos curiosos y recomendaciones específicas para cada área."
        else:  # normal
            detalle_instruccion = "Crea un recorrido equilibrado con información interesante pero no abrumadora."
        
        descansos_texto = "Incluye sugerencias de descansos entre áreas." if incluir_descansos else "No es necesario incluir descansos."
        
        prompt = f"""Eres un guía experto del Museo Pumapungo en Cuenca, Ecuador. Tu tarea es crear un itinerario personalizado para un visitante.

**INFORMACIÓN DEL VISITANTE:**
- Nombre: {visitante_nombre}
- Intereses principales: {', '.join(intereses)}
- Tiempo disponible: {tiempo_disponible} minutos
- Nivel de detalle deseado: {nivel_detalle}

**ÁREAS DISPONIBLES DEL MUSEO:**
{areas_texto}

**INSTRUCCIONES:**
1. Selecciona las áreas MÁS RELEVANTES según los intereses del visitante
2. Organiza el recorrido de forma lógica y eficiente
3. Respeta el tiempo disponible ({tiempo_disponible} minutos)
4. {detalle_instruccion}
5. {descansos_texto}
6. Crea títulos atractivos y descripciones envolventes

**IMPORTANTE:** Responde SOLO con un JSON válido en este formato exacto:
{{
  "titulo": "Título atractivo del itinerario (máximo 100 caracteres)",
  "descripcion": "Descripción narrativa general del recorrido (200-300 palabras)",
  "duracion_total": número_en_minutos,
  "areas": [
    {{
      "area_codigo": "código del área (ej: ARQ-01)",
      "orden": número_de_orden,
      "tiempo_sugerido": minutos,
      "introduccion": "Introducción contextual para esta área (100-150 palabras)",
      "puntos_clave": ["punto 1", "punto 2", "punto 3"],
      "recomendacion": "Recomendación específica para aprovechar esta área"
    }}
  ]
}}

Genera el itinerario ahora:"""

        return prompt
    
    def generar_itinerario(
        self,
        visitante_nombre: str,
        intereses: List[str],
        tiempo_disponible: int,
        nivel_detalle: str,
        areas_disponibles: List[Dict[str, Any]],
        incluir_descansos: bool = True
    ) -> Dict[str, Any]:
        """
        Generar itinerario personalizado usando Ollama/DeepSeek
        
        Returns:
            Dict con estructura:
            {
                "titulo": str,
                "descripcion": str,
                "duracion_total": int,
                "areas": List[Dict],
                "metadata": {
                    "prompt": str,
                    "modelo": str,
                    "respuesta_cruda": str
                }
            }
        """
        try:
            # Construir prompt
            prompt = self._construir_prompt_itinerario(
                visitante_nombre,
                intereses,
                tiempo_disponible,
                nivel_detalle,
                areas_disponibles,
                incluir_descansos
            )
            
            logger.info(f"🤖 Generando itinerario para {visitante_nombre} con IA...")
            logger.debug(f"Prompt: {prompt[:200]}...")
            
            # Llamar a Ollama
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": 2000  # Máximo tokens
                    }
                },
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            # Extraer respuesta
            resultado = response.json()
            respuesta_ia = resultado.get("response", "")
            
            logger.debug(f"Respuesta IA: {respuesta_ia[:200]}...")
            
            # Parsear JSON de la respuesta
            itinerario_json = self._extraer_json(respuesta_ia)
            
            # Validar estructura
            if not self._validar_itinerario(itinerario_json):
                raise ValueError("El itinerario generado no tiene la estructura correcta")
            
            # Agregar metadata
            itinerario_json["metadata"] = {
                "prompt": prompt,
                "modelo": self.model,
                "respuesta_cruda": respuesta_ia,
                "temperature": self.temperature
            }
            
            logger.info(f"✅ Itinerario generado exitosamente: {itinerario_json['titulo']}")
            
            return itinerario_json
        
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout al conectar con Ollama")
            raise Exception("El servicio de IA tardó demasiado en responder")
        
        except requests.exceptions.ConnectionError:
            logger.error("❌ No se pudo conectar con Ollama")
            raise Exception(f"No se pudo conectar con Ollama en {self.base_url}")
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error al parsear JSON de la IA: {e}")
            raise Exception("La IA no generó un JSON válido")
        
        except Exception as e:
            logger.error(f"❌ Error al generar itinerario: {e}")
            raise
    
    def _extraer_json(self, respuesta: str) -> Dict[str, Any]:
        """
        Extraer JSON de la respuesta de la IA
        """
        # Intentar parsear directamente
        try:
            return json.loads(respuesta)
        except:
            pass
        
        # Buscar JSON entre ```json y ```
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', respuesta, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # Buscar JSON entre { y }
        json_match = re.search(r'\{.*\}', respuesta, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        raise ValueError("No se pudo extraer JSON de la respuesta de la IA")
    
    def _validar_itinerario(self, itinerario: Dict[str, Any]) -> bool:
        """
        Validar que el itinerario tenga la estructura correcta
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
        for area in itinerario["areas"]:
            campos_area = ["area_codigo", "orden", "tiempo_sugerido", "introduccion"]
            for campo in campos_area:
                if campo not in area:
                    logger.error(f"❌ Falta campo en área: {campo}")
                    return False
        
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
    
    def generar_descripcion_area(
        self,
        area_nombre: str,
        area_descripcion: str,
        intereses_visitante: List[str]
    ) -> str:
        """
        Generar descripción personalizada de un área según intereses del visitante
        """
        prompt = f"""Como guía del Museo Pumapungo, describe brevemente el área "{area_nombre}" 
para un visitante interesado en: {', '.join(intereses_visitante)}.

Información del área: {area_descripcion}

Genera una descripción de 2-3 oraciones que conecte con sus intereses.
Responde solo con el texto, sin formato adicional."""

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.8}
                },
                timeout=30
            )
            
            response.raise_for_status()
            resultado = response.json()
            return resultado.get("response", area_descripcion).strip()
        
        except Exception as e:
            logger.error(f"Error al generar descripción: {e}")
            return area_descripcion


# Instancia global del servicio
ia_service = IAGenerativaService()