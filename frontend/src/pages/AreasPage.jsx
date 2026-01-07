import { useState, useEffect } from 'react';
import { areasAPI } from '../services/api';
import LoadingSpinner from '../components/Layout/LoadingSpinner';

const AreasPage = () => {
  const [areas, setAreas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filtroCategoria, setFiltroCategoria] = useState('todas');

  useEffect(() => {
    cargarAreas();
  }, []);

  const cargarAreas = async () => {
    try {
      setLoading(true);
      const data = await areasAPI.listarAreas();
      setAreas(data);
    } catch (err) {
      console.error('Error cargando áreas:', err);
      setError('Error al cargar las áreas del museo');
    } finally {
      setLoading(false);
    }
  };

  const categorias = ['todas', ...new Set(areas.map(a => a.categoria))];
  
  const areasFiltradas = filtroCategoria === 'todas' 
    ? areas 
    : areas.filter(a => a.categoria === filtroCategoria);

  if (loading) return <LoadingSpinner message="Cargando áreas del museo..." />;

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-700">{error}</p>
          <button onClick={cargarAreas} className="btn-primary mt-4">
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Áreas del Museo Pumapungo
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Explora las {areas.length} áreas temáticas que componen nuestro museo
          </p>
        </div>

        {/* Filtros */}
        <div className="mb-8 flex flex-wrap gap-2 justify-center">
          {categorias.map(cat => (
            <button
              key={cat}
              onClick={() => setFiltroCategoria(cat)}
              className={`px-6 py-2 rounded-full font-medium transition-colors ${
                filtroCategoria === cat
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {cat === 'todas' ? 'Todas' : cat}
            </button>
          ))}
        </div>

        {/* Grid de Áreas */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {areasFiltradas.map(area => (
            <div key={area.id} className="card hover:scale-105 transition-transform">
              {/* Badge de categoría */}
              <div className="flex justify-between items-start mb-4">
                <span className="bg-primary-100 text-primary-700 px-3 py-1 rounded-full text-sm font-medium">
                  {area.categoria}
                </span>
                <span className="text-2xl">{area.orden_recomendado}</span>
              </div>

              {/* Código */}
              <div className="text-xs text-gray-500 font-mono mb-2">
                {area.codigo}
              </div>

              {/* Nombre */}
              <h3 className="text-xl font-bold text-gray-900 mb-3">
                {area.nombre}
              </h3>

              {/* Descripción */}
              <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                {area.descripcion || 'Área del museo con exhibiciones únicas.'}
              </p>

              {/* Info adicional */}
              <div className="space-y-2 text-sm">
                {area.subcategoria && (
                  <div className="flex items-center text-gray-600">
                    <span className="mr-2">🏷️</span>
                    <span>{area.subcategoria}</span>
                  </div>
                )}
                
                <div className="flex items-center text-gray-600">
                  <span className="mr-2">⏱️</span>
                  <span>{area.tiempo_minimo}-{area.tiempo_maximo} minutos</span>
                </div>

                {area.piso && (
                  <div className="flex items-center text-gray-600">
                    <span className="mr-2">🏢</span>
                    <span>Piso {area.piso}</span>
                  </div>
                )}

                {area.zona && (
                  <div className="flex items-center text-gray-600">
                    <span className="mr-2">📍</span>
                    <span>{area.zona}</span>
                  </div>
                )}
              </div>

              {/* Estado */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                  area.activa 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-red-100 text-red-700'
                }`}>
                  {area.activa ? '✓ Disponible' : '✗ No disponible'}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Mensaje si no hay resultados */}
        {areasFiltradas.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-600 text-lg">
              No se encontraron áreas en esta categoría
            </p>
          </div>
        )}

        {/* CTA */}
        <div className="mt-16 bg-gradient-to-r from-primary-600 to-primary-800 rounded-2xl p-12 text-center text-white">
          <h2 className="text-3xl font-bold mb-4">
            ¿Listo para tu visita personalizada?
          </h2>
          <p className="text-xl mb-8 opacity-90">
            Genera un itinerario adaptado a tus intereses con IA
          </p>
          <button
            onClick={() => window.location.href = '/login'}
            className="bg-white text-primary-600 px-8 py-4 rounded-lg font-bold text-lg hover:bg-gray-100 transition-colors"
          >
            Generar Mi Itinerario
          </button>
        </div>
      </div>
    </div>
  );
};

export default AreasPage;