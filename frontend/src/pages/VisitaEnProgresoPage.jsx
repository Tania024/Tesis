import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { itinerariosAPI, detallesAPI } from '../services/api';
import LoadingSpinner from '../components/Layout/LoadingSpinner';

const VisitaEnProgresoPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [procesando, setProcesando] = useState(false);
  const [error, setError] = useState(null);
  const [itinerario, setItinerario] = useState(null);
  const [detalles, setDetalles] = useState([]);
  const [progreso, setProgreso] = useState(null);
  const [tiempoInicio] = useState(Date.now());
  const [tiempoTranscurrido, setTiempoTranscurrido] = useState(0);
  const [mostrarModalCompletado, setMostrarModalCompletado] = useState(false);

  useEffect(() => {
    cargarDatos();
  }, [id]);

  // Temporizador
  useEffect(() => {
    const interval = setInterval(() => {
      setTiempoTranscurrido(Math.floor((Date.now() - tiempoInicio) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [tiempoInicio]);

  const cargarDatos = async () => {
    try {
      setLoading(true);
      setError(null);

      const [itinerarioData, detallesData, progresoData] = await Promise.all([
        itinerariosAPI.obtenerItinerario(id),
        detallesAPI.obtenerDetalles(id),
        detallesAPI.verProgreso(id)
      ]);

      setItinerario(itinerarioData);
      setDetalles(detallesData.sort((a, b) => a.orden - b.orden));
      setProgreso(progresoData);
    } catch (err) {
      console.error('Error al cargar datos:', err);
      setError('No se pudo cargar la información de la visita.');
    } finally {
      setLoading(false);
    }
  };

  const handleCompletarArea = async (detalleId) => {
    try {
      setProcesando(true);
      await detallesAPI.completarArea(detalleId);
      await cargarDatos();
      
      // Verificar si se completaron todas las áreas
      const todasCompletadas = detalles.every(d => 
        d.id === detalleId || d.estado === 'completado' || d.estado === 'omitido'
      );
      
      if (todasCompletadas) {
        setMostrarModalCompletado(true);
      }
    } catch (err) {
      console.error('Error al completar área:', err);
      alert('No se pudo marcar el área como completada. Intenta de nuevo.');
    } finally {
      setProcesando(false);
    }
  };

  const handleOmitirArea = async (detalleId) => {
    if (!confirm('¿Estás seguro de que deseas omitir esta área?')) {
      return;
    }

    try {
      setProcesando(true);
      await detallesAPI.omitirArea(detalleId);
      await cargarDatos();
    } catch (err) {
      console.error('Error al omitir área:', err);
      alert('No se pudo omitir el área. Intenta de nuevo.');
    } finally {
      setProcesando(false);
    }
  };

  const handleFinalizarVisita = async () => {
    try {
      setProcesando(true);
      await itinerariosAPI.completarItinerario(id);
      navigate('/mis-itinerarios', { 
        state: { mensaje: '¡Visita completada exitosamente! 🎉' }
      });
    } catch (err) {
      console.error('Error al finalizar visita:', err);
      alert('No se pudo finalizar la visita. Intenta de nuevo.');
      setProcesando(false);
    }
  };

  const obtenerAreaActual = () => {
    return detalles.find(d => d.estado === 'pendiente');
  };

  const calcularPorcentaje = () => {
    if (!progreso) return 0;
    const total = progreso.total_areas;
    const completadas = progreso.areas_completadas + progreso.areas_omitidas;
    return Math.round((completadas / total) * 100);
  };

  const formatearTiempo = (segundos) => {
    const horas = Math.floor(segundos / 3600);
    const minutos = Math.floor((segundos % 3600) / 60);
    const segs = segundos % 60;

    if (horas > 0) {
      return `${horas}h ${minutos}m ${segs}s`;
    } else if (minutos > 0) {
      return `${minutos}m ${segs}s`;
    } else {
      return `${segs}s`;
    }
  };

  const obtenerEstadoIcono = (estado) => {
    switch (estado) {
      case 'completado':
        return '✅';
      case 'omitido':
        return '⏭️';
      default:
        return '⏳';
    }
  };

  const obtenerEstadoColor = (estado) => {
    switch (estado) {
      case 'completado':
        return 'bg-green-50 border-green-200';
      case 'omitido':
        return 'bg-yellow-50 border-yellow-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const obtenerEstadoTexto = (estado) => {
    switch (estado) {
      case 'completado':
        return 'Completada';
      case 'omitido':
        return 'Omitida';
      default:
        return 'Pendiente';
    }
  };

  if (loading) return <LoadingSpinner />;

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <div className="text-4xl mb-4">❌</div>
          <h2 className="text-xl font-semibold text-red-800 mb-2">Error</h2>
          <p className="text-red-600 mb-4">{error}</p>
          <button onClick={() => navigate('/mis-itinerarios')} className="btn-secondary">
            Volver
          </button>
        </div>
      </div>
    );
  }

  const areaActual = obtenerAreaActual();
  const porcentaje = calcularPorcentaje();
  const todasCompletadas = !areaActual && detalles.length > 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-museo-cream to-white py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Header con Progreso */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <h1 className="text-2xl font-bold text-gray-900">
                {itinerario?.titulo || 'Visita en Progreso'}
              </h1>
              <span className="text-sm text-gray-600 flex items-center gap-1">
                ⏱️ {formatearTiempo(tiempoTranscurrido)}
              </span>
            </div>
          </div>

          {/* Barra de Progreso */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                Progreso General
              </span>
              <span className="text-sm font-bold text-primary-600">
                {porcentaje}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className="bg-gradient-to-r from-primary-500 to-primary-600 h-3 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${porcentaje}%` }}
              />
            </div>
            {progreso && (
              <div className="flex items-center justify-between mt-2 text-xs text-gray-600">
                <span>
                  ✅ {progreso.areas_completadas} completadas
                </span>
                <span>
                  ⏭️ {progreso.areas_omitidas} omitidas
                </span>
                <span>
                  ⏳ {progreso.areas_pendientes} pendientes
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Área Actual */}
        {areaActual && (
          <div className="bg-gradient-to-br from-primary-50 to-white border-2 border-primary-300 rounded-2xl shadow-xl p-6 mb-6">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-2xl">📍</span>
              <h2 className="text-xl font-bold text-gray-900">
                Área Actual - Paso {areaActual.orden}
              </h2>
            </div>

            <h3 className="text-2xl font-bold text-primary-700 mb-3">
              {areaActual.area.nombre}
            </h3>

            {areaActual.area.descripcion && (
              <div className="mb-4 p-4 bg-white rounded-lg">
                <p className="text-gray-700 leading-relaxed">
                  {areaActual.area.descripcion}
                </p>
              </div>
            )}

            <div className="mb-4 flex items-center gap-4 text-sm text-gray-600">
              <span className="flex items-center gap-1">
                ⏱️ Tiempo sugerido: {areaActual.tiempo_sugerido} minutos
              </span>
              {areaActual.area.ubicacion && (
                <span className="flex items-center gap-1">
                  📍 {areaActual.area.ubicacion}
                </span>
              )}
            </div>

            {areaActual.introduccion_ia && (
              <div className="mb-4 p-4 bg-white rounded-lg border border-gray-200">
                <div className="flex items-center gap-2 mb-2">
                  <span>🤖</span>
                  <h4 className="font-semibold text-gray-900">
                    Tu Guía Personalizada
                  </h4>
                </div>
                <p className="text-gray-700 leading-relaxed">
                  {areaActual.introduccion_ia}
                </p>
              </div>
            )}

            {areaActual.puntos_clave_ia && areaActual.puntos_clave_ia.length > 0 && (
              <div className="mb-4 p-4 bg-white rounded-lg border border-gray-200">
                <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <span>✨</span>
                  Puntos a Destacar
                </h4>
                <ul className="space-y-2">
                  {areaActual.puntos_clave_ia.map((punto, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-gray-700">
                      <span className="text-primary-500 mt-1 font-bold">•</span>
                      <span>{punto}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {areaActual.recomendacion_ia && (
              <div className="mb-6 p-4 bg-museo-gold bg-opacity-10 border border-museo-gold border-opacity-30 rounded-lg">
                <div className="flex items-start gap-2">
                  <span className="text-xl">💡</span>
                  <div>
                    <h4 className="font-semibold text-museo-brown mb-1">
                      Recomendación
                    </h4>
                    <p className="text-gray-700">
                      {areaActual.recomendacion_ia}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Botones de Acción */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => handleCompletarArea(areaActual.id)}
                disabled={procesando}
                className="btn-primary py-4 text-lg flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <span className="text-2xl">✅</span>
                {procesando ? 'Procesando...' : 'Completar Esta Área'}
              </button>
              <button
                onClick={() => handleOmitirArea(areaActual.id)}
                disabled={procesando}
                className="bg-yellow-500 text-white px-6 py-4 rounded-lg font-semibold hover:bg-yellow-600 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <span className="text-2xl">⏭️</span>
                Omitir Área
              </button>
            </div>
          </div>
        )}

        {/* Lista Completa de Áreas */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span>🗺️</span>
            Todas las Áreas del Recorrido
          </h2>

          <div className="space-y-3">
            {detalles.map((detalle) => {
              const esActual = areaActual?.id === detalle.id;
              
              return (
                <div
                  key={detalle.id}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    esActual
                      ? 'border-primary-500 bg-primary-50 shadow-md'
                      : obtenerEstadoColor(detalle.estado)
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                        esActual
                          ? 'bg-primary-500 text-white'
                          : detalle.estado === 'completado'
                          ? 'bg-green-500 text-white'
                          : detalle.estado === 'omitido'
                          ? 'bg-yellow-500 text-white'
                          : 'bg-gray-300 text-gray-700'
                      }`}>
                        {detalle.orden}
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">
                          {detalle.area.nombre}
                        </h3>
                        <div className="flex items-center gap-3 text-sm text-gray-600 mt-1">
                          <span>⏱️ {detalle.tiempo_sugerido} min</span>
                          <span className="flex items-center gap-1">
                            {obtenerEstadoIcono(detalle.estado)}
                            {obtenerEstadoTexto(detalle.estado)}
                          </span>
                        </div>
                      </div>
                    </div>
                    {esActual && (
                      <span className="px-3 py-1 bg-primary-500 text-white rounded-full text-xs font-semibold animate-pulse">
                        ACTUAL
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Mensaje de Visita Completada */}
        {todasCompletadas && (
          <div className="mt-6 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-2xl p-6">
            <div className="text-center">
              <div className="text-6xl mb-4">🎉</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                ¡Felicitaciones!
              </h2>
              <p className="text-gray-700 mb-6">
                Has completado tu visita al Museo Pumapungo
              </p>
              <button
                onClick={handleFinalizarVisita}
                disabled={procesando}
                className="btn-primary text-lg px-8 py-3 disabled:opacity-50"
              >
                {procesando ? 'Finalizando...' : 'Finalizar Visita ✨'}
              </button>
            </div>
          </div>
        )}

        {/* Modal de Confirmación */}
        {mostrarModalCompletado && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
              <div className="text-center">
                <div className="text-6xl mb-4">🎊</div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">
                  ¡Visita Completada!
                </h3>
                <p className="text-gray-600 mb-6">
                  Has terminado todas las áreas de tu itinerario personalizado.
                </p>
                <div className="space-y-3">
                  <button
                    onClick={handleFinalizarVisita}
                    disabled={procesando}
                    className="w-full btn-primary disabled:opacity-50"
                  >
                    {procesando ? 'Finalizando...' : 'Finalizar y Ver Resumen'}
                  </button>
                  <button
                    onClick={() => setMostrarModalCompletado(false)}
                    className="w-full btn-secondary"
                  >
                    Continuar Explorando
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VisitaEnProgresoPage;