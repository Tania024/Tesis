// src/services/api.js
// Sistema Museo Pumapungo - API Completa
import axios from 'axios';

// Configuración base
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Instancia de axios con configuración base
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// ============================================
// INTERCEPTORES
// ============================================

// Interceptor para añadir token y logging
api.interceptors.request.use(
  (config) => {
    // Añadir token de autenticación
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Logging (desarrollo)
    console.log('🔵 API Request:', config.method.toUpperCase(), config.url);
    
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Interceptor para manejar respuestas
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
// AUTH API
// ============================================

export const authAPI = {
  // Login con Google OAuth
  loginWithGoogle: async () => {
    window.location.href = `${API_URL}/auth/google/login`;
  },

  // Callback de Google OAuth
  handleGoogleCallback: async (code) => {
    const response = await api.get(`/auth/google/callback?code=${code}`);
    return response.data;
  },

  // Logout
  logout: async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  },

  // Obtener usuario actual
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
  
  // Obtener visitante por ID
  getVisitante: async (visitanteId) => {
    const response = await api.get(`/visitantes/${visitanteId}`);
    return response.data;
  },
};

// ============================================
// PERFILES API
// ============================================

export const perfilesAPI = {
  // Obtener perfil de un visitante
  obtener: async (visitante_id) => {
    const response = await api.get(`/perfiles/visitante/${visitante_id}`);
    return response.data;
  },

  // Crear perfil
  crear: async (data) => {
    const response = await api.post('/perfiles/', data);
    return response.data;
  },

  // Actualizar perfil
  actualizar: async (id, data) => {
    const response = await api.put(`/perfiles/${id}`, data);
    return response.data;
  },
};

// ============================================
// ÁREAS DEL MUSEO API
// ============================================

export const areasAPI = {
  // Listar todas las áreas activas
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
// ITINERARIOS API
// ============================================

export const itinerariosAPI = {
  // Generar itinerario con IA
  generar: async (data) => {
    const response = await api.post('/itinerarios/generar', data);
    return response.data;
  },
  
  // Alias para compatibilidad
  generarItinerario: async (data) => {
    const response = await api.post('/itinerarios/generar', data);
    return response.data;
  },

  // Listar itinerarios de un visitante
  listar: async (visitante_id) => {
    const response = await api.get(`/itinerarios/visitante/${visitante_id}`);
    return response.data;
  },
  
  // Alias para compatibilidad
  listarItinerariosVisitante: async (visitante_id) => {
    const response = await api.get(`/itinerarios/visitante/${visitante_id}`);
    return response.data;
  },

  // Obtener itinerario completo con detalles
  obtenerItinerario: async (id) => {
    const response = await api.get(`/itinerarios/${id}`);
    return response.data;
  },

  // Iniciar itinerario
  iniciarItinerario: async (id) => {
    const response = await api.post(`/itinerarios/${id}/iniciar`);
    return response.data;
  },

  // Completar itinerario
  completarItinerario: async (id) => {
    const response = await api.post(`/itinerarios/${id}/completar`);
    return response.data;
  },

  // Eliminar itinerario
  eliminar: async (id) => {
    const response = await api.delete(`/itinerarios/${id}`);
    return response.data;
  },

   // Estadísticas generales
  estadisticas: async () => {
   const response = await api.get('/itinerarios/estadisticas');
    return response.data;
  },
  guardarEvaluacion: async (itinerarioId, evaluacion) => {
    return await evaluacionesAPI.guardarEvaluacion(itinerarioId, evaluacion);
  }
}

// ============================================
// DETALLES DE ITINERARIO API
// ============================================

export const detallesAPI = {
  // Obtener detalles de un itinerario
  obtenerDetalles: async (itinerarioId) => {
    const response = await api.get(`/detalles/itinerario/${itinerarioId}`);
    return response.data;
  },
  
  // Marcar área como visitada
  completarArea: async (detalleId) => {
    const response = await api.patch(`/itinerarios/detalles/${detalleId}`, {
      visitado: true,
      hora_fin: new Date().toISOString(),
    });
    return response.data;
  },

  // Omitir área
  omitirArea: async (detalleId) => {
    const response = await api.patch(`/itinerarios/detalles/${detalleId}`, {
      skip: true,
    });
    return response.data;
  },

  // Iniciar área
  iniciarArea: async (detalleId) => {
    const response = await api.patch(`/itinerarios/detalles/${detalleId}`, {
      hora_inicio: new Date().toISOString(),
    });
    return response.data;
  },
  
  // Actualizar tiempo real
  actualizarTiempoReal: async (detalleId, tiempoMinutos) => {
    const response = await api.patch(`/itinerarios/detalles/${detalleId}`, {
      tiempo_real: tiempoMinutos,
    });
    return response.data;
  },
  
  // Ver progreso de un itinerario
  verProgreso: async (itinerarioId) => {
    const response = await api.get(`/detalles/itinerario/${itinerarioId}/progreso`);
    return response.data;
  },
  
  reactivarArea: async (detalleId) => {
    try {
      const response = await api.patch(`/detalles/${detalleId}/reactivar`);
      console.log('✅ Área reactivada:', detalleId);
      return response.data;
    } catch (error) {
      console.error('❌ Error reactivando área:', error);
      throw error;
    }
  },

  desmarcarArea: async (detalleId) => {
    try {
      const response = await api.patch(`/detalles/${detalleId}/desmarcar`);
      console.log('✅ Área desmarcada:', detalleId);
      return response.data;
    } catch (error) {
      console.error('❌ Error desmarcando área:', error);
      throw error;
    }
  }
};

// ============================================
// VISITANTES API (Admin)
// ============================================

export const visitantesAPI = {
  // Listar todos los visitantes
  listar: async (params = {}) => {
    const response = await api.get('/visitantes/', { params });
    return response.data;
  },
  
  // Obtener visitante específico
  obtener: async (id) => {
    const response = await api.get(`/visitantes/${id}`);
    return response.data;
  },

  // Estadísticas de visitantes
  estadisticas: async () => {
   const response = await api.get('/visitantes/estadisticas');
    return response.data;
  },
}

// ============================================
// HISTORIAL API (Admin)
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


// ============================================
// API DE EVALUACIONES
// ============================================

export const evaluacionesAPI = {
  guardarEvaluacion: async (itinerarioId, evaluacion) => {
    try {
      const response = await api.post('/evaluaciones/', {
        itinerario_id: itinerarioId,
        calificacion_general: evaluacion.calificacion_general,
        personalizado: evaluacion.personalizado,
        buenas_decisiones: evaluacion.buenas_decisiones,
        acompaniamiento: evaluacion.acompaniamiento,
        comprension: evaluacion.comprension,
        relevante: evaluacion.relevante,
        usaria_nuevamente: evaluacion.usaria_nuevamente,
        comentarios: evaluacion.comentarios || null
      });
      
      console.log('✅ Evaluación guardada:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error guardando evaluación:', error.response?.data || error);
      throw error;
    }
  }
};

// Exportar instancia de axios por defecto
export default api;