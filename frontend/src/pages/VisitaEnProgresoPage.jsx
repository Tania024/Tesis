import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { itinerariosAPI, detallesAPI } from '../services/api';
import LoadingSpinner from '../components/Layout/LoadingSpinner';

const VisitaEnProgresoPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [itinerario, setItinerario] = useState(null);
  const [detalles, setDetalles] = useState([]);
  const [areaActualIndex, setAreaActualIndex] = useState(0);
  const [tiempoInicio, setTiempoInicio] = useState(null);
  const [tiempoTranscurrido, setTiempoTranscurrido] = useState(0);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    cargarItinerario();
    setTiempoInicio(Date.now());
  }, [id, isAuthenticated]);

  useEffect(() => {
    if (!tiempoInicio) return;
    
    const interval = setInterval(() => {
      const transcurrido = Math.floor((Date.now() - tiempoInicio) / 1000);
      setTiempoTranscurrido(transcurrido);
    }, 1000);

    return () => clearInterval(interval);
  }, [tiempoInicio]);

  const cargarItinerario = async () => {
    try {
      setLoading(true);
      const data = await itinerariosAPI.obtenerItinerario(id);
      setItinerario(data);
      
      if (data.detalles) {
        const detallesOrdenados = [...data.detalles].sort((a, b) => a.orden - b.orden);
        setDetalles(detallesOrdenados);
        
        const primeraNoVisitada = detallesOrdenados.findIndex(d => !d.visitado && !d.skip);
        if (primeraNoVisitada !== -1) {
          setAreaActualIndex(primeraNoVisitada);
        }
      }
    } catch (err) {
      console.error('❌ Error cargando itinerario:', err);
      setError('Error al cargar el itinerario.');
    } finally {
      setLoading(false);
    }
  };

  const handleMarcarVisitada = async (detalleId) => {
    try {
      await detallesAPI.completarArea(detalleId);
      setDetalles(prev => prev.map(d => 
        d.id === detalleId ? { ...d, visitado: true } : d
      ));
      
      const siguienteIndex = areaActualIndex + 1;
      if (siguienteIndex < detalles.length) {
        setAreaActualIndex(siguienteIndex);
      }
    } catch (err) {
      console.error('❌ Error:', err);
    }
  };

  const handleSaltarArea = async (detalleId) => {
    try {
      await detallesAPI.omitirArea(detalleId);
      setDetalles(prev => prev.map(d => 
        d.id === detalleId ? { ...d, skip: true } : d
      ));
      
      const siguienteIndex = areaActualIndex + 1;
      if (siguienteIndex < detalles.length) {
        setAreaActualIndex(siguienteIndex);
      }
    } catch (err) {
      console.error('❌ Error:', err);
    }
  };

  const handleFinalizarVisita = async () => {
    try {
      await itinerariosAPI.completarItinerario(id);
      navigate(`/itinerario/${id}?completado=true`);
    } catch (err) {
      console.error('❌ Error:', err);
    }
  };

  const formatearTiempo = (segundos) => {
    const horas = Math.floor(segundos / 3600);
    const minutos = Math.floor((segundos % 3600) / 60);
    const segs = segundos % 60;
    
    if (horas > 0) {
      return `${horas}h ${minutos}m`;
    }
    return `${minutos}m ${segs}s`;
  };

  const obtenerInstruccionesNavegacion = (areaActual, areaSiguiente) => {
    if (!areaActual || !areaSiguiente) return null;
    
    const pisoActual = areaActual.area?.piso || 1;
    const pisoSiguiente = areaSiguiente.area?.piso || 1;
    const zonaActual = areaActual.area?.zona || 'central';
    const zonaSiguiente = areaSiguiente.area?.zona || 'central';
    
    let instrucciones = [];
    
    if (pisoActual !== pisoSiguiente) {
      if (pisoSiguiente > pisoActual) {
        instrucciones.push(`🔼 Sube al Piso ${pisoSiguiente}`);
      } else {
        instrucciones.push(`🔽 Baja al Piso ${pisoSiguiente}`);
      }
    } else {
      instrucciones.push(`📍 Mismo piso (Piso ${pisoActual})`);
    }
    
    if (zonaActual !== zonaSiguiente) {
      const direcciones = {
        'norte': '⬆️ Dirígete hacia el norte',
        'sur': '⬇️ Dirígete hacia el sur',
        'este': '➡️ Dirígete hacia el este',
        'oeste': '⬅️ Dirígete hacia el oeste',
        'central': '🎯 Dirígete al centro',
        'exterior': '🌳 Sal al exterior'
      };
      instrucciones.push(direcciones[zonaSiguiente] || `Zona ${zonaSiguiente}`);
    }
    
    return instrucciones;
  };

  const calcularProgreso = () => {
    const visitadas = detalles.filter(d => d.visitado).length;
    const total = detalles.length;
    return total > 0 ? Math.round((visitadas / total) * 100) : 0;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner message="Cargando tu visita..." />
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
            Volver
          </button>
        </div>
      </div>
    );
  }

  const areaActual = detalles[areaActualIndex];
  const areaSiguiente = detalles[areaActualIndex + 1];
  const progreso = calcularProgreso();
  const areasVisitadas = detalles.filter(d => d.visitado).length;
  const todasVisitadas = areasVisitadas === detalles.length;

  return (
    <div className="min-h-screen bg-gray-50 pb-8">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button onClick={() => navigate('/mis-itinerarios')} className="text-gray-600 hover:text-gray-900">
                ← Volver
              </button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Visita en Progreso</h1>
                <p className="text-sm text-gray-600">{itinerario.titulo || 'Itinerario'}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-primary-600">
                  {formatearTiempo(tiempoTranscurrido)}
                </div>
                <div className="text-xs text-gray-500">Tiempo</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{progreso}%</div>
                <div className="text-xs text-gray-500">Progreso</div>
              </div>
            </div>
          </div>
          
          <div className="mt-4 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-primary-500 to-green-500 transition-all duration-500" style={{ width: `${progreso}%` }} />
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6 max-w-7xl">
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Columna izquierda: Área actual */}
          <div className="lg:col-span-2 space-y-6">
            {!todasVisitadas && areaActual ? (
              <div className="card">
                <div className="mb-6">
                  <span className="inline-block px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium mb-2">
                    📍 Estás aquí
                  </span>
                  <h2 className="text-3xl font-bold text-gray-900 mb-2">
                    {areaActual.area?.nombre || 'Área'}
                  </h2>
                  <p className="text-gray-600">
                    Área {areaActualIndex + 1} de {detalles.length} • {areaActual.tiempo_sugerido || 20} minutos
                  </p>
                </div>

                <div className="flex gap-3 mb-6">
                  <button onClick={() => handleMarcarVisitada(areaActual.id)} className="flex-1 bg-green-600 text-white px-6 py-4 rounded-lg font-semibold hover:bg-green-700 transition-colors">
                    ✓ Marcar como Visitada
                  </button>
                  <button onClick={() => handleSaltarArea(areaActual.id)} className="bg-gray-200 text-gray-700 px-6 py-4 rounded-lg font-semibold hover:bg-gray-300 transition-colors">
                    Saltar →
                  </button>
                </div>

                <div className="border-t-2 border-gray-200 pt-6 space-y-8">
                  {/* Introducción */}
                  {areaActual.introduccion && (
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <p className="text-gray-700 leading-relaxed">
                        {areaActual.introduccion}
                      </p>
                    </div>
                  )}

                  {/* 📖 Historia y Contexto */}
                  {areaActual.historia_contextual && (
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                        <span>📖</span>
                        <span>Historia y Contexto</span>
                      </h3>
                      <div className="prose prose-gray max-w-none">
                        <p className="text-gray-700 leading-relaxed whitespace-pre-line">
                          {areaActual.historia_contextual}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* 💡 ¿Sabías que...? */}
                  {areaActual.datos_curiosos && areaActual.datos_curiosos.length > 0 && (
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                        <span>💡</span>
                        <span>¿Sabías que...?</span>
                      </h3>
                      <div className="bg-blue-50 rounded-lg p-6 space-y-4">
                        {areaActual.datos_curiosos.map((dato, idx) => (
                          <div key={idx} className="flex items-start gap-3">
                            <span className="flex-shrink-0 text-2xl">🔹</span>
                            <p className="text-gray-800 leading-relaxed">{dato}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 👀 Qué Observar */}
                  {areaActual.que_observar && areaActual.que_observar.length > 0 && (
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                        <span>👀</span>
                        <span>Qué Observar</span>
                      </h3>
                      <div className="bg-purple-50 rounded-lg p-6 space-y-4">
                        {areaActual.que_observar.map((observacion, idx) => (
                          <div key={idx} className="flex items-start gap-3">
                            <span className="flex-shrink-0 w-6 h-6 bg-purple-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
                              {idx + 1}
                            </span>
                            <p className="text-gray-800 leading-relaxed">{observacion}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Puntos clave (legacy) */}
                  {areaActual.puntos_clave && areaActual.puntos_clave.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <span>💡</span>
                        <span>Puntos clave:</span>
                      </h3>
                      <ul className="space-y-2">
                        {areaActual.puntos_clave.map((punto, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-primary-500 mt-1">•</span>
                            <span className="text-gray-700">{punto}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Recomendación */}
                  {areaActual.recomendacion && (
                    <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                      <h3 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
                        <span>✨</span>
                        <span>Recomendación:</span>
                      </h3>
                      <p className="text-green-800 leading-relaxed">{areaActual.recomendacion}</p>
                    </div>
                  )}
                </div>
              </div>
            ) : todasVisitadas ? (
              <div className="card text-center py-12">
                <div className="text-8xl mb-4">🎉</div>
                <h2 className="text-3xl font-bold text-gray-900 mb-3">¡Visita Completada!</h2>
                <p className="text-lg text-primary-600 font-semibold mb-6">
                  Tiempo total: {formatearTiempo(tiempoTranscurrido)}
                </p>
                <button onClick={handleFinalizarVisita} className="btn-primary inline-flex items-center gap-2 text-lg">
                  <span>🏁</span>
                  <span>Finalizar Visita</span>
                </button>
              </div>
            ) : null}

            {!todasVisitadas && areaSiguiente && (
              <div className="card bg-gradient-to-r from-purple-50 to-blue-50 border-2 border-purple-200">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <span>🧭</span>
                  <span>Siguiente parada:</span>
                </h3>
                
                <div className="mb-4">
                  <h4 className="text-xl font-bold text-purple-900">
                    {areaSiguiente.area?.nombre || 'Próxima área'}
                  </h4>
                  <p className="text-purple-700">
                    ⏱️ Tiempo estimado: {areaSiguiente.tiempo_sugerido || 20} minutos
                  </p>
                </div>

                <div className="bg-white rounded-lg p-4 border border-purple-200">
                  <h5 className="font-semibold text-gray-900 mb-3">📍 Cómo llegar:</h5>
                  <div className="space-y-2">
                    {obtenerInstruccionesNavegacion(areaActual, areaSiguiente)?.map((instruccion, idx) => (
                      <div key={idx} className="flex items-center gap-3 text-gray-700">
                        <span className="flex-shrink-0 w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center text-xs font-bold text-purple-700">
                          {idx + 1}
                        </span>
                        <span>{instruccion}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Columna derecha: Plano y Recorrido */}
          <div className="space-y-6">
            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <span>🗺️</span>
                <span>Plano del Museo</span>
              </h3>
              
              <div className="space-y-4">
                {[1, 2, 3].map(piso => {
                  const areasPiso = detalles.filter(d => d.area?.piso === piso);
                  if (areasPiso.length === 0) return null;
                  
                  return (
                    <div key={piso} className="border border-gray-200 rounded-lg p-3">
                      <div className="font-semibold text-sm text-gray-700 mb-2">
                        Piso {piso}
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        {areasPiso.map(detalle => (
                          <div
                            key={detalle.id}
                            className={`p-2 rounded text-xs font-medium text-center ${
                              detalle.id === areaActual?.id
                                ? 'bg-blue-500 text-white animate-pulse'
                                : detalle.visitado
                                ? 'bg-green-100 text-green-700'
                                : detalle.skip
                                ? 'bg-gray-100 text-gray-500'
                                : 'bg-gray-50 text-gray-700'
                            }`}
                          >
                            {detalle.id === areaActual?.id && '📍 '}
                            {detalle.orden}. {detalle.area?.nombre?.substring(0, 15)}...
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <span>📋</span>
                <span>Tu Recorrido</span>
              </h3>
              
              <div className="space-y-3">
                {detalles.map((detalle, idx) => (
                  <div
                    key={detalle.id}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      detalle.id === areaActual?.id
                        ? 'border-blue-500 bg-blue-50'
                        : detalle.visitado
                        ? 'border-green-300 bg-green-50'
                        : detalle.skip
                        ? 'border-gray-200 bg-gray-50 opacity-60'
                        : 'border-gray-200'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex-shrink-0">
                        {detalle.visitado ? (
                          <span className="text-2xl">✅</span>
                        ) : detalle.skip ? (
                          <span className="text-2xl">⏭️</span>
                        ) : detalle.id === areaActual?.id ? (
                          <span className="text-2xl animate-bounce">📍</span>
                        ) : (
                          <span className="text-2xl">⏸️</span>
                        )}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900 truncate">
                          {idx + 1}. {detalle.area?.nombre || 'Área'}
                        </div>
                        <div className="text-sm text-gray-600">
                          ⏱️ {detalle.tiempo_sugerido || 20} min • Piso {detalle.area?.piso || 1}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="text-center p-2 bg-green-50 rounded">
                    <div className="font-bold text-green-700">{areasVisitadas}</div>
                    <div className="text-gray-600">Visitadas</div>
                  </div>
                  <div className="text-center p-2 bg-blue-50 rounded">
                    <div className="font-bold text-blue-700">
                      {detalles.length - areasVisitadas}
                    </div>
                    <div className="text-gray-600">Pendientes</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VisitaEnProgresoPage;