import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { itinerariosAPI, detallesAPI } from '../services/api';
import LoadingSpinner from '../components/Layout/LoadingSpinner';
import EvaluacionModal from '../components/EvaluacionModal';
import GeneracionProgresivaIndicador from '../components/GeneracionProgresivaIndicador';


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
  const [mostrarEvaluacion, setMostrarEvaluacion] = useState(false);

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

  

  // 🔥 NUEVO: Función para volver a la sala anterior
  const handleVolverSalaAnterior = async () => {
    if (areaActualIndex <= 0) {
      alert('Ya estás en la primera sala del recorrido');
      return;
    }

    const anteriorIndex = areaActualIndex - 1;
    const areaAnterior = detalles[anteriorIndex];

    try {
      // Si el área anterior estaba saltada, reactivarla
      if (areaAnterior.skip) {
        await detallesAPI.reactivarArea(areaAnterior.id);
        setDetalles(prev => prev.map(d => 
          d.id === areaAnterior.id ? { ...d, skip: false, visitado: false } : d
        ));
      }
      
      // Si el área anterior estaba visitada, desmarcarla
      if (areaAnterior.visitado) {
        await detallesAPI.desmarcarArea(areaAnterior.id);
        setDetalles(prev => prev.map(d => 
          d.id === areaAnterior.id ? { ...d, visitado: false } : d
        ));
      }

      // Volver al índice anterior
      setAreaActualIndex(anteriorIndex);
    } catch (err) {
      console.error('❌ Error volviendo a sala anterior:', err);
      // Aunque falle la API, permitimos volver visualmente
      setAreaActualIndex(anteriorIndex);
    }
  };

  const handleMostrarEvaluacion = () => {
    setMostrarEvaluacion(true);
  };

  const handleEnviarEvaluacion = async (evaluacion) => {
    try {
      // Guardar evaluación
      await itinerariosAPI.guardarEvaluacion(parseInt(id), evaluacion);
      
      // Completar itinerario
      await itinerariosAPI.actualizar(id, { estado: 'completado' });
      
      setMostrarEvaluacion(false);
      
      // Mensaje de agradecimiento
      alert('¡Gracias por tu evaluación! Tu opinión nos ayuda a mejorar.');
      
      // Redirigir al detalle del itinerario
      navigate(`/itinerarios/${id}`);
    } catch (err) {
      console.error('❌ Error guardando evaluación:', err);
      alert('Hubo un error al guardar tu evaluación. Por favor, intenta de nuevo.');
    }
  };

  const formatearTiempo = (segundos) => {
    const h = Math.floor(segundos / 3600);
    const m = Math.floor((segundos % 3600) / 60);
    const s = segundos % 60;
    
    if (h > 0) {
      return `${h}h ${m}m ${s}s`;
    }
    return `${m}m ${s}s`;
  };

  const obtenerInstruccionesNavegacion = (areaActual, areaSiguiente) => {
    if (!areaActual?.area || !areaSiguiente?.area) return [];
    
    const pisoActual = areaActual.area.piso;
    const pisoSiguiente = areaSiguiente.area.piso;
    
    const instrucciones = [];
    
    if (pisoActual !== pisoSiguiente) {
      if (pisoSiguiente > pisoActual) {
        instrucciones.push(`Sube al piso ${pisoSiguiente}`);
      } else {
        instrucciones.push(`Baja al piso ${pisoSiguiente}`);
      }
    }
    
    instrucciones.push(`Dirígete a la ${areaSiguiente.area.zona || 'zona indicada'}`);
    instrucciones.push(`Busca "${areaSiguiente.area.nombre}"`);
    
    return instrucciones;
  };

  if (loading) return <LoadingSpinner />;

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <div className="text-4xl mb-4">❌</div>
          <h2 className="text-xl font-semibold text-red-800 mb-2">Error</h2>
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  const areaActual = detalles[areaActualIndex];
  const areaSiguiente = detalles[areaActualIndex + 1];
  
  const areasVisitadas = detalles.filter(d => d.visitado).length;
  const areasOmitidas = detalles.filter(d => d.skip).length;
  const areasPendientes = detalles.length - areasVisitadas - areasOmitidas;
  const progreso = detalles.length > 0 
    ? Math.round((areasVisitadas / detalles.length) * 100)
    : 0;
  
  const todasVisitadas = areasVisitadas + areasOmitidas === detalles.length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-museo-cream to-white">
      {/* Header sticky */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button onClick={() => navigate('/mis-itinerarios')} className="text-gray-600 hover:text-gray-900">
                ← Volver
              </button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Visita en Progreso</h1>
                <p className="text-sm text-gray-600">{itinerario.titulo || 'Explorando la Historia de Cuenca'}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-6">
              <div className="text-right">
                <div className="text-2xl font-bold text-primary-600">
                  {formatearTiempo(tiempoTranscurrido)}
                </div>
                <div className="text-xs text-gray-600">Tiempo</div>
              </div>
              
              <div className="text-right">
                <div className="text-2xl font-bold text-green-600">{progreso}%</div>
                <div className="text-xs text-gray-600">Progreso</div>
              </div>
            </div>
          </div>
          
          <div className="mt-3">
            <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div 
                className="bg-gradient-to-r from-green-500 to-blue-500 h-full rounded-full transition-all duration-500"
                style={{ width: `${progreso}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Contenido principal */}
      <div className="container mx-auto px-4 mt-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Columna izquierda: Área actual */}
          <div className="lg:col-span-2 space-y-6">
            {areaActual && !todasVisitadas ? (
              <div className="card border-2 border-primary-200">
                {/* Encabezado del área */}
                <div className="flex items-start justify-between mb-6">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-600 text-white rounded-full text-xl font-bold shadow-lg">
                        {areaActualIndex + 1}
                      </span>
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900">
                          {areaActual.area?.nombre || 'Área del museo'}
                        </h2>
                        <div className="flex items-center gap-3 text-sm text-gray-600 mt-1">
                          <span className="flex items-center gap-1">
                            <span>⏱️</span>
                            <span>Tiempo sugerido: {areaActual.tiempo_sugerido || 20} minutos</span>
                          </span>
                          {areaActual.area?.piso && (
                            <span className="flex items-center gap-1">
                              <span>📍</span>
                              <span>Piso {areaActual.area.piso}</span>
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Introducción */}
                {areaActual.introduccion && (
                  <div className="mb-6 p-4 bg-primary-50 rounded-lg border border-primary-100">
                    <p className="text-gray-800 leading-relaxed">{areaActual.introduccion}</p>
                  </div>
                )}

                {/* Historia Contextual */}
                {areaActual.historia_contextual && (
                  <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
                    <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                      <span>📖</span>
                      <span>Historia y Contexto:</span>
                    </h3>
                    <p className="text-blue-800 leading-relaxed">{areaActual.historia_contextual}</p>
                  </div>
                )}

                {/* Datos Curiosos */}
                {areaActual.datos_curiosos && areaActual.datos_curiosos.length > 0 && (
                  <div className="mb-6 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                    <h3 className="font-semibold text-yellow-900 mb-3 flex items-center gap-2">
                      <span>✨</span>
                      <span>Datos Curiosos:</span>
                    </h3>
                    <div className="space-y-2">
                      {areaActual.datos_curiosos.map((dato, idx) => (
                        <div key={idx} className="flex items-start gap-3 text-yellow-800">
                          <span className="flex-shrink-0 w-6 h-6 bg-yellow-200 rounded-full flex items-center justify-center text-xs font-bold">
                            {idx + 1}
                          </span>
                          <p className="flex-1">{dato}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Qué Observar */}
                {areaActual.que_observar && areaActual.que_observar.length > 0 && (
                  <div className="mb-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
                    <h3 className="font-semibold text-purple-900 mb-3 flex items-center gap-2">
                      <span>👀</span>
                      <span>Qué Observar:</span>
                    </h3>
                    <div className="space-y-2">
                      {areaActual.que_observar.map((item, idx) => (
                        <div key={idx} className="flex items-start gap-3 text-purple-800">
                          <span className="flex-shrink-0 w-6 h-6 bg-purple-200 rounded-full flex items-center justify-center text-xs font-bold">
                            {idx + 1}
                          </span>
                          <p className="flex-1">{item}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recomendación */}
                {areaActual.recomendacion && (
                  <div className="mb-6 p-4 bg-green-50 rounded-lg border border-green-200">
                    <h3 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
                      <span>💡</span>
                      <span>Recomendación:</span>
                    </h3>
                    <p className="text-green-800 leading-relaxed">{areaActual.recomendacion}</p>
                  </div>
                )}

                {/* 🔥 NUEVA SECCIÓN: Botones de acción con VOLVER */}
                <div className="space-y-3">
                  {/* Fila 1: Botón Volver a Sala Anterior (solo si NO es la primera) */}
                  {areaActualIndex > 0 && (
                    <button
                      onClick={handleVolverSalaAnterior}
                      className="w-full bg-gradient-to-r from-amber-500 to-orange-500 text-white px-6 py-3 rounded-lg font-semibold hover:from-amber-600 hover:to-orange-600 transition-all shadow-lg flex items-center justify-center gap-2"
                    >
                      <span>←</span>
                      <span>Volver a Sala Anterior</span>
                    </button>
                  )}

                  {/* Fila 2: Botones Marcar y Saltar */}
                  <div className="flex gap-4">
                    <button
                      onClick={() => handleMarcarVisitada(areaActual.id)}
                      className="flex-1 bg-gradient-to-r from-green-600 to-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-green-700 hover:to-blue-700 transition-all shadow-lg flex items-center justify-center gap-2"
                    >
                      <span>✅</span>
                      <span>Marcar como Visitada</span>
                    </button>
                    
                    <button
                      onClick={() => handleSaltarArea(areaActual.id)}
                      className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors flex items-center gap-2"
                    >
                      <span>⏭️</span>
                      <span>Saltar</span>
                    </button>
                  </div>
                </div>
              </div>
            ) : todasVisitadas ? (
              <div className="card text-center py-12">
                <div className="text-8xl mb-4">🎉</div>
                <h2 className="text-3xl font-bold text-gray-900 mb-3">¡Visita Completada!</h2>
                <p className="text-lg text-primary-600 font-semibold mb-6">
                  Tiempo total: {formatearTiempo(tiempoTranscurrido)}
                </p>
                <button 
                  onClick={handleMostrarEvaluacion} 
                  className="btn-primary inline-flex items-center gap-2 text-lg"
                >
                  <span>🏁</span>
                  <span>Finalizar Visita</span>
                </button>
              </div>
            ) : null}

            {/* Siguiente parada */}
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
            {/* Plano del Museo */}
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
                                ? 'bg-primary-500 text-white'
                                : detalle.visitado
                                ? 'bg-green-100 text-green-700'
                                : detalle.skip
                                ? 'bg-gray-100 text-gray-500 line-through'
                                : 'bg-gray-50 text-gray-600'
                            }`}
                          >
                            {detalle.orden}. {detalle.area?.nombre?.substring(0, 15)}...
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Tu Recorrido */}
            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <span>📝</span>
                <span>Tu Recorrido</span>
              </h3>
              
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {detalles.map((detalle, index) => (
                  <div
                    key={detalle.id}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      detalle.id === areaActual?.id
                        ? 'bg-primary-50 border-primary-500 shadow-md'
                        : detalle.visitado
                        ? 'bg-green-50 border-green-200'
                        : detalle.skip
                        ? 'bg-gray-50 border-gray-200 opacity-60'
                        : 'bg-white border-gray-200'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                        detalle.id === areaActual?.id
                          ? 'bg-primary-500 text-white'
                          : detalle.visitado
                          ? 'bg-green-500 text-white'
                          : detalle.skip
                          ? 'bg-gray-300 text-gray-600'
                          : 'bg-gray-200 text-gray-700'
                      }`}>
                        {detalle.visitado ? '✓' : detalle.skip ? '⏭' : detalle.orden}
                      </div>
                      
                      <div className="flex-1">
                        <div className="font-medium text-sm text-gray-900">
                          {detalle.area?.nombre || 'Área del museo'}
                        </div>
                        <div className="text-xs text-gray-600 mt-1 flex items-center gap-2">
                          <span>⏱️ {detalle.tiempo_sugerido || 20} min</span>
                          <span>•</span>
                          <span>Piso {detalle.area?.piso || 1}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="text-center p-2 bg-green-50 rounded">
                    <div className="text-2xl font-bold text-green-600">{areasVisitadas}</div>
                    <div className="text-gray-600 text-xs">Visitadas</div>
                  </div>
                  <div className="text-center p-2 bg-blue-50 rounded">
                    <div className="text-2xl font-bold text-blue-600">{areasPendientes}</div>
                    <div className="text-gray-600 text-xs">Pendientes</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modal de Evaluación */}
      {mostrarEvaluacion && (
        <EvaluacionModal
  isOpen={mostrarEvaluacion}
  onClose={() => setMostrarEvaluacion(false)}
  onSubmit={handleEnviarEvaluacion}
  itinerarioId={parseInt(id)}
/>
      )}
    </div>
  );
};

export default VisitaEnProgresoPage;