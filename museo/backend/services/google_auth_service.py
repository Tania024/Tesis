# services/google_auth_service.py
# Servicio de autenticación con Google y extracción de datos
# Sistema Museo Pumapungo

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
    Servicio para autenticación OAuth con Google y extracción de datos:
    - Perfil básico (nombre, email)
    - Subscripciones de YouTube
    - Lugares guardados en Google Maps
    - Historial de búsquedas (si autoriza)
    """
    
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
        # Scopes que solicitaremos
        self.scopes = [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/youtube.readonly',
        ]
    
    # ============================================
    # AUTENTICACIÓN OAUTH
    # ============================================
    
    def get_authorization_url(self, state: str = "random_state") -> str:
        """
        Genera URL de autorización de Google OAuth
        
        Returns:
            URL completa para redirigir al usuario
        """
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
        """
        Intercambia código de autorización por access token
        
        Args:
            code: Código recibido del callback
            
        Returns:
            dict con access_token, refresh_token, expires_in
        """
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
    
    # ============================================
    # EXTRACCIÓN DE DATOS DE PERFIL
    # ============================================
    
    async def get_user_profile(self, access_token: str) -> Dict:
        """
        Obtiene información básica del perfil de Google
        
        Returns:
            dict con id, email, name, picture
        """
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
    
    # ============================================
    # EXTRACCIÓN DE YOUTUBE
    # ============================================
    
    async def get_youtube_subscriptions(self, access_token: str) -> Dict:
        """
        Obtiene las subscripciones de YouTube del usuario
        Esto nos da pistas sobre sus intereses
        
        Returns:
            dict con subscriptions, channels, categorias_detectadas
        """
        try:
            # Crear credenciales
            credentials = Credentials(token=access_token)
            
            # Construir servicio de YouTube
            youtube = build('youtube', 'v3', credentials=credentials)
            
            # Obtener subscripciones
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
            
            # Detectar categorías basadas en palabras clave
            categorias = self._detectar_categorias_youtube(channels)
            
            logger.info(f"✅ YouTube: {len(subscriptions)} subscripciones obtenidas")
            
            return {
                'subscriptions': subscriptions,
                'channels': channels,
                'total_subscriptions': len(subscriptions),
                'categorias_detectadas': categorias
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo subscripciones de YouTube: {e}")
            # Retornar vacío en lugar de fallar
            return {
                'subscriptions': [],
                'channels': [],
                'total_subscriptions': 0,
                'categorias_detectadas': []
            }
    
    def _detectar_categorias_youtube(self, channels: List[str]) -> List[str]:
        """
        Detecta categorías de interés basadas en nombres de canales
        """
        categorias_detectadas = set()
        
        # Mapeo de palabras clave a categorías del museo
        keywords_map = {
            'arqueologia': ['arqueolog', 'ancient', 'civilization', 'ruins', 'pyramid'],
            'historia': ['history', 'historia', 'historical', 'historic'],
            'arte': ['art', 'arte', 'museum', 'museo', 'gallery', 'painting'],
            'naturaleza': ['nature', 'naturaleza', 'wildlife', 'animal', 'planet'],
            'biodiversidad': ['biodiversity', 'especies', 'conservation', 'aves', 'birds'],
            'cultura_andina': ['andean', 'andino', 'inca', 'quechua', 'indigenous'],
            'ciencia': ['science', 'ciencia', 'discovery', 'documentary'],
        }
        
        # Buscar palabras clave en nombres de canales
        for channel in channels:
            channel_lower = channel.lower()
            
            for categoria, keywords in keywords_map.items():
                if any(keyword in channel_lower for keyword in keywords):
                    categorias_detectadas.add(categoria)
        
        return list(categorias_detectadas)
    
    # ============================================
    # ANÁLISIS COMPLETO
    # ============================================
    
    async def extract_user_interests(self, access_token: str) -> Dict:
        """
        Extrae todos los datos relevantes del usuario de Google
        
        Returns:
            dict con profile, youtube_data, y resumen de intereses
        """
        try:
            # 1. Perfil básico
            profile = await self.get_user_profile(access_token)
            
            # 2. Subscripciones de YouTube
            youtube_data = await self.get_youtube_subscriptions(access_token)
            
            # 3. Construir resumen
            intereses_detectados = youtube_data['categorias_detectadas']
            
            logger.info(f"✅ Extracción completa: {len(intereses_detectados)} categorías detectadas")
            
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
        
        # Fórmula simple de confianza
        confianza = 0
        
        if subscriptions > 0:
            confianza += min(40, subscriptions * 2)  # Máximo 40 puntos
        
        if categorias > 0:
            confianza += min(30, categorias * 10)  # Máximo 30 puntos
        
        # Base mínima de 20 si hay algún dato
        if subscriptions > 0 or categorias > 0:
            confianza = max(20, confianza)
        
        return min(100, confianza)

# Instancia global
google_auth_service = GoogleAuthService()