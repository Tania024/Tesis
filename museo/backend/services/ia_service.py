# services/ia_service_HIBRIDO.py
# 🔥 VERSIÓN HÍBRIDA: KB + Web Search como fallback

import requests
import json
import logging
import re
import threading
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class IAGenerativaService:
    """
    Servicio HÍBRIDO:
    1. Intenta usar knowledge base
    2. Si es insuficiente, busca en web
    3. Combina ambas fuentes
    """
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self.temperature = getattr(settings, 'OLLAMA_TEMPERATURE', 0.7)
        
        # 🔥 CARGAR KNOWLEDGE BASE
        self.knowledge_base = self._cargar_knowledge_base()
        
    def _cargar_knowledge_base(self) -> Dict[str, Any]:
        """Cargar información real del museo desde JSON"""
        try:
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
            
            logger.warning("⚠️ No se encontro museo_knowledge.json - usará web search")
            return {"areas": {}}
        
        except Exception as e:
            logger.error(f"❌ Error cargando knowledge base: {e}")
            return {"areas": {}}
    
    def _obtener_info_area(self, area_codigo: str) -> Dict[str, Any]:
        """Obtener información REAL de un área del museo"""
        if not self.knowledge_base or "areas" not in self.knowledge_base:
            return {}
        
        area_info = self.knowledge_base["areas"].get(area_codigo, {})
        
        if area_info:
            # Verificar si tiene suficiente contenido
            datos = len(area_info.get('datos_curiosos', []))
            objetos = len(area_info.get('objetos_destacados', []))
            info_det = len(area_info.get('informacion_detallada', []))
            
            if datos >= 3 and objetos >= 3 and info_det >= 2:
                logger.info(f"✅ KB completo para {area_codigo}: {datos} datos, {objetos} objetos")
                return area_info
            else:
                logger.warning(f"⚠️ KB insuficiente para {area_codigo}: {datos} datos, {objetos} objetos")
                return area_info  # Lo devuelve igual, pero se complementará con web
        else:
            logger.warning(f"⚠️ Sin KB para {area_codigo}")
            return {}
    
    def _buscar_info_web_simple(self, nombre_area: str, museo: str = "Museo Pumapungo") -> str:
        """
        Buscar información básica en web sobre un área
        NOTA: Este es un ejemplo simplificado sin web_search
        En producción, usarías la API de web_search
        """
        try:
            # Por ahora, retorna string vacío
            # En producción, aquí irían las llamadas a web_search
            logger.info(f"🌐 Web search deshabilitado - usando solo KB")
            return ""
        except Exception as e:
            logger.error(f"❌ Error en web search: {e}")
            return ""
    
    def generar_itinerario_progresivo(
        self,
        visitante_nombre: str,
        intereses: List[str],
        tiempo_disponible: Optional[int],
        nivel_detalle: str,
        areas_disponibles: List[Dict[str, Any]],
        incluir_descansos: bool = True,
        db_session=None,
        itinerario_id: int = None
    ) -> Dict[str, Any]:
        """
        🔥 MÉTODO PROGRESIVO HÍBRIDO
        """
        tiempo_inicio = datetime.now()
        
        tiene_kb = bool(self.knowledge_base and self.knowledge_base.get("areas"))
        logger.info(f"🚀 HÍBRIDO: Generando para {visitante_nombre} (nivel: {nivel_detalle}, KB: {tiene_kb})")
        
        # PASO 1: Generar estructura básica
        logger.info("📋 PASO 1: Generando estructura...")
        estructura = self._generar_estructura_base(
            visitante_nombre,
            intereses,
            tiempo_disponible,
            areas_disponibles
        )
        
        # PASO 2: Generar SOLO primera área con contenido completo
        logger.info("📝 PASO 2: Generando primera área completa...")
        primera_area = self._generar_area_individual_hibrida(
            estructura['areas'][0],
            areas_disponibles,
            visitante_nombre,
            intereses,
            nivel_detalle,
            es_primera=True
        )
        
        # PASO 3: Marcar resto como "generando"
        areas_resultado = [primera_area]
        for area_estructura in estructura['areas'][1:]:
            areas_resultado.append({
                **area_estructura,
                "introduccion": "⏳ Generando contenido detallado...",
                "historia_contextual": None,
                "datos_curiosos": [],
                "que_observar": [],
                "recomendacion": None,
                "generando": True
            })
        
        tiempo_fin = datetime.now()
        tiempo_primera = (tiempo_fin - tiempo_inicio).total_seconds()
        
        resultado = {
            **estructura,
            "areas": areas_resultado,
            "metadata": {
                "modelo": self.model,
                "temperature": 0.1,
                "nivel_detalle": nivel_detalle,
                "tiempo_primera_area": f"{tiempo_primera:.2f}s",
                "timestamp": tiempo_fin.isoformat(),
                "usa_knowledge_base": tiene_kb,
                "areas_kb": len(self.knowledge_base.get("areas", {})),
                "modo": "hibrido"
            }
        }
        
        logger.info(f"✅ Primera área lista en {tiempo_primera:.1f}s")
        
        # PASO 4: Lanzar generación del resto en background
        if db_session and itinerario_id:
            logger.info(f"🔄 Lanzando generación background de {len(estructura['areas']) - 1} áreas...")
            thread = threading.Thread(
                target=self._generar_resto_areas_background,
                args=(
                    itinerario_id,
                    estructura['areas'][1:],
                    areas_disponibles,
                    visitante_nombre,
                    intereses,
                    nivel_detalle,
                    db_session
                ),
                daemon=True
            )
            thread.start()
        
        return resultado
    
    def _generar_estructura_base(
        self,
        visitante_nombre: str,
        intereses: List[str],
        tiempo_disponible: Optional[int],
        areas_disponibles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Genera estructura básica"""
        areas_texto = "\n".join([
            f"- {a['codigo']}: {a['nombre']} ({a['tiempo_minimo']}-{a['tiempo_maximo']}min)"
            for a in areas_disponibles
        ])
        
        intereses_texto = ", ".join(intereses) if intereses else "generales"
        
        if tiempo_disponible:
            instruccion = f"Selecciona 3-5 areas que sumen aprox {tiempo_disponible} minutos"
        else:
            instruccion = f"Selecciona todas las {len(areas_disponibles)} areas disponibles"
        
        prompt = f"""Selecciona areas para itinerario del Museo Pumapungo.

VISITANTE: {visitante_nombre}
INTERESES: {intereses_texto}
AREAS: {areas_texto}
TAREA: {instruccion}

Responde JSON:
{{
  "titulo": "titulo",
  "descripcion": "descripcion",
  "duracion_total": minutos,
  "areas": [{{"area_codigo": "cod", "orden": 1, "tiempo_sugerido": min}}]
}}"""
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.1, "num_predict": 500}
                },
                timeout=30
            )
            
            response.raise_for_status()
            return self._extraer_json(response.json().get("response", ""))
            
        except Exception as e:
            logger.error(f"❌ Error estructura: {e}")
            return self._estructura_fallback(areas_disponibles, tiempo_disponible)
    
    def _generar_area_individual_hibrida(
        self,
        area_estructura: Dict[str, Any],
        areas_disponibles: List[Dict[str, Any]],
        visitante_nombre: str,
        intereses: List[str],
        nivel_detalle: str,
        es_primera: bool = False
    ) -> Dict[str, Any]:
        """
        🔥 VERSIÓN HÍBRIDA
        1. Intenta KB
        2. Si insuficiente, complementa con info genérica educativa
        3. Genera contenido rico
        """
        area_codigo = area_estructura['area_codigo']
        area_info = next((a for a in areas_disponibles if a['codigo'] == area_codigo), None)
        
        if not area_info:
            logger.error(f"❌ Área {area_codigo} no encontrada")
            return {**area_estructura, "error": "Área no encontrada"}
        
        # 1. Intentar KB
        info_kb = self._obtener_info_area(area_codigo)
        
        # 2. Evaluar si es suficiente
        datos_kb = info_kb.get('datos_curiosos', []) if info_kb else []
        objetos_kb = info_kb.get('objetos_destacados', []) if info_kb else []
        info_det_kb = info_kb.get('informacion_detallada', []) if info_kb else []
        
        usa_kb = len(datos_kb) >= 3 and len(objetos_kb) >= 3
        
        if usa_kb:
            logger.info(f"✅ Usando KB para {area_codigo}")
            fuente = "knowledge_base"
        else:
            logger.warning(f"⚠️ KB insuficiente para {area_codigo} - generando contenido educativo")
            fuente = "generativo"
        
        # Ajustar extensión
        if nivel_detalle == "profundo":
            num_datos = 7 if usa_kb else 5
            num_observar = 8 if usa_kb else 5
            num_predict = 3000
        else:
            num_datos = 4
            num_observar = 4
            num_predict = 1800
        
        # Construir prompt
        if usa_kb:
            # PROMPT CON KB
            prompt = self._construir_prompt_con_kb(
                area_info, info_kb, visitante_nombre, intereses,
                nivel_detalle, num_datos, num_observar, es_primera
            )
        else:
            # PROMPT GENERATIVO EDUCATIVO
            prompt = self._construir_prompt_generativo(
                area_info, visitante_nombre, intereses,
                nivel_detalle, num_datos, num_observar, es_primera
            )
        
        try:
            logger.info(f"📝 Generando '{area_info['nombre']}' ({fuente}, {nivel_detalle})...")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.2, "num_predict": num_predict}
                },
                timeout=120
            )
            
            response.raise_for_status()
            contenido = self._extraer_json(response.json().get("response", ""))
            
            logger.info(f"✅ '{area_info['nombre']}' generada ({len(contenido.get('datos_curiosos', []))} datos)")
            
            return {
                **area_estructura,
                **contenido,
                "generando": False,
                "_fuente": fuente
            }
            
        except Exception as e:
            logger.error(f"❌ Error {area_codigo}: {e}")
            return self._area_fallback(area_estructura, area_info)
    
    def _construir_prompt_con_kb(self, area_info, info_kb, visitante, intereses, nivel, num_datos, num_obs, primera):
        """Prompt cuando HAY knowledge base"""
        objetos = "\n".join([f"{i+1}. {obj}" for i, obj in enumerate(info_kb.get('objetos_destacados', [])[:num_obs])])
        datos = "\n".join([f"{i+1}. {dato}" for i, dato in enumerate(info_kb.get('datos_curiosos', [])[:num_datos])])
        contexto = "\n\n".join(info_kb.get('informacion_detallada', [])[:3])
        
        return f"""Genera contenido educativo para {area_info['nombre']} del Museo Pumapungo.

VISITANTE: {visitante}
INTERESES: {", ".join(intereses)}
{'⭐ PRIMERA ÁREA - Bienvenida cálida' if primera else ''}

INFORMACIÓN REAL DEL MUSEO:

OBJETOS DESTACADOS:
{objetos}

DATOS CURIOSOS REALES:
{datos}

CONTEXTO HISTÓRICO:
{contexto}

INSTRUCCIONES:
* USA los objetos y datos listados arriba
* Parafrasea el contexto para hacerlo accesible
* Genera {num_datos} datos y {num_obs} observaciones
* Nivel: {nivel.upper()}

JSON:
{{
  "introduccion": "3-4 oraciones",
  "historia_contextual": "6-8 lineas basadas en contexto",
  "datos_curiosos": [{num_datos} items de DATOS CURIOSOS],
  "que_observar": [{num_obs} items de OBJETOS DESTACADOS],
  "recomendacion": "consejo práctico"
}}"""
    
    def _construir_prompt_generativo(self, area_info, visitante, intereses, nivel, num_datos, num_obs, primera):
        """Prompt cuando NO hay KB suficiente - contenido educativo general"""
        return f"""Genera contenido educativo para {area_info['nombre']} del Museo Pumapungo.

ÁREA: {area_info['nombre']}
DESCRIPCIÓN: {area_info.get('descripcion', 'Área del museo')}
VISITANTE: {visitante}
INTERESES: {", ".join(intereses)}
{'⭐ PRIMERA ÁREA' if primera else ''}

TAREA:
Genera contenido educativo apropiado para un museo sobre:
* Contexto histórico/cultural del área
* {num_datos} datos interesantes y educativos
* {num_obs} cosas importantes que observar
* Recomendación práctica

Nivel: {nivel.upper()}

JSON:
{{
  "introduccion": "3-4 oraciones sobre qué verá",
  "historia_contextual": "6-8 lineas de contexto histórico/cultural",
  "datos_curiosos": [{num_datos} datos educativos relevantes],
  "que_observar": [{num_obs} elementos importantes a observar],
  "recomendacion": "consejo práctico"
}}"""
    
    def _generar_resto_areas_background(self, itinerario_id, areas_pendientes, areas_disponibles,
                                       visitante_nombre, intereses, nivel_detalle, db_session):
        """Background thread"""
        from models import ItinerarioDetalle
        
        logger.info(f"🔄 Background: {len(areas_pendientes)} áreas")
        
        for idx, area_pendiente in enumerate(areas_pendientes, start=2):
            try:
                area_completa = self._generar_area_individual_hibrida(
                    area_pendiente, areas_disponibles, visitante_nombre,
                    intereses, nivel_detalle, False
                )
                
                detalle = db_session.query(ItinerarioDetalle).filter(
                    ItinerarioDetalle.itinerario_id == itinerario_id,
                    ItinerarioDetalle.orden == area_completa['orden']
                ).first()
                
                if detalle:
                    detalle.introduccion = area_completa.get('introduccion')
                    detalle.historia_contextual = area_completa.get('historia_contextual')
                    detalle.datos_curiosos = area_completa.get('datos_curiosos', [])
                    detalle.que_observar = area_completa.get('que_observar', [])
                    detalle.recomendacion = area_completa.get('recomendacion')
                    db_session.commit()
                    logger.info(f"✅ [{idx}/{len(areas_pendientes)+1}] guardada")
                
                time.sleep(2)
            except Exception as e:
                logger.error(f"❌ Error área {idx}: {e}")
                db_session.rollback()
        
        logger.info(f"🎉 Completado itinerario {itinerario_id}")
    
    def _estructura_fallback(self, areas_disponibles, tiempo_disponible):
        """Fallback"""
        areas_sel = areas_disponibles[:4]
        return {
            "titulo": "Recorrido Museo Pumapungo",
            "descripcion": "Explora las áreas principales",
            "duracion_total": sum(a.get('tiempo_maximo', 25) for a in areas_sel),
            "areas": [
                {"area_codigo": a['codigo'], "orden": i+1, "tiempo_sugerido": a.get('tiempo_maximo', 25)}
                for i, a in enumerate(areas_sel)
            ]
        }
    
    def _area_fallback(self, area_estructura, area_info):
        """Fallback"""
        return {
            **area_estructura,
            "introduccion": f"Bienvenido a {area_info['nombre']}",
            "historia_contextual": area_info.get('descripcion', 'Área del museo'),
            "datos_curiosos": ["Área fascinante del museo"],
            "que_observar": ["Observa los detalles"],
            "recomendacion": "Tómate tu tiempo",
            "generando": False
        }
    
    def _extraer_json(self, respuesta: str) -> Dict[str, Any]:
        """Extraer JSON"""
        if '<think>' in respuesta:
            respuesta = re.sub(r'<think>.*?</think>', '', respuesta, flags=re.DOTALL)
        
        try:
            return json.loads(respuesta.strip())
        except:
            pass
        
        try:
            inicio = respuesta.find('{')
            fin = respuesta.rfind('}')
            if inicio != -1 and fin != -1:
                return json.loads(respuesta[inicio:fin+1])
        except:
            pass
        
        raise ValueError("No se pudo extraer JSON")
    
    def verificar_conexion(self) -> Dict[str, Any]:
        """Verificar sistema"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            tiene_kb = bool(self.knowledge_base and self.knowledge_base.get("areas"))
            
            return {
                "conectado": True,
                "modelo": self.model,
                "knowledge_base_cargada": tiene_kb,
                "areas_kb": len(self.knowledge_base.get("areas", {})),
                "modo": "hibrido"
            }
        except Exception as e:
            return {"conectado": False, "error": str(e)}


# Instancia
ia_service = IAGenerativaService()