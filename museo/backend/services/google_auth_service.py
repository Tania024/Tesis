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
    """
    
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
        """
        Obtiene las subscripciones de YouTube del usuario
        """
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
            
            # LOG IMPORTANTE: Ver qué canales está detectando
            logger.info(f"📺 Canales de YouTube detectados: {channels[:10]}...")  # Primeros 10
            
            # Detectar categorías con el nuevo sistema mejorado
            categorias = self._detectar_categorias_youtube_mejorado(channels)
            
            logger.info(f"✅ YouTube: {len(subscriptions)} subscripciones → Categorías: {categorias}")
            
            return {
                'subscriptions': subscriptions,
                'channels': channels,
                'total_subscriptions': len(subscriptions),
                'categorias_detectadas': categorias
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo subscripciones de YouTube: {e}")
            return {
                'subscriptions': [],
                'channels': [],
                'total_subscriptions': 0,
                'categorias_detectadas': []
            }
    
    def _detectar_categorias_youtube_mejorado(self, channels: List[str]) -> List[str]:
        """
        Sistema mejorado de detección de categorías con MUCHAS más palabras clave
        """
        categorias_detectadas = {}  
        
        keywords_map = {
            # ARQUEOLOGÍA (relacionado con Museo Pumapungo)
            'arqueologia': [
                'arqueolog', 'archaeolog', 'ancient', 'ruins', 'pyramid', 'tomb',
                'excavation', 'artifact', 'mesopotamia', 'egypt', 'maya', 'aztec',
                'civilization', 'ancestral', 'prehistoric', 'paleontology',
                'fossil', 'excavaciones', 'ruinas', 'civilizacion', 'antiguedad'
            ],
            
            # HISTORIA
            'historia': [
                'history', 'historia', 'historical', 'historic', 'war', 'guerra',
                'revolution', 'revolucion', 'timeline', 'biography', 'biografia',
                'documentar', 'chronicle', 'cronica', 'period', 'epoch', 'era',
                'medieval', 'renaissance', 'victorian', 'empire', 'imperio'
            ],
            
            # ARTE (importante para museo)
            'arte': [
                'art', 'arte', 'museum', 'museo', 'gallery', 'galeria', 'painting',
                'pintura', 'sculpture', 'escultura', 'artist', 'artista', 'canvas',
                'masterpiece', 'obra', 'exhibition', 'exposicion', 'design',
                'creative', 'draw', 'dibujo', 'illustration', 'ilustracion',
                'contemporary', 'modern', 'abstract', 'portrait', 'retrato'
            ],
            
            # NATURALEZA Y BIODIVERSIDAD (Pumapungo tiene jardín etnobotánico)
            'naturaleza': [
                'nature', 'naturaleza', 'wildlife', 'animal', 'planet', 'planeta',
                'earth', 'tierra', 'ocean', 'oceano', 'forest', 'bosque', 'jungle',
                'safari', 'outdoor', 'landscape', 'paisaje', 'environment', 'ambiente',
                'ecology', 'ecologia', 'wild', 'salvaje', 'mountain', 'montaña'
            ],
            
            'biodiversidad': [
                'biodiversity', 'biodiversidad', 'species', 'especies', 'conservation',
                'conservacion', 'aves', 'birds', 'parrot', 'loro', 'guacamaya',
                'condor', 'flora', 'fauna', 'endemic', 'endemico', 'botanical',
                'botanico', 'plants', 'plantas', 'orchid', 'orquidea'
            ],
            
            # CULTURA ANDINA (MUY importante para Pumapungo)
            'cultura_andina': [
                'andean', 'andino', 'inca', 'inkas', 'quechua', 'kichwa',
                'indigenous', 'indigena', 'native', 'nativo', 'tribal', 'tribe',
                'cañari', 'cañar', 'cuenca', 'ecuador', 'peru', 'bolivia',
                'altiplano', 'highlands', 'sierra', 'shamanic', 'chamanico',
                'ritual', 'ceremony', 'ceremonia', 'traditional', 'tradicional'
            ],
            
            # CIENCIA Y EDUCACIÓN
            'ciencia': [
                'science', 'ciencia', 'discovery', 'descubrimiento', 'research',
                'investigacion', 'experiment', 'experimento', 'physics', 'fisica',
                'chemistry', 'quimica', 'biology', 'biologia', 'astronomy',
                'astronomia', 'cosmos', 'space', 'espacio', 'nasa', 'lab',
                'laboratorio', 'scientist', 'cientifico', 'theory', 'teoria'
            ],
            
            # GEOGRAFÍA Y VIAJES (interesante para visitantes)
            'geografia': [
                'geography', 'geografia', 'travel', 'viaje', 'tourism', 'turismo',
                'world', 'mundo', 'country', 'pais', 'city', 'ciudad', 'explore',
                'explorar', 'adventure', 'aventura', 'journey', 'trip', 'destination',
                'destino', 'culture', 'cultural', 'atlas', 'map', 'mapa'
            ],
            
            # ANTROPOLOGÍA Y ETNOGRAFÍA (Pumapungo tiene sala etnográfica)
            'antropologia': [
                'anthropology', 'antropologia', 'ethnography', 'etnografia',
                'cultural', 'folklore', 'tradition', 'tradicion', 'customs',
                'costumbres', 'heritage', 'patrimonio', 'identity', 'identidad',
                'community', 'comunidad', 'society', 'sociedad', 'ethnic', 'etnico'
            ],
            
            # MÚSICA Y DANZA (cultura)
            'musica': [
                'music', 'musica', 'song', 'cancion', 'dance', 'danza', 'baile',
                'instrument', 'instrumento', 'folk', 'folklorico', 'traditional music',
                'andean music', 'musica andina', 'quena', 'charango', 'zampoña'
            ],
            
            # TECNOLOGÍA (para distinguir de otros intereses)
            'tecnologia': [
                'tech', 'technology', 'tecnologia', 'gadget', 'computer', 'computadora',
                'software', 'programming', 'programacion', 'code', 'codigo', 'gaming',
                'videogame', 'videojuego', 'console', 'pc', 'smartphone', 'app',
                'digital', 'cyber', 'robot', 'ai', 'inteligencia artificial'
            ],
            
            # COCINA Y GASTRONOMÍA
            'gastronomia': [
                'food', 'comida', 'cooking', 'cocina', 'recipe', 'receta', 'chef',
                'restaurant', 'restaurante', 'cuisine', 'culinary', 'culinario',
                'gastronomy', 'gastronomia', 'dish', 'plato', 'traditional food'
            ],
            
            # ENTRETENIMIENTO GENERAL (para descartar)
            'entretenimiento': [
                'entertainment', 'entretenimiento', 'comedy', 'comedia', 'funny',
                'gracioso', 'laugh', 'risa', 'prank', 'broma', 'challenge', 'reto',
                'vlog', 'lifestyle', 'estilo de vida', 'celebrity', 'celebridad',
                'gossip', 'chisme', 'trend', 'tendencia', 'viral'
            ],
            
            # DEPORTES (para descartar, no relacionado con museo)
            'deportes': [
                'sport', 'deporte', 'football', 'futbol', 'soccer', 'basketball',
                'tennis', 'tenis', 'athletic', 'atletismo', 'fitness', 'gym',
                'exercise', 'ejercicio', 'workout', 'training', 'entrenamiento',
                'champion', 'campeon', 'league', 'liga', 'team', 'equipo'
            ]
        }
        
        # Buscar palabras clave en nombres de canales
        for channel in channels:
            channel_lower = channel.lower()
            
            for categoria, keywords in keywords_map.items():
                coincidencias = sum(1 for keyword in keywords if keyword in channel_lower)
                
                if coincidencias > 0:
                    # Contar cuántas veces aparece cada categoría
                    if categoria not in categorias_detectadas:
                        categorias_detectadas[categoria] = 0
                    categorias_detectadas[categoria] += coincidencias
                    
                    # LOG detallado para debugging
                    logger.debug(f"🎯 Canal '{channel}' → {categoria} ({coincidencias} coincidencias)")
        
        # Ordenar categorías por frecuencia y retornar las más relevantes
        categorias_ordenadas = sorted(
            categorias_detectadas.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Filtrar: solo categorías relacionadas con el museo (excluir deportes, entretenimiento, tecnología)
        categorias_museo = [
            cat for cat, _ in categorias_ordenadas 
            if cat not in ['deportes', 'entretenimiento', 'tecnologia', 'gastronomia']
        ]
        
        # Si no se detectó nada relevante, usar cultura como fallback
        if not categorias_museo:
            logger.warning("⚠️ No se detectaron categorías específicas, usando fallback: cultura")
            return ['cultura']
        
        # Retornar hasta 5 categorías principales
        return categorias_museo[:5]
    
    async def extract_user_interests(self, access_token: str) -> Dict:
        """
        Extrae todos los datos relevantes del usuario de Google
        """
        try:
            # 1. Perfil básico
            profile = await self.get_user_profile(access_token)
            
            # 2. Subscripciones de YouTube
            youtube_data = await self.get_youtube_subscriptions(access_token)
            
            # 3. Construir resumen
            intereses_detectados = youtube_data['categorias_detectadas']
            
            logger.info(f"✅ Extracción completa: {len(intereses_detectados)} categorías detectadas → {intereses_detectados}")
            
            return {
                'profile': profile,
                'youtube': youtube_data,
                'intereses_detectados': intereses_detectados,
                'confianza_base': self._calcular_confianza(youtube_data),
                'fuentes_datos': ['Google Profile', 'YouTube Subscriptions']
            }
            
        except Exception as e:
            logger.error(f"❌ Error en extracción completa: {e}")
            raise
    
    def _calcular_confianza(self, youtube_data: Dict) -> int:
        """
        Calcula nivel de confianza basado en cantidad de datos
        """
        subscriptions = youtube_data.get('total_subscriptions', 0)
        categorias = len(youtube_data.get('categorias_detectadas', []))
        
        confianza = 0
        
        if subscriptions > 0:
            confianza += min(40, subscriptions * 2)  # Máximo 40 puntos
        
        if categorias > 0:
            confianza += min(30, categorias * 10)  # Máximo 30 puntos
        
        if subscriptions > 0 or categorias > 0:
            confianza = max(20, confianza)
        
        return min(100, confianza)

# Instancia global
google_auth_service = GoogleAuthService()