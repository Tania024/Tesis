# services/google_auth_service.py

import logging
from typing import Dict, List, Optional
from urllib.parse import urlencode
import httpx

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from config import settings

logger = logging.getLogger(__name__)

class GoogleAuthService:
    """
    Servicio para autenticación OAuth con Google y extracción de datos
    Mapea intereses a los códigos exactos de áreas del museo en BD
    """
    
    # 🏛️ ÁREAS DEL MUSEO (deben coincidir EXACTAMENTE con la BD)
    AREAS_MUSEO = {
        "ARQ-01": "Sala Arqueológica Cañari",
        "ETN-01": "Sala Etnográfica",
        "AVE-01": "Aviario de Aves Andinas",
        "BOT-01": "Jardín Botánico",
        "ART-01": "Sala de Arte Colonial",
        "RUIN-01": "Parque Arqueológico Pumapungo",
        "TEMP-01": "Exhibición Temporal"
    }
    
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
        self.scopes = [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/youtube.readonly',
        ]
    
    def get_authorization_url(self, state: str = "random_state") -> str:
        """Genera URL de autorización de Google OAuth"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.scopes),
            'access_type': 'offline',
            'prompt': 'consent',
            'state': state
        }
        
        base_url = 'https://accounts.google.com/o/oauth2/v2/auth'
        auth_url = f"{base_url}?{urlencode(params)}"
        
        logger.info(f"🔗 URL de autorización generada")
        return auth_url
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """Intercambia código de autorización por access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://oauth2.googleapis.com/token',
                    data={
                        'code': code,
                        'client_id': self.client_id,
                        'client_secret': self.client_secret,
                        'redirect_uri': self.redirect_uri,
                        'grant_type': 'authorization_code'
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Error intercambiando código: {response.text}")
                
                token_data = response.json()
                logger.info(f"✅ Token de Google obtenido exitosamente")
                
                return {
                    'access_token': token_data['access_token'],
                    'refresh_token': token_data.get('refresh_token'),
                    'expires_in': token_data.get('expires_in', 3600),
                    'token_type': token_data.get('token_type', 'Bearer')
                }
                
        except Exception as e:
            logger.error(f"❌ Error intercambiando código: {e}")
            raise
    
    async def get_user_profile(self, access_token: str) -> Dict:
        """Obtiene información básica del perfil de Google"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://www.googleapis.com/oauth2/v2/userinfo',
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                
                if response.status_code != 200:
                    raise Exception(f"Error obteniendo perfil: {response.text}")
                
                profile = response.json()
                logger.info(f"✅ Perfil de Google obtenido: {profile.get('name')}")
                
                return {
                    'google_id': profile.get('id'),
                    'email': profile.get('email'),
                    'name': profile.get('name'),
                    'given_name': profile.get('given_name'),
                    'family_name': profile.get('family_name'),
                    'picture': profile.get('picture'),
                    'verified_email': profile.get('verified_email', False)
                }
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo perfil: {e}")
            raise
    
    async def get_youtube_subscriptions(self, access_token: str) -> Dict:
        """Obtiene las subscripciones de YouTube del usuario"""
        try:
            credentials = Credentials(token=access_token)
            youtube = build('youtube', 'v3', credentials=credentials)
            
            request = youtube.subscriptions().list(
                part='snippet',
                mine=True,
                maxResults=50
            )
            response = request.execute()
            
            subscriptions = []
            channels = []
            
            for item in response.get('items', []):
                snippet = item['snippet']
                channel_title = snippet['title']
                channel_description = snippet.get('description', '')
                
                subscriptions.append({
                    'channel_title': channel_title,
                    'channel_description': channel_description,
                    'thumbnail': snippet.get('thumbnails', {}).get('default', {}).get('url')
                })
                
                channels.append(channel_title)
            
            logger.info(f"📺 YouTube: {len(channels)} canales detectados")
            
            # Detectar códigos de áreas del museo basadas en los canales
            codigos_areas = self._mapear_canales_a_codigos_areas(channels)
            
            logger.info(f"✅ Áreas detectadas: {codigos_areas}")
            
            return {
                'subscriptions': subscriptions,
                'channels': channels,
                'total_subscriptions': len(subscriptions),
                'codigos_areas_detectadas': codigos_areas  # Retorna códigos BD
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo subscripciones de YouTube: {e}")
            return {
                'subscriptions': [],
                'channels': [],
                'total_subscriptions': 0,
                'codigos_areas_detectadas': []
            }
    
    def _mapear_canales_a_codigos_areas(self, channels: List[str]) -> List[str]:
        """
        🎯 Mapea canales de YouTube a códigos de áreas del museo (BD)
        Retorna: Lista de códigos como ["ARQ-01", "AVE-01", "BOT-01"]
        """
        areas_scores = {
            'ARQ-01': 0,   # Arqueológica Cañari
            'RUIN-01': 0,  # Parque Arqueológico
            'ART-01': 0,   # Arte Colonial
            'ETN-01': 0,   # Etnográfica
            'AVE-01': 0,   # Aves Andinas
            'BOT-01': 0,   # Jardín Botánico
            'TEMP-01': 0   # Temporal
        }
        
        # 🔥 KEYWORDS MAPEADAS A CÓDIGOS DE ÁREAS
        keywords_por_codigo = {
            # ARQUEOLOGÍA CAÑARI (ARQ-01)
            'ARQ-01': [
                'arqueolog', 'archaeolog', 'ancient', 'ruins', 'ruinas', 'excavation',
                'artifact', 'artefacto', 'civilization', 'civilizacion', 'prehistoric',
                'cañari', 'canari', 'inca', 'precolombino', 'precolumbian',
                'tomb', 'tumba', 'ceramic', 'ceramica', 'pottery', 'antiquity',
                'antiguedad', 'heritage', 'patrimonio', 'relic', 'reliquia',
                'maya', 'aztec', 'mesopotamia', 'egypt', 'egipto'
            ],
            
            # PARQUE ARQUEOLÓGICO (RUIN-01)
            'RUIN-01': [
                'ruins', 'ruinas', 'archaeological park', 'parque arqueologico',
                'outdoor', 'exterior', 'open air', 'aire libre', 'monument',
                'monumento', 'site', 'sitio', 'excavation', 'excavaciones',
                'stone', 'piedra', 'wall', 'muro', 'structure', 'estructura'
            ],
            
            # ARTE COLONIAL (ART-01)
            'ART-01': [
                'art', 'arte', 'painting', 'pintura', 'painter', 'pintor',
                'sculpture', 'escultura', 'artist', 'artista', 'gallery', 'galeria',
                'museum', 'museo', 'exhibition', 'exposicion', 'masterpiece',
                'portrait', 'retrato', 'baroque', 'barroco', 'colonial',
                'virreinal', 'religious art', 'arte religioso', 'iconography',
                'mural', 'fresco', 'renaissance', 'renacimiento', 'drawing',
                'illustration', 'design', 'contemporary', 'modern'
            ],
            
            # ETNOGRAFÍA (ETN-01)
            'ETN-01': [
                'ethnography', 'etnografia', 'indigenous', 'indigena', 'tribe',
                'tribal', 'native', 'nativo', 'cultural', 'cultura', 'folklore',
                'tradition', 'tradicion', 'customs', 'costumbres', 'ritual',
                'ceremony', 'ceremonia', 'shamanic', 'chamanico', 'andean',
                'andino', 'quechua', 'kichwa', 'highland', 'sierra',
                'community', 'comunidad', 'anthropology', 'antropologia',
                'textile', 'textil', 'craft', 'artesania', 'weaving', 'tejido',
                'pottery', 'ceramica', 'mask', 'mascara', 'ethnic', 'etnico'
            ],
            
            # AVES ANDINAS (AVE-01)
            'AVE-01': [
                'bird', 'birds', 'ave', 'aves', 'parrot', 'loro', 'macaw',
                'guacamaya', 'condor', 'eagle', 'aguila', 'hawk', 'halcon',
                'hummingbird', 'colibri', 'toucan', 'tucan', 'flamingo',
                'owl', 'buho', 'penguin', 'pinguino', 'birdwatching',
                'ornithology', 'ornitologia', 'feather', 'pluma', 'nest',
                'flight', 'vuelo', 'wing', 'ala', 'aviary', 'aviario',
                'wildlife', 'fauna', 'rescue', 'rescate', 'endemic',
                'tropical birds', 'aves tropicales', 'andean birds'
            ],
            
            # JARDÍN BOTÁNICO (BOT-01)
            'BOT-01': [
                'plant', 'plants', 'planta', 'plantas', 'botanical', 'botanico',
                'garden', 'jardin', 'flower', 'flor', 'tree', 'arbol', 'forest',
                'flora', 'orchid', 'orquidea', 'medicinal', 'herb', 'hierba',
                'biodiversity', 'biodiversidad', 'species', 'especies',
                'ecosystem', 'native', 'nativo', 'endemic', 'conservation',
                'botany', 'botanica', 'vegetation', 'vegetacion', 'leaf',
                'seed', 'semilla', 'ecology', 'ecologia', 'green', 'verde',
                'nature', 'naturaleza', 'environment', 'ambiente'
            ],
            
            # EXHIBICIÓN TEMPORAL (TEMP-01) - menos específico
            'TEMP-01': [
                'exhibition', 'exposicion', 'temporary', 'temporal', 'special',
                'contemporary', 'modern', 'innovation', 'trending', 'current',
                'new', 'latest', 'reciente', 'show', 'display'
            ]
        }
        
        # Analizar cada canal
        for channel in channels:
            channel_lower = channel.lower()
            
            for codigo, keywords in keywords_por_codigo.items():
                # Contar coincidencias
                coincidencias = sum(1 for keyword in keywords if keyword in channel_lower)
                
                if coincidencias > 0:
                    areas_scores[codigo] += coincidencias
                    logger.debug(f"🎯 '{channel}' → {codigo} ({self.AREAS_MUSEO[codigo]}) +{coincidencias}")
        
        # Ordenar áreas por score
        areas_ordenadas = sorted(
            areas_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Filtrar solo áreas con score > 0
        codigos_con_interes = [codigo for codigo, score in areas_ordenadas if score > 0]
        
        # Log detallado de scores con nombres de áreas
        scores_con_nombres = {
            f"{codigo} ({self.AREAS_MUSEO[codigo]})": score 
            for codigo, score in areas_ordenadas
        }
        logger.info(f"📊 Scores: {scores_con_nombres}")
        
        # Si no se detectó nada, sugerir áreas principales
        if not codigos_con_interes:
            logger.warning("⚠️ No se detectaron intereses, sugiriendo áreas principales")
            return ['ARQ-01', 'ETN-01', 'ART-01']  # Áreas core del museo
        
        # Retornar hasta 4 áreas con mayor interés
        return codigos_con_interes[:4]
    
    async def extract_user_interests(self, access_token: str) -> Dict:
        """
        Extrae todos los datos relevantes del usuario de Google
        """
        try:
            # 1. Perfil básico
            profile = await self.get_user_profile(access_token)
            
            # 2. Subscripciones de YouTube
            youtube_data = await self.get_youtube_subscriptions(access_token)
            
            # 3. Códigos de áreas detectadas
            codigos_areas = youtube_data['codigos_areas_detectadas']
            
            # 4. Construir info legible para logs
            nombres_areas = [self.AREAS_MUSEO[codigo] for codigo in codigos_areas]
            
            logger.info(f"✅ Extracción completa: {len(codigos_areas)} áreas → {nombres_areas}")
            
            return {
                'profile': profile,
                'youtube': youtube_data,
                'codigos_areas_detectadas': codigos_areas,  # ["ARQ-01", "AVE-01", ...]
                'nombres_areas_detectadas': nombres_areas,  # Para mostrar en UI
                'confianza_base': self._calcular_confianza(youtube_data),
                'fuentes_datos': ['Google Profile', 'YouTube Subscriptions']
            }
            
        except Exception as e:
            logger.error(f"❌ Error en extracción completa: {e}")
            raise
    
    def _calcular_confianza(self, youtube_data: Dict) -> int:
        """Calcula nivel de confianza basado en cantidad de datos"""
        subscriptions = youtube_data.get('total_subscriptions', 0)
        areas = len(youtube_data.get('codigos_areas_detectadas', []))
        
        confianza = 0
        
        if subscriptions > 0:
            confianza += min(40, subscriptions * 2)
        
        if areas > 0:
            confianza += min(30, areas * 10)
        
        if subscriptions > 0 or areas > 0:
            confianza = max(20, confianza)
        
        return min(100, confianza)

# Instancia global
google_auth_service = GoogleAuthService()