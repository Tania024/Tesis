import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { itinerariosAPI } from '../services/api';
import LoadingSpinner from '../components/Layout/LoadingSpinner';

const VerItinerarioPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, isAuthenticated } = useAuth();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [itinerario, setItinerario] = useState(null);
  const [generandoAreas, setGenerandoAreas] = useState(false);
  const [areasGeneradas, setAreasGeneradas] = useState(0);
  const [totalAreas, setTotalAreas] = useState(0);
  const eventSourceRef = useRef(null);
  const completado = searchParams.get('completado') === 'true';

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    cargarItinerario();

    return () => {
      // Cleanup SSE al desmontar
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [id, isAuthenticated]);

  const cargarItinerario = async () => {
    try {
      setLoading(true);
      console.log('📍 Cargando itinerario:', id);

      const data = await itinerariosAPI.obtenerItinerario(id);

      console.log('✅ Itinerario cargado:', data);
      setItinerario(data);

      // Verificar si hay áreas pendientes de generar
      const tieneAreasPendientes = data.detalles?.some(
        d => !d.introduccion || d.introduccion === '⏳ Generando contenido detallado...'
      );

      if (tieneAreasPendientes) {
        iniciarSSE();
      }
    } catch (err) {
      console.error('❌ Error cargando itinerario:', err);
      setError('Error al cargar el itinerario. Intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  const iniciarSSE = () => {
    setGenerandoAreas(true);

    const eventSource = itinerariosAPI.conectarStreamAreas(id, {
      onInicio: (data) => {
        console.log('SSE inicio:', data.total_areas, 'áreas');
        setTotalAreas(data.total_areas);
        setAreasGeneradas(0);
      },

      onAreaCompletada: (data) => {
        console.log('SSE área completada:', data.area_nombre);
        setAreasGeneradas(prev => prev + 1);

        // Actualizar el detalle en el estado del itinerario
        setItinerario(prev => {
          if (!prev) return prev;

          const nuevosDetalles = prev.detalles.map(detalle => {
            if (detalle.id === data.detalle_id) {
              return {
                ...detalle,
                introduccion: data.contenido.introduccion,
                historia_contextual: data.contenido.historia_contextual,
                datos_curiosos: data.contenido.datos_curiosos,
                que_observar: data.contenido.que_observar,
                recomendacion: data.contenido.recomendacion
              };
            }
            return detalle;
          });

          return { ...prev, detalles: nuevosDetalles };
        });
      },

      onCompletado: () => {
        console.log('SSE: Todas las áreas generadas');
        setGenerandoAreas(false);
      },

      onError: (data) => {
        console.error('SSE error:', data.message);
        setGenerandoAreas(false);
      }
    });

    eventSourceRef.current = eventSource;
  };

  const handleIniciarVisita = async () => {
    try {
      console.log('🚀 Iniciando visita del itinerario:', id);
      await itinerariosAPI.iniciarItinerario(id);
      navigate(`/visita/${id}`);
    } catch (err) {
      console.error('❌ Error iniciando visita:', err);
      alert('Error al iniciar la visita. Intenta de nuevo.');
    }
  };

  const formatearFecha = (fecha) => {
    return new Date(fecha).toLocaleString('es-EC', {
      timeZone: 'America/Guayaquil',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };

  const esAreaPendiente = (detalle) => {
    return !detalle.introduccion || detalle.introduccion === '⏳ Generando contenido detallado...';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner message="Cargando itinerario..." />
      </div>
    );
  }

  if (error || !itinerario) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <span className="text-6xl">❌</span>
          <p className="text-xl text-gray-700 mt-4">{error || 'Itinerario no encontrado'}</p>
          <button onClick={() => navigate('/mis-itinerarios')} className="btn-primary mt-4">
            Volver a Mis Itinerarios
          </button>
        </div>
      </div>
    );
  }

  const estadoBadge = {
    generado: { bg: 'bg-blue-100', text: 'text-blue-700', icon: '🤖', label: 'Generado con IA' },
    activo: { bg: 'bg-green-100', text: 'text-green-700', icon: '▶️', label: 'En Progreso' },
    completado: { bg: 'bg-purple-100', text: 'text-purple-700', icon: '✅', label: 'Completado' },
    pausado: { bg: 'bg-yellow-100', text: 'text-yellow-700', icon: '⏸️', label: 'Pausado' },
    cancelado: { bg: 'bg-red-100', text: 'text-red-700', icon: '❌', label: 'Cancelado' },
  };

  const estado = estadoBadge[itinerario.estado] || estadoBadge.generado;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-5xl">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/mis-itinerarios')}
            className="text-gray-600 hover:text-gray-900 mb-4 inline-flex items-center gap-2"
          >
            <span>←</span>
            <span>Volver a Mis Itinerarios</span>
          </button>
        </div>

        {/* Mensaje de completado */}
        {completado && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
            <div className="flex items-center gap-4">
              <span className="text-5xl">🎉</span>
              <div>
                <h3 className="text-xl font-bold text-green-900 mb-1">
                  ¡Visita Completada!
                </h3>
                <p className="text-green-700">
                  Has completado tu recorrido por el Museo Pumapungo.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Barra de progreso SSE */}
        {generandoAreas && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="animate-spin w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
              <span className="text-blue-800 font-medium">
                Generando contenido con IA... ({areasGeneradas}/{totalAreas} áreas)
              </span>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                style={{ width: totalAreas > 0 ? `${(areasGeneradas / totalAreas) * 100}%` : '0%' }}
              ></div>
            </div>
          </div>
        )}

        {/* Card principal */}
        <div className="card mb-6">
          {/* Badge de estado */}
          <div className="flex items-center justify-between mb-6">
            <span className={`inline-flex items-center gap-2 px-4 py-2 ${estado.bg} ${estado.text} rounded-full text-sm font-medium`}>
              <span>{estado.icon}</span>
              <span>{estado.label}</span>
            </span>

            <div className="text-right">
              <div className="text-sm text-gray-600">Generado</div>
            </div>
          </div>

          {/* Título */}
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            {itinerario.titulo || 'Itinerario Personalizado del Museo Pumapungo'}
          </h1>

          {/* Descripción */}
          {itinerario.descripcion && (
            <p className="text-gray-700 leading-relaxed mb-6">
              {itinerario.descripcion}
            </p>
          )}

          {/* Métricas */}
          <div className="grid grid-cols-3 gap-4 p-6 bg-gray-50 rounded-lg mb-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-primary-600">
                {itinerario.duracion_total || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">Minutos</div>
            </div>

            <div className="text-center">
              <div className="text-3xl font-bold text-primary-600">
                {itinerario.detalles?.length || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">Áreas</div>
            </div>

            <div className="text-center">
              <div className="text-3xl font-bold text-primary-600">
                {itinerario.fecha_generacion ? formatearFecha(itinerario.fecha_generacion).split(',')[0] : 'N/A'}
              </div>
              <div className="text-sm text-gray-600 mt-1">Fecha</div>
            </div>
          </div>

          {/* Botón de iniciar visita */}
          {itinerario.estado === 'generado' && (
            <button
              onClick={handleIniciarVisita}
              disabled={generandoAreas}
              className={`w-full text-white px-8 py-4 rounded-lg font-semibold text-lg transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-3 ${
                generandoAreas
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-700 hover:to-blue-700'
              }`}
            >
              <span className="text-2xl">{generandoAreas ? '⏳' : '🚀'}</span>
              <span>{generandoAreas ? 'Esperando generación...' : 'Iniciar Visita Ahora'}</span>
            </button>
          )}

          {itinerario.estado === 'activo' && (
            <button
              onClick={() => navigate(`/visita/${id}`)}
              className="w-full bg-green-600 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-green-700 transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-3"
            >
              <span className="text-2xl">▶️</span>
              <span>Continuar Visita</span>
            </button>
          )}
        </div>

        {/* Tu Recorrido Personalizado */}
        <div className="card">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
            <span>🗺️</span>
            <span>Tu Recorrido Personalizado</span>
          </h2>

          {itinerario.detalles && itinerario.detalles.length > 0 ? (
            <div className="space-y-4">
              {itinerario.detalles
                .sort((a, b) => a.orden - b.orden)
                .map((detalle) => (
                  <div
                    key={detalle.id}
                    className={`border-2 rounded-lg p-6 transition-all duration-500 ${
                      esAreaPendiente(detalle)
                        ? 'border-gray-200 bg-gray-50 opacity-60'
                        : 'border-gray-200 hover:border-primary-300'
                    }`}
                  >
                    {/* Header del área */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-xl flex-shrink-0 ${
                          esAreaPendiente(detalle)
                            ? 'bg-gray-300 text-gray-600'
                            : 'bg-primary-500 text-white'
                        }`}>
                          {esAreaPendiente(detalle) ? (
                            <div className="animate-spin w-6 h-6 border-2 border-gray-500 border-t-transparent rounded-full"></div>
                          ) : (
                            detalle.orden
                          )}
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-gray-900">
                            {detalle.area?.nombre || 'Área'}
                          </h3>
                          <p className="text-gray-600 text-sm mt-1">
                            ⏱️ {detalle.tiempo_sugerido || 20} minutos •
                            📍 Piso {detalle.area?.piso || 1}
                            {detalle.area?.zona && ` • ${detalle.area.zona}`}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Contenido del área */}
                    {esAreaPendiente(detalle) ? (
                      <div className="flex items-center gap-3 text-gray-500 py-4">
                        <div className="animate-pulse flex-1">
                          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                        </div>
                      </div>
                    ) : (
                      <>
                        {/* Introducción */}
                        {detalle.introduccion && (
                          <p className="text-gray-700 mb-4 leading-relaxed">
                            {detalle.introduccion}
                          </p>
                        )}

                        {/* Datos curiosos */}
                        {detalle.datos_curiosos && detalle.datos_curiosos.length > 0 && (
                          <div className="mb-4">
                            <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                              <span>🧠</span>
                              <span>Datos curiosos:</span>
                            </h4>
                            <ul className="space-y-1">
                              {detalle.datos_curiosos.map((dato, idx) => (
                                <li key={idx} className="flex items-start gap-2 text-gray-700">
                                  <span className="text-amber-500">★</span>
                                  <span>{dato}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Qué observar */}
                        {detalle.que_observar && detalle.que_observar.length > 0 && (
                          <div className="mb-4">
                            <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                              <span>👀</span>
                              <span>Qué observar:</span>
                            </h4>
                            <ul className="space-y-1">
                              {detalle.que_observar.map((punto, idx) => (
                                <li key={idx} className="flex items-start gap-2 text-gray-700">
                                  <span className="text-primary-500">•</span>
                                  <span>{punto}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Puntos clave (legacy) */}
                        {detalle.puntos_clave && detalle.puntos_clave.length > 0 && (
                          <div className="mb-4">
                            <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                              <span>💡</span>
                              <span>Puntos clave:</span>
                            </h4>
                            <ul className="space-y-1">
                              {detalle.puntos_clave.map((punto, idx) => (
                                <li key={idx} className="flex items-start gap-2 text-gray-700">
                                  <span className="text-primary-500">•</span>
                                  <span>{punto}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Recomendación */}
                        {detalle.recomendacion && (
                          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                            <p className="text-green-800 flex items-start gap-2">
                              <span className="text-xl">✨</span>
                              <span>{detalle.recomendacion}</span>
                            </p>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <span className="text-5xl mb-4 block">📭</span>
              <p>No hay áreas en este itinerario</p>
            </div>
          )}
        </div>

        {/* Información del modelo IA */}
        {itinerario.modelo_ia_usado && (
          <div className="mt-6 p-4 bg-gray-100 rounded-lg">
            <p className="text-sm text-gray-600 text-center">
              🤖 Generado con <span className="font-semibold">{itinerario.modelo_ia_usado}</span>
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default VerItinerarioPage;
