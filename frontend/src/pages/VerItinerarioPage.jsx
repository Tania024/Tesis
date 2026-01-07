import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { itinerariosAPI, detallesAPI } from '../services/api';
import LoadingSpinner from '../components/Layout/LoadingSpinner';

const VerItinerarioPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [itinerario, setItinerario] = useState(null);
  const [detalles, setDetalles] = useState([]);

  useEffect(() => {
    cargarDatos();
  }, [id]);

  const cargarDatos = async () => {
    try {
      setLoading(true);
      setError(null);

      // Cargar itinerario y detalles en paralelo
      const [itinerarioData, detallesData] = await Promise.all([
        itinerariosAPI.obtenerItinerario(id),
        detallesAPI.obtenerDetalles(id)
      ]);

      setItinerario(itinerarioData);
      setDetalles(detallesData.sort((a, b) => a.orden - b.orden));
    } catch (err) {
      console.error('Error al cargar itinerario:', err);
      setError('No se pudo cargar el itinerario. Por favor, intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  const handleIniciarVisita = async () => {
    try {
      setLoading(true);
      await itinerariosAPI.iniciarItinerario(id);
      navigate(`/visita/${id}`);
    } catch (err) {
      console.error('Error al iniciar visita:', err);
      alert('No se pudo iniciar la visita. Por favor, intenta de nuevo.');
      setLoading(false);
    }
  };

  const calcularDuracionTotal = () => {
    if (!detalles || detalles.length === 0) return 0;
    return detalles.reduce((total, detalle) => total + (detalle.tiempo_sugerido || 0), 0);
  };

  const formatearFecha = (fecha) => {
    return new Date(fecha).toLocaleDateString('es-EC', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) return <LoadingSpinner />;

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <div className="text-4xl mb-4">❌</div>
          <h2 className="text-xl font-semibold text-red-800 mb-2">Error</h2>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={() => navigate('/mis-itinerarios')}
            className="btn-secondary"
          >
            Volver a Mis Itinerarios
          </button>
        </div>
      </div>
    );
  }

  if (!itinerario) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <p className="text-gray-600">No se encontró el itinerario.</p>
      </div>
    );
  }

  const duracionTotal = calcularDuracionTotal();

  return (
    <div className="min-h-screen bg-gradient-to-br from-museo-cream to-white py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Header del Itinerario */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-3xl">🤖</span>
                <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                  Generado con IA
                </span>
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {itinerario.titulo}
              </h1>
              {itinerario.descripcion && (
                <p className="text-gray-600 text-lg">
                  {itinerario.descripcion}
                </p>
              )}
            </div>
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-200">
            <div className="flex items-center gap-3">
              <span className="text-2xl">⏱️</span>
              <div>
                <p className="text-sm text-gray-500">Duración Total</p>
                <p className="text-lg font-semibold text-gray-900">
                  {duracionTotal} minutos
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-2xl">📍</span>
              <div>
                <p className="text-sm text-gray-500">Áreas a Visitar</p>
                <p className="text-lg font-semibold text-gray-900">
                  {detalles.length} áreas
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-2xl">📅</span>
              <div>
                <p className="text-sm text-gray-500">Generado</p>
                <p className="text-lg font-semibold text-gray-900">
                  {formatearFecha(itinerario.fecha_creacion)}
                </p>
              </div>
            </div>
          </div>

          {/* Información del Modelo de IA */}
          {itinerario.modelo_usado && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">
                <span className="font-medium">Modelo de IA:</span> {itinerario.modelo_usado}
              </p>
            </div>
          )}

          {/* Botón Principal */}
          <div className="mt-6">
            <button
              onClick={handleIniciarVisita}
              className="w-full btn-primary text-lg py-4 flex items-center justify-center gap-2 hover:scale-[1.02] transition-transform"
            >
              <span className="text-2xl">🚀</span>
              Iniciar Visita Ahora
            </button>
          </div>
        </div>

        {/* Lista de Áreas del Itinerario */}
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span>🗺️</span>
            Tu Recorrido Personalizado
          </h2>

          {detalles.map((detalle, index) => (
            <div
              key={detalle.id}
              className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6"
            >
              {/* Header del Área */}
              <div className="flex items-start gap-4 mb-4">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-700 rounded-full flex items-center justify-center text-white text-xl font-bold shadow-md">
                    {detalle.orden}
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-1">
                    {detalle.area.nombre}
                  </h3>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span className="flex items-center gap-1">
                      ⏱️ {detalle.tiempo_sugerido} minutos
                    </span>
                    {detalle.area.ubicacion && (
                      <span className="flex items-center gap-1">
                        📍 {detalle.area.ubicacion}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Descripción del Área */}
              {detalle.area.descripcion && (
                <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                  <p className="text-gray-700 text-sm leading-relaxed">
                    {detalle.area.descripcion}
                  </p>
                </div>
              )}

              {/* Introducción Generada por IA */}
              {detalle.introduccion_ia && (
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm">🤖</span>
                    <h4 className="font-semibold text-gray-900 text-sm">
                      Introducción Personalizada
                    </h4>
                  </div>
                  <p className="text-gray-700 leading-relaxed">
                    {detalle.introduccion_ia}
                  </p>
                </div>
              )}

              {/* Puntos Clave */}
              {detalle.puntos_clave_ia && detalle.puntos_clave_ia.length > 0 && (
                <div className="mb-4">
                  <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                    <span>✨</span>
                    Puntos Destacados
                  </h4>
                  <ul className="space-y-2">
                    {detalle.puntos_clave_ia.map((punto, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-gray-700">
                        <span className="text-primary-500 mt-1">•</span>
                        <span>{punto}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recomendación */}
              {detalle.recomendacion_ia && (
                <div className="mt-4 p-4 bg-museo-gold bg-opacity-10 border border-museo-gold border-opacity-30 rounded-lg">
                  <div className="flex items-start gap-2">
                    <span className="text-xl">💡</span>
                    <div>
                      <h4 className="font-semibold text-museo-brown mb-1">
                        Recomendación
                      </h4>
                      <p className="text-gray-700 text-sm">
                        {detalle.recomendacion_ia}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Footer con Botón Adicional */}
        <div className="mt-8 bg-white rounded-xl shadow-md p-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="font-semibold text-gray-900 mb-1">
                ¿Listo para comenzar tu visita?
              </h3>
              <p className="text-sm text-gray-600">
                Este recorrido fue diseñado especialmente para ti
              </p>
            </div>
            <button
              onClick={handleIniciarVisita}
              className="btn-primary whitespace-nowrap"
            >
              Iniciar Visita 🚀
            </button>
          </div>
        </div>

        {/* Botón Volver */}
        <div className="mt-6 text-center">
          <button
            onClick={() => navigate('/mis-itinerarios')}
            className="text-gray-600 hover:text-gray-900 transition-colors"
          >
            ← Volver a Mis Itinerarios
          </button>
        </div>
      </div>
    </div>
  );
};

export default VerItinerarioPage;