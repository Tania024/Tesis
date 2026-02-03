import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { itinerariosAPI } from '../services/api';
import LoadingSpinner from '../components/Layout/LoadingSpinner';

const MisItinerariosPage = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  
  const [itinerarios, setItinerarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    cargarItinerarios();
  }, [user, isAuthenticated]);

  const cargarItinerarios = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('📋 Cargando itinerarios para visitante:', user.visitante_id);

      const data = await itinerariosAPI.listar(user.visitante_id);
      
      console.log('✅ Respuesta del backend:', data);
      
      // ✅ CORRECCIÓN: El backend retorna {total: 0, itinerarios: []}
      if (data && Array.isArray(data.itinerarios)) {
        console.log('✅ Itinerarios encontrados:', data.itinerarios.length);
        setItinerarios(data.itinerarios);
      } else if (Array.isArray(data)) {
        console.log('✅ Itinerarios (array directo):', data.length);
        setItinerarios(data);
      } else {
        console.warn('⚠️ Formato inesperado de respuesta:', data);
        setItinerarios([]);
      }
    } catch (err) {
      console.error('❌ Error cargando itinerarios:', err);
      
      if (err.response?.status === 404) {
        // No hay itinerarios, está bien
        console.log('ℹ️ No se encontraron itinerarios (404)');
        setItinerarios([]);
      } else {
        setError('Error al cargar tus itinerarios. Intenta de nuevo.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVerItinerario = (id) => {
    navigate(`/itinerario/${id}`);
  };

  const handleGenerarNuevo = () => {
    console.log('🚀 Navegando a generar itinerario...');
    navigate('/generar-itinerario');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner message="Cargando tus itinerarios..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-6xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-4xl">📋</span>
            <h1 className="text-4xl font-bold text-gray-900">Mis Itinerarios</h1>
          </div>
          <p className="text-gray-600 text-lg">
            Aquí encontrarás todos los itinerarios que has generado
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2 text-red-800">
              <span className="text-xl">⚠️</span>
              <p>{error}</p>
            </div>
          </div>
        )}

        {/* Lista de itinerarios */}
        {itinerarios.length === 0 ? (
          // Estado vacío
          <div className="card text-center py-16">
            <div className="mb-6">
              <span className="text-8xl">📭</span>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-3">
              Aún no tienes itinerarios
            </h2>
            <p className="text-gray-600 mb-6 max-w-md mx-auto">
              Genera tu primer itinerario personalizado con IA y comienza a explorar el museo
            </p>
            <button
              onClick={handleGenerarNuevo}
              className="btn-primary inline-flex items-center gap-2"
            >
              <span>🤖</span>
              <span>Generar Mi Primer Itinerario</span>
            </button>
          </div>
        ) : (
          // Grid de itinerarios
          <div>
            <div className="flex justify-between items-center mb-6">
              <p className="text-gray-600">
                {itinerarios.length} {itinerarios.length === 1 ? 'itinerario' : 'itinerarios'} encontrados
              </p>
              <button
                onClick={handleGenerarNuevo}
                className="btn-primary inline-flex items-center gap-2"
              >
                <span>➕</span>
                <span>Generar Nuevo Itinerario</span>
              </button>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {itinerarios.map((itinerario) => (
                <div
                  key={itinerario.id}
                  className="card hover:shadow-xl transition-shadow cursor-pointer"
                  onClick={() => handleVerItinerario(itinerario.id)}
                >
                  {/* Badge de estado */}
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      {itinerario.estado === 'completado' && (
                        <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                          <span>✅</span> Completado
                        </span>
                      )}
                      {itinerario.estado === 'activo' && (
                        <span className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                          <span>⏳</span> En Progreso
                        </span>
                      )}
                      {itinerario.estado === 'generado' && (
                        <span className="inline-flex items-center gap-1 px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-medium">
                          <span>📋</span> Generado
                        </span>
                      )}
                    </div>
                    
                    {/* Valoración */}
                    {itinerario.puntuacion && (
                      <div className="flex items-center gap-1">
                        <span className="text-yellow-500">⭐</span>
                        <span className="font-semibold text-gray-900">
                          {itinerario.puntuacion}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Información */}
                  <h3 className="text-xl font-bold text-gray-900 mb-3">
                    Itinerario #{itinerario.id}
                  </h3>

                  <div className="space-y-2 text-sm text-gray-600 mb-4">
                    <div className="flex items-center gap-2">
                      <span>⏱️</span>
                      <span>Duración: {itinerario.duracion_total || 0} minutos</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span>📍</span>
                      <span>{itinerario.detalles?.length || 0} {itinerario.detalles?.length === 1 ? 'área' : 'áreas'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span>📅</span>
                      <span>{new Date(itinerario.fecha_generacion).toLocaleDateString('es-EC', { timeZone: 'America/Guayaquil' })}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span>🤖</span>
                      <span className="text-xs">{itinerario.modelo_ia || 'IA'}</span>
                    </div>
                  </div>

                  {/* Botón */}
                  <button
                    className="w-full bg-primary-500 text-white px-4 py-2 rounded-lg font-medium hover:bg-primary-600 transition-colors"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleVerItinerario(itinerario.id);
                    }}
                  >
                    {itinerario.estado === 'pendiente' ? 'Iniciar Visita' : 'Ver Detalles'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MisItinerariosPage;