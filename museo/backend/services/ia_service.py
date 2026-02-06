# services/ia_service.py
# 🔥 VERSIÓN HÍBRIDA: Ollama (local) + DeepSeek API (producción)
# Usa AI_PROVIDER del .env para elegir el proveedor

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
    Servicio HÍBRIDO con soporte dual:
    - AI_PROVIDER=ollama  → Usa Ollama local (desarrollo)
    - AI_PROVIDER=deepseek → Usa DeepSeek API (producción)
    """
    
    def __init__(self):
        # 🔥 NUEVO: Detectar proveedor
        self.provider = getattr(settings, 'AI_PROVIDER', 'ollama').lower()
        
        if self.provider == "deepseek":
            # ============================================
            # CONFIGURACIÓN DEEPSEEK
            # ============================================
            self.api_key = settings.DEEPSEEK_API_KEY
            self.model = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')
            self.base_url = getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
            self.timeout = getattr(settings, 'AI_TIMEOUT', 420)
            self.temperature = getattr(settings, 'AI_TEMPERATURE', 0.25)
            
            if not self.api_key:
                logger.error("❌ DEEPSEEK_API_KEY no configurada!")
                raise ValueError("DEEPSEEK_API_KEY es requerida cuando AI_PROVIDER=deepseek")
            
            logger.info(f"🤖 IA Provider: DEEPSEEK API ({self.model})")
        else:
            # ============================================
            # CONFIGURACIÓN OLLAMA (por defecto)
            # ============================================
            self.base_url = settings.OLLAMA_BASE_URL
            self.model = settings.OLLAMA_MODEL
            self.timeout = settings.OLLAMA_TIMEOUT
            self.temperature = getattr(settings, 'OLLAMA_TEMPERATURE', 0.7)
            
            logger.info(f"🤖 IA Provider: OLLAMA ({self.model})")
        
        # 🔥 CARGAR KNOWLEDGE BASE (funciona con ambos proveedores)
        self.knowledge_base = self._cargar_knowledge_base()
    
    # ============================================
    # 🔥 NUEVO: MÉTODO UNIFICADO PARA LLAMAR A LA IA
    # ============================================
    
    def _llamar_ia(self, prompt: str, max_tokens: int = 1800, temperature: float = None, json_mode: bool = True) -> str:
        """
        🔥 MÉTODO CENTRAL: Llama a Ollama o DeepSeek según AI_PROVIDER
        Retorna el texto de respuesta de la IA
        """
        temp = temperature if temperature is not None else self.temperature
        
        if self.provider == "deepseek":
            return self._llamar_deepseek(prompt, max_tokens, temp, json_mode)
        else:
            return self._llamar_ollama(prompt, max_tokens, temp, json_mode)
    
    def _llamar_deepseek(self, prompt: str, max_tokens: int, temperature: float, json_mode: bool) -> str:
        """Llamada a DeepSeek API (compatible con OpenAI)"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un guía experto del Museo Pumapungo en Cuenca, Ecuador. Responde SOLO en JSON válido, sin texto adicional, sin markdown, sin ```json."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        try:
            logger.info(f"📡 DeepSeek API: enviando request ({max_tokens} tokens max)...")
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            texto = data["choices"][0]["message"]["content"]
            tokens_usados = data.get("usage", {})
            
            logger.info(f"✅ DeepSeek respondió: {tokens_usados.get('total_tokens', '?')} tokens")
            return texto
            
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_detail = e.response.json()
            except:
                error_detail = e.response.text
            logger.error(f"❌ DeepSeek HTTP Error: {e.response.status_code} - {error_detail}")
            raise
        except Exception as e:
            logger.error(f"❌ DeepSeek Error: {e}")
            raise
    
    def _llamar_ollama(self, prompt: str, max_tokens: int, temperature: float, json_mode: bool) -> str:
        """Llamada a Ollama local"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if json_mode:
            payload["format"] = "json"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json().get("response", "")
            
        except Exception as e:
            logger.error(f"❌ Ollama Error: {e}")
            raise
    
    # ============================================
    # KNOWLEDGE BASE (sin cambios)
    # ============================================
    
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
            
            logger.warning("⚠️ No se encontró museo_knowledge.json")
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
            datos = len(area_info.get('datos_curiosos', []))
            objetos = len(area_info.get('objetos_destacados', []))
            info_det = len(area_info.get('informacion_detallada', []))
            
            if datos >= 3 and objetos >= 3 and info_det >= 2:
                logger.info(f"✅ KB completo para {area_codigo}: {datos} datos, {objetos} objetos")
                return area_info
            else:
                logger.warning(f"⚠️ KB insuficiente para {area_codigo}: {datos} datos, {objetos} objetos")
                return area_info
        else:
            logger.warning(f"⚠️ Sin KB para {area_codigo}")
            return {}
    
    # ============================================
    # GENERACIÓN PROGRESIVA (actualizado para usar _llamar_ia)
    # ============================================
    
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
        """🔥 MÉTODO PROGRESIVO HÍBRIDO — Funciona con Ollama y DeepSeek"""
        tiempo_inicio = datetime.now()
        
        tiene_kb = bool(self.knowledge_base and self.knowledge_base.get("areas"))
        logger.info(f"🚀 HÍBRIDO [{self.provider.upper()}]: Generando para {visitante_nombre} (nivel: {nivel_detalle}, KB: {tiene_kb})")
        
        # PASO 1: Generar estructura básica
        logger.info("📋 PASO 1: Generando estructura...")
        estructura = self._generar_estructura_base(
            visitante_nombre, intereses, tiempo_disponible, areas_disponibles
        )
        
        # PASO 2: Generar SOLO primera área con contenido completo
        logger.info("📝 PASO 2: Generando primera área completa...")
        primera_area = self._generar_area_individual_hibrida(
            estructura['areas'][0], areas_disponibles,
            visitante_nombre, intereses, nivel_detalle, es_primera=True
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
                "provider": self.provider,  # 🔥 NUEVO
                "temperature": 0.1,
                "nivel_detalle": nivel_detalle,
                "tiempo_primera_area": f"{tiempo_primera:.2f}s",
                "timestamp": tiempo_fin.isoformat(),
                "usa_knowledge_base": tiene_kb,
                "areas_kb": len(self.knowledge_base.get("areas", {})),
                "modo": "hibrido"
            }
        }
        
        logger.info(f"✅ Primera área lista en {tiempo_primera:.1f}s [{self.provider}]")
        
        # PASO 4: Lanzar generación del resto en background
        if db_session and itinerario_id:
            logger.info(f"🔄 Lanzando generación background de {len(estructura['areas']) - 1} áreas...")
            thread = threading.Thread(
                target=self._generar_resto_areas_background,
                args=(
                    itinerario_id, estructura['areas'][1:], areas_disponibles,
                    visitante_nombre, intereses, nivel_detalle, db_session
                ),
                daemon=True
            )
            thread.start()
        
        return resultado
    
    def _generar_estructura_base(
        self, visitante_nombre, intereses, tiempo_disponible, areas_disponibles
    ) -> Dict[str, Any]:
        """Genera estructura básica"""
        
        # SI NO HAY LÍMITE DE TIEMPO, USAR TODAS LAS ÁREAS
        if not tiempo_disponible:
            logger.info(f"✅ Sin límite de tiempo - Usando TODAS las {len(areas_disponibles)} áreas")
            
            areas_estructura = []
            duracion_total = 0
            
            for i, area in enumerate(areas_disponibles, 1):
                tiempo_area = area.get('tiempo_maximo', 25)
                areas_estructura.append({
                    "area_codigo": area['codigo'],
                    "orden": i,
                    "tiempo_sugerido": tiempo_area
                })
                duracion_total += tiempo_area
            
            return {
                "titulo": f"Recorrido Completo del Museo Pumapungo",
                "descripcion": f"Itinerario personalizado para {visitante_nombre} que explora todas las áreas del museo. Este recorrido está diseñado para satisfacer los intereses en {', '.join(intereses) if intereses else 'cultura andina'} y ofrece una experiencia bien equilibrada.",
                "duracion_total": duracion_total,
                "areas": areas_estructura
            }
        
        # SI HAY LÍMITE DE TIEMPO, USAR IA PARA SELECCIONAR
        areas_texto = "\n".join([
            f"- {a['codigo']}: {a['nombre']} ({a['tiempo_minimo']}-{a['tiempo_maximo']}min)"
            for a in areas_disponibles
        ])
        
        intereses_texto = ", ".join(intereses) if intereses else "generales"
        
        prompt = f"""Selecciona areas para itinerario del Museo Pumapungo.

VISITANTE: {visitante_nombre}
INTERESES: {intereses_texto}
AREAS: {areas_texto}
TAREA: Selecciona 3-5 areas que sumen aprox {tiempo_disponible} minutos. USA los tiempos indicados.

Responde SOLO JSON:
{{
  "titulo": "titulo",
  "descripcion": "descripcion",
  "duracion_total": minutos,
  "areas": [{{"area_codigo": "cod", "orden": 1, "tiempo_sugerido": min}}]
}}"""
        
        try:
            # 🔥 USAR MÉTODO UNIFICADO
            respuesta = self._llamar_ia(prompt, max_tokens=500, temperature=0.1)
            return self._extraer_json(respuesta)
            
        except Exception as e:
            logger.error(f"❌ Error estructura: {e}")
            return self._estructura_fallback(areas_disponibles, tiempo_disponible)

    def _generar_area_individual_hibrida(
        self, area_estructura, areas_disponibles, visitante_nombre,
        intereses, nivel_detalle, es_primera=False
    ) -> Dict[str, Any]:
        """🔥 VERSIÓN HÍBRIDA — Funciona con Ollama y DeepSeek"""
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
        
        usa_kb = len(datos_kb) >= 3 and len(objetos_kb) >= 3
        fuente = "knowledge_base" if usa_kb else "generativo"
        
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
            prompt = self._construir_prompt_con_kb(
                area_info, info_kb, visitante_nombre, intereses,
                nivel_detalle, num_datos, num_observar, es_primera
            )
        else:
            prompt = self._construir_prompt_generativo(
                area_info, visitante_nombre, intereses,
                nivel_detalle, num_datos, num_observar, es_primera
            )
        
        try:
            logger.info(f"📝 Generando '{area_info['nombre']}' ({fuente}, {nivel_detalle}) [{self.provider}]...")
            
            # 🔥 USAR MÉTODO UNIFICADO
            respuesta = self._llamar_ia(prompt, max_tokens=num_predict, temperature=0.2)
            contenido = self._extraer_json(respuesta)
            
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
        """Prompt cuando NO hay KB suficiente"""
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
        """Background thread — funciona con ambos proveedores"""
        from models import ItinerarioDetalle
        
        logger.info(f"🔄 Background [{self.provider}]: {len(areas_pendientes)} áreas")
        
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
                
                time.sleep(1)  # Menor delay con DeepSeek (es más rápido)
            except Exception as e:
                logger.error(f"❌ Error área {idx}: {e}")
                db_session.rollback()
        
        logger.info(f"🎉 Completado itinerario {itinerario_id} [{self.provider}]")
    
    # ============================================
    # UTILIDADES (sin cambios significativos)
    # ============================================
    
    def _estructura_fallback(self, areas_disponibles, tiempo_disponible):
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
        """Extraer JSON de la respuesta"""
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
        """🔥 ACTUALIZADO: Verificar conexión según proveedor"""
        tiene_kb = bool(self.knowledge_base and self.knowledge_base.get("areas"))
        
        if self.provider == "deepseek":
            try:
                # Verificar con una llamada pequeña
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                response = requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 5
                    },
                    timeout=10
                )
                response.raise_for_status()
                
                return {
                    "conectado": True,
                    "provider": "deepseek",
                    "modelo": self.model,
                    "modelo_configurado": self.model,
                    "modelo_disponible": True,
                    "knowledge_base_cargada": tiene_kb,
                    "areas_kb": len(self.knowledge_base.get("areas", {})),
                    "modo": "hibrido"
                }
            except Exception as e:
                return {
                    "conectado": False,
                    "provider": "deepseek",
                    "error": str(e),
                    "modelo_configurado": self.model,
                    "modelo_disponible": False
                }
        else:
            # Ollama
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                response.raise_for_status()
                
                modelos = response.json().get("models", [])
                modelo_disponible = any(
                    self.model in m.get("name", "") for m in modelos
                )
                
                return {
                    "conectado": True,
                    "provider": "ollama",
                    "modelo": self.model,
                    "modelo_configurado": self.model,
                    "modelo_disponible": modelo_disponible,
                    "knowledge_base_cargada": tiene_kb,
                    "areas_kb": len(self.knowledge_base.get("areas", {})),
                    "modo": "hibrido"
                }
            except Exception as e:
                return {
                    "conectado": False,
                    "provider": "ollama",
                    "error": str(e),
                    "modelo_configurado": self.model,
                    "modelo_disponible": False
                }

    def generar_itinerario(
        self, visitante_nombre, intereses, tiempo_disponible,
        nivel_detalle, areas_disponibles, incluir_descansos=True
    ) -> Dict[str, Any]:
        """Método alias para compatibilidad"""
        return self.generar_itinerario_progresivo(
            visitante_nombre=visitante_nombre,
            intereses=intereses,
            tiempo_disponible=tiempo_disponible,
            nivel_detalle=nivel_detalle,
            areas_disponibles=areas_disponibles,
            incluir_descansos=incluir_descansos,
            db_session=None,
            itinerario_id=None
        )


# Instancia
ia_service = IAGenerativaService()