import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { itinerariosAPI } from '../services/api';
import LoadingSpinner from '../components/Layout/LoadingSpinner';

const MisItinerariosPage = () => {
  const { user } = useAuth();
  const [itinerarios, setItinerarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    cargarItinerarios();
  }, []);

  const cargarItinerarios = async () => {
    try {
      setLoading(true);
      const data = await itinerariosAPI.listarItinerariosVisitante(user.visitante_id);
      setItinerarios(data.itinerarios || []);
    } catch (err) {
      console.error('Error cargando itinerarios:', err);
      setError('Error al cargar tus itinerarios');
    } finally {
      setLoading(false);
    }
  };

  const getEstadoBadge = (estado) => {
    const estados = {
      generado: { color: 'bg-blue-100 text-blue-700', text: '📄 Generado' },
      activo: { color: 'bg-green-100 text-green-700', text: '▶️ En progreso' },
      completado: { color: 'bg-purple-100 text-purple-700', text: '✓ Completado' },
    };
    return estados[estado] || estados.generado;
  };

  const formatearFecha = (fecha) => {
    return new Date(fecha).toLocaleDateString('es-EC', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) return <LoadingSpinner message="Cargando tus itinerarios..." />;

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            📋 Mis Itinerarios
          </h1>
          <p className="text-xl text-gray-600">
            Aquí encontrarás todos los itinerarios que has generado
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
            <p className="text-red-700">{error}</p>
            <button onClick={cargarItinerarios} className="btn-primary mt-4">
              Reintentar
            </button>
          </div>
        )}

        {/* Sin itinerarios */}
        {!loading && itinerarios.length === 0 && (
          <div className="card text-center py-16">
            <div className="text-6xl mb-6">📭</div>
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Aún no tienes itinerarios
            </h3>
            <p className="text-gray-600 mb-8 max-w-md mx-auto">
              Genera tu primer itinerario personalizado con IA y comienza a explorar el museo
            </p>
            <Link to="/generar" className="btn-primary inline-block">
              🤖 Generar Mi Primer Itinerario
            </Link>
          </div>
        )}

        {/* Lista de itinerarios */}
        {itinerarios.length > 0 && (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {itinerarios.map(itinerario => {
                const estado = getEstadoBadge(itinerario.estado);
                
                return (
                  <div key={itinerario.id} className="card hover:shadow-xl transition-shadow">
                    {/* Header */}
                    <div className="flex justify-between items-start mb-4">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${estado.color}`}>
                        {estado.text}
                      </span>
                      <span className="text-sm text-gray-500">
                        ID: {itinerario.id}
                      </span>
                    </div>

                    {/* Título */}
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">
                      {itinerario.titulo}
                    </h3>

                    {/* Descripción */}
                    <p className="text-gray-600 mb-4 line-clamp-2">
                      {itinerario.descripcion}
                    </p>

                    {/* Stats */}
                    <div className="grid grid-cols-3 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary-600">
                          {itinerario.duracion_total}
                        </div>
                        <div className="text-xs text-gray-600">minutos</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary-600">
                          {itinerario.detalles?.length || 0}
                        </div>
                        <div className="text-xs text-gray-600">áreas</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary-600">
                          {itinerario.puntuacion || '-'}
                        </div>
                        <div className="text-xs text-gray-600">rating</div>
                      </div>
                    </div>

                    {/* Metadata */}
                    <div className="space-y-2 text-sm text-gray-600 mb-6">
                      <div className="flex items-center">
                        <span className="mr-2">🤖</span>
                        <span>Generado con {itinerario.modelo_ia_usado}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="mr-2">📅</span>
                        <span>{formatearFecha(itinerario.fecha_generacion)}</span>
                      </div>
                      {itinerario.fecha_inicio && (
                        <div className="flex items-center">
                          <span className="mr-2">▶️</span>
                          <span>Iniciado: {formatearFecha(itinerario.fecha_inicio)}</span>
                        </div>
                      )}
                    </div>

                    {/* Acciones */}
                    <div className="flex gap-3">
                      <Link
                        to={`/itinerario/${itinerario.id}`}
                        className="flex-1 btn-primary text-center"
                      >
                        Ver Detalle
                      </Link>
                      
                      {itinerario.estado === 'generado' && (
                        <Link
                          to={`/visita/${itinerario.id}`}
                          className="flex-1 btn-secondary text-center"
                        >
                          Iniciar Visita
                        </Link>
                      )}
                      
                      {itinerario.estado === 'activo' && (
                        <Link
                          to={`/visita/${itinerario.id}`}
                          className="flex-1 bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors text-center"
                        >
                          Continuar
                        </Link>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* CTA para generar otro */}
            <div className="mt-12 card bg-gradient-to-r from-primary-600 to-primary-800 text-white text-center">
              <h3 className="text-2xl font-bold mb-2">
                ¿Quieres otra experiencia?
              </h3>
              <p className="mb-6 opacity-90">
                Genera un nuevo itinerario con diferentes intereses o tiempo
              </p>
              <Link
                to="/generar"
                className="bg-white text-primary-600 px-8 py-4 rounded-lg font-bold hover:bg-gray-100 transition-colors inline-block"
              >
                🤖 Generar Nuevo Itinerario
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default MisItinerariosPage;