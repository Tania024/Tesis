import axios from 'axios';

// Configuración base de API
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para logging (desarrollo)
api.interceptors.request.use(
  (config) => {
    console.log('🔵 API Request:', config.method.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    console.log('✅ API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

// ============================================
// AUTENTICACIÓN
// ============================================

export const authAPI = {
  // Obtener URL de login de Google
  getGoogleLoginUrl: async () => {
    const response = await api.get('/auth/google/login');
    return response.data;
  },
  
  // Verificar estado del visitante
  getVisitante: async (visitanteId) => {
    const response = await api.get(`/visitantes/${visitanteId}`);
    return response.data;
  },
};

// ============================================
// ÁREAS DEL MUSEO
// ============================================

export const areasAPI = {
  // Listar todas las áreas
  listarAreas: async () => {
    const response = await api.get('/areas/', {
      params: { activa: true, limit: 50 }
    });
    return response.data;
  },
  
  // Obtener área específica
  obtenerArea: async (areaId) => {
    const response = await api.get(`/areas/${areaId}`);
    return response.data;
  },
  
  // Recorrido sugerido
  recorridoSugerido: async () => {
    const response = await api.get('/areas/recorrido/sugerido');
    return response.data;
  },
};

// ============================================
// ITINERARIOS
// ============================================

export const itinerariosAPI = {
  // Generar itinerario con IA
  generarItinerario: async (data) => {
    const response = await api.post('/itinerarios/generar', data);
    return response.data;
  },
  
  // Obtener itinerario específico
  obtenerItinerario: async (itinerarioId) => {
    const response = await api.get(`/itinerarios/${itinerarioId}`);
    return response.data;
  },
  
  // Listar itinerarios de un visitante
  listarItinerariosVisitante: async (visitanteId) => {
    const response = await api.get(`/itinerarios/visitante/${visitanteId}`);
    return response.data;
  },
  
  // Iniciar itinerario
  iniciarItinerario: async (itinerarioId) => {
    const response = await api.post(`/itinerarios/${itinerarioId}/iniciar`);
    return response.data;
  },
  
  // Completar itinerario
  completarItinerario: async (itinerarioId) => {
    const response = await api.post(`/itinerarios/${itinerarioId}/completar`);
    return response.data;
  },
  
  // Estadísticas
  estadisticas: async () => {
    const response = await api.get('/itinerarios/estadisticas/general');
    return response.data;
  },
};

// ============================================
// DETALLES DE ITINERARIO
// ============================================

export const detallesAPI = {
  // Obtener detalles de un itinerario
  obtenerDetalles: async (itinerarioId) => {
    const response = await api.get(`/detalles/itinerario/${itinerarioId}`);
    return response.data;
  },
  
  // Completar área
  completarArea: async (detalleId) => {
    const response = await api.post(`/detalles/${detalleId}/completar`);
    return response.data;
  },
  
  // Omitir área
  omitirArea: async (detalleId) => {
    const response = await api.post(`/detalles/${detalleId}/omitir`);
    return response.data;
  },
  
  // Ver progreso
  verProgreso: async (itinerarioId) => {
    const response = await api.get(`/detalles/itinerario/${itinerarioId}/progreso`);
    return response.data;
  },
};

// ============================================
// VISITANTES (Admin)
// ============================================

export const visitantesAPI = {
  // Listar todos
  listar: async (params = {}) => {
    const response = await api.get('/visitantes/', { params });
    return response.data;
  },
  
  // Estadísticas
  estadisticas: async () => {
    const response = await api.get('/visitantes/estadisticas/resumen');
    return response.data;
  },
};

// ============================================
// HISTORIAL (Admin)
// ============================================

export const historialAPI = {
  // Estadísticas de hoy
  estadisticasHoy: async () => {
    const response = await api.get('/historial/estadisticas/hoy');
    return response.data;
  },
  
  // Estadísticas de la semana
  estadisticasSemana: async () => {
    const response = await api.get('/historial/estadisticas/semana');
    return response.data;
  },
  
  // Horas pico
  horasPico: async () => {
    const response = await api.get('/historial/estadisticas/horas-pico');
    return response.data;
  },
};

export default api;