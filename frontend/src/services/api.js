// src/services/api.js
// Sistema Museo Pumapungo - API Completa
import axios from 'axios';

// Configuración base
const API_URL = import.meta.env.VITE_API_URL || '/pumapungo/api/v1';

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
  },
  actualizar: async (id, datos) => {
    const response = await api.put(`/itinerarios/${id}`, datos);
    return response.data;
  },

  actualizarItinerario: async (id, datos) => {
    const response = await api.put(`/itinerarios/${id}`, datos);
    return response.data;
  },
  generarProgresivo: async (visitanteId, datos) => {
  try {
    const response = await api.post('/itinerarios/generar', {  // ← CAMBIAR URL
      visitante_id: visitanteId,
      intereses: datos.intereses || [],
      tiempo_disponible: datos.tiempo_disponible || null,
      nivel_detalle: datos.nivel_detalle || 'normal',
      tipo_entrada: datos.tipo_entrada || 'individual',     // ← AGREGAR
      acompanantes: datos.acompanantes || 0,                // ← AGREGAR (sin ñ)
      incluir_descansos: datos.incluir_descansos !== false,
      areas_evitar: datos.areas_evitar || []
    });
      
      console.log('✅ Primera área generada, resto en progreso');
      return response.data;
    } catch (error) {
      console.error('❌ Error en generación progresiva:', error);
      throw error;
    }
  },

  // 🔥 NUEVO: Obtener estado de generación (para polling)
  obtenerEstadoGeneracion: async (itinerarioId) => {
    try {
      const response = await api.get(`/ia/itinerario/${itinerarioId}/estado-generacion`);
      return response.data;
    } catch (error) {
      console.error('❌ Error obteniendo estado:', error);
      throw error;
    }
  },

  // SSE: Conectar al stream de generación de áreas
  conectarStreamAreas: (itinerarioId, callbacks) => {
    const url = `${API_URL}/itinerarios/${itinerarioId}/stream`;
    console.log('SSE: Conectando a', url);

    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('SSE evento:', data.type, data.area_nombre || '');

        if (data.type === 'inicio' && callbacks.onInicio) {
          callbacks.onInicio(data);
        } else if (data.type === 'area_completada' && callbacks.onAreaCompletada) {
          callbacks.onAreaCompletada(data);
        } else if (data.type === 'completado' && callbacks.onCompletado) {
          callbacks.onCompletado(data);
          eventSource.close();
        } else if (data.type === 'error' && callbacks.onError) {
          callbacks.onError(data);
          eventSource.close();
        }
      } catch (err) {
        console.error('SSE parse error:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE connection error:', err);
      if (callbacks.onError) {
        callbacks.onError({ message: 'Conexión SSE perdida' });
      }
      eventSource.close();
    };

    return eventSource;
  },

  generarCertificado: async (itinerarioId) => {
    try {
      const response = await api.post(`/itinerarios/${itinerarioId}/certificado`);
      console.log('✅ Certificado generado:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error generando certificado:', error.response?.data || error);
      throw error;
    }
  },
};


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

  // Actualizar perfil del visitante
  update: async (id, datos) => {
    const response = await api.put(`/visitantes/${id}/`, datos);
    return response.data;
  }
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
  },

  // ✅ FUNCIÓN QUE FALTABA
  obtenerEstadisticas: async () => {
    const response = await api.get('/evaluaciones/estadisticas');
    return response.data;
  }
};

// ============================================
// REPORTES API (Admin - Descarga CSV)
// ============================================

const descargarCSV = async (endpoint, nombreArchivo) => {
  try {
    const response = await api.get(endpoint, {
      responseType: 'blob'
    });
    const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', nombreArchivo);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    return true;
  } catch (error) {
    console.error(`❌ Error descargando ${nombreArchivo}:`, error);
    throw error;
  }
};

export const reportesAPI = {
  descargarVisitantes: () => descargarCSV('/reportes/visitantes', `visitantes_${new Date().toISOString().slice(0,10)}.csv`),
  descargarEvaluaciones: () => descargarCSV('/reportes/evaluaciones', `evaluaciones_${new Date().toISOString().slice(0,10)}.csv`),
  descargarResumen: () => descargarCSV('/reportes/resumen', `resumen_museo_${new Date().toISOString().slice(0,10)}.csv`),
};

// Exportar instancia de axios por defecto
export default api;