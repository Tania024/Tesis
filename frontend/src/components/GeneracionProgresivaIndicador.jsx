// src/components/GeneracionProgresivaIndicador.jsx
// 🔥 NUEVO: Componente que muestra el progreso de generación

import { useState, useEffect } from 'react';
import { itinerariosAPI } from '../services/api';

const GeneracionProgresivaIndicador = ({ itinerarioId, onCompletado }) => {
  const [estado, setEstado] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Verificar estado cada 3 segundos
    const interval = setInterval(async () => {
      try {
        const data = await itinerariosAPI.obtenerEstadoGeneracion(itinerarioId);
        setEstado(data);
        setLoading(false);

        // Si está completado, detener polling y notificar
        if (data.completado) {
          clearInterval(interval);
          if (onCompletado) {
            onCompletado();
          }
        }
      } catch (error) {
        console.error('Error verificando estado:', error);
      }
    }, 3000); // Cada 3 segundos

    // Limpiar interval al desmontar
    return () => clearInterval(interval);
  }, [itinerarioId, onCompletado]);

  if (loading || !estado) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary-600 border-t-transparent"></div>
        <span>Verificando progreso...</span>
      </div>
    );
  }

  if (estado.completado) {
    return (
      <div className="flex items-center gap-2 text-sm text-green-600">
        <span>✅</span>
        <span>Todas las áreas generadas</span>
      </div>
    );
  }

  return (
    <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-600 border-t-transparent"></div>
          <span className="font-semibold text-blue-900">
            Generando áreas restantes...
          </span>
        </div>
        <span className="text-sm font-bold text-blue-700">
          {estado.areas_generadas} / {estado.total_areas}
        </span>
      </div>

      {/* Barra de progreso */}
      <div className="w-full bg-blue-100 rounded-full h-2 overflow-hidden">
        <div
          className="bg-gradient-to-r from-blue-500 to-purple-500 h-full rounded-full transition-all duration-500"
          style={{ width: `${estado.porcentaje_completado}%` }}
        />
      </div>

      <p className="text-xs text-blue-700 mt-2">
        ℹ️ Puedes comenzar tu visita ahora. Las siguientes áreas se completarán mientras exploras.
      </p>
    </div>
  );
};

export default GeneracionProgresivaIndicador;