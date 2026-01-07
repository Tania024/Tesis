import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { itinerariosAPI, areasAPI } from '../services/api';
import LoadingSpinner from '../components/Layout/LoadingSpinner';

const GenerarItinerarioPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [loading, setLoading] = useState(false);
  const [generando, setGenerando] = useState(false);
  const [areas, setAreas] = useState([]);
  const [error, setError] = useState(null);

  const [formData, setFormData] = useState({
    intereses: [],
    tiempo_disponible: 90,
    nivel_detalle: 'normal',
    incluir_descansos: false,
    areas_evitar: [],
  });

  // Categorías disponibles
  const categoriasDisponibles = [
    { id: 'arqueologia', nombre: 'Arqueología', icon: '🏛️' },
    { id: 'historia', nombre: 'Historia', icon: '📜' },
    { id: 'arte', nombre: 'Arte', icon: '🎨' },
    { id: 'naturaleza', nombre: 'Naturaleza', icon: '🌿' },
    { id: 'biodiversidad', nombre: 'Biodiversidad', icon: '🦜' },
    { id: 'cultura_andina', nombre: 'Cultura Andina', icon: '⛰️' },
    { id: 'etnografia', nombre: 'Etnografía', icon: '👥' },
    { id: 'artesania', nombre: 'Artesanía', icon: '🎭' },
  ];

  useEffect(() => {
    cargarAreas();
  }, []);

  const cargarAreas = async () => {
    try {
      const data = await areasAPI.listarAreas();
      setAreas(data);
    } catch (err) {
      console.error('Error cargando áreas:', err);
    }
  };

  const handleInteresToggle = (interes) => {
    setFormData(prev => ({
      ...prev,
      intereses: prev.intereses.includes(interes)
        ? prev.intereses.filter(i => i !== interes)
        : [...prev.intereses, interes]
    }));
  };

  const handleAreaToggle = (areaId) => {
    setFormData(prev => ({
      ...prev,
      areas_evitar: prev.areas_evitar.includes(areaId)
        ? prev.areas_evitar.filter(id => id !== areaId)
        : [...prev.areas_evitar, areaId]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.intereses.length === 0) {
      setError('Por favor selecciona al menos un interés');
      return;
    }

    try {
      setGenerando(true);
      setError(null);

      const payload = {
        visitante_id: user.visitante_id,
        intereses: formData.intereses,
        tiempo_disponible: formData.tiempo_disponible,
        nivel_detalle: formData.nivel_detalle,
        incluir_descansos: formData.incluir_descansos,
        areas_evitar: formData.areas_evitar,
      };

      console.log('🚀 Generando itinerario con:', payload);

      const itinerario = await itinerariosAPI.generarItinerario(payload);

      console.log('✅ Itinerario generado:', itinerario);

      // Redirigir al itinerario generado
      navigate(`/itinerario/${itinerario.id}`);

    } catch (err) {
      console.error('Error generando itinerario:', err);
      setError(err.response?.data?.detail || 'Error al generar el itinerario. Inténtalo de nuevo.');
    } finally {
      setGenerando(false);
    }
  };

  if (generando) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white flex items-center justify-center">
        <div className="text-center max-w-md">
          <LoadingSpinner message="Generando tu itinerario personalizado..." />
          <div className="mt-8 space-y-4">
            <p className="text-gray-700 font-medium">🤖 IA analizando tus preferencias...</p>
            <p className="text-gray-600">🎯 Seleccionando áreas relevantes...</p>
            <p className="text-gray-600">📝 Creando descripciones narrativas...</p>
            <p className="text-sm text-gray-500 mt-4">
              Esto puede tomar 10-15 segundos
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🤖 Generar Itinerario con IA
          </h1>
          <p className="text-xl text-gray-600">
            Personaliza tu visita según tus intereses y tiempo disponible
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Sección 1: Intereses */}
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              1. Selecciona tus intereses
            </h2>
            <p className="text-gray-600 mb-6">
              Elige las temáticas que más te interesan (mínimo 1)
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
              {categoriasDisponibles.map(cat => (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => handleInteresToggle(cat.id)}
                  className={`p-4 rounded-lg border-2 transition-all text-center ${
                    formData.intereses.includes(cat.id)
                      ? 'border-primary-600 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="text-3xl mb-2">{cat.icon}</div>
                  <div className="text-sm font-medium">{cat.nombre}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Sección 2: Tiempo */}
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              2. ¿Cuánto tiempo tienes?
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-gray-700 font-medium mb-2">
                  Tiempo disponible: {formData.tiempo_disponible} minutos
                </label>
                <input
                  type="range"
                  min="30"
                  max="240"
                  step="15"
                  value={formData.tiempo_disponible}
                  onChange={(e) => setFormData({ ...formData, tiempo_disponible: parseInt(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-sm text-gray-500 mt-2">
                  <span>30 min</span>
                  <span>1 hora</span>
                  <span>2 horas</span>
                  <span>3 horas</span>
                  <span>4 horas</span>
                </div>
              </div>

              {/* Presets rápidos */}
              <div className="flex flex-wrap gap-2">
                {[60, 90, 120, 180].map(mins => (
                  <button
                    key={mins}
                    type="button"
                    onClick={() => setFormData({ ...formData, tiempo_disponible: mins })}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      formData.tiempo_disponible === mins
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {mins} min
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Sección 3: Nivel de Detalle */}
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              3. Nivel de detalle
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                type="button"
                onClick={() => setFormData({ ...formData, nivel_detalle: 'rapido' })}
                className={`p-6 rounded-lg border-2 transition-all text-left ${
                  formData.nivel_detalle === 'rapido'
                    ? 'border-primary-600 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-2xl mb-2">⚡</div>
                <div className="font-bold mb-1">Rápido</div>
                <div className="text-sm text-gray-600">
                  Descripciones breves, ideal para visitas cortas
                </div>
              </button>

              <button
                type="button"
                onClick={() => setFormData({ ...formData, nivel_detalle: 'normal' })}
                className={`p-6 rounded-lg border-2 transition-all text-left ${
                  formData.nivel_detalle === 'normal'
                    ? 'border-primary-600 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-2xl mb-2">📖</div>
                <div className="font-bold mb-1">Normal</div>
                <div className="text-sm text-gray-600">
                  Balance entre información y tiempo
                </div>
              </button>

              <button
                type="button"
                onClick={() => setFormData({ ...formData, nivel_detalle: 'profundo' })}
                className={`p-6 rounded-lg border-2 transition-all text-left ${
                  formData.nivel_detalle === 'profundo'
                    ? 'border-primary-600 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-2xl mb-2">🔍</div>
                <div className="font-bold mb-1">Profundo</div>
                <div className="text-sm text-gray-600">
                  Información detallada y académica
                </div>
              </button>
            </div>
          </div>

          {/* Sección 4: Opciones Adicionales */}
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              4. Opciones adicionales
            </h2>
            <div className="space-y-4">
              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.incluir_descansos}
                  onChange={(e) => setFormData({ ...formData, incluir_descansos: e.target.checked })}
                  className="w-5 h-5 text-primary-600 rounded focus:ring-primary-500"
                />
                <span className="text-gray-700">
                  Incluir tiempo para descansos
                </span>
              </label>

              {areas.length > 0 && (
                <div>
                  <p className="text-gray-700 font-medium mb-3">
                    Áreas a evitar (opcional):
                  </p>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {areas.map(area => (
                      <label key={area.id} className="flex items-center space-x-2 cursor-pointer text-sm">
                        <input
                          type="checkbox"
                          checked={formData.areas_evitar.includes(area.id)}
                          onChange={() => handleAreaToggle(area.id)}
                          className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                        />
                        <span className="text-gray-600">{area.nombre}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Botón Submit */}
          <div className="card bg-gradient-to-r from-primary-600 to-primary-800 text-white">
            <div className="text-center">
              <h3 className="text-2xl font-bold mb-2">
                ¿Listo para tu itinerario personalizado?
              </h3>
              <p className="mb-6 opacity-90">
                La IA generará una guía única basada en tus preferencias
              </p>
              <button
                type="submit"
                disabled={loading || formData.intereses.length === 0}
                className="bg-white text-primary-600 px-12 py-4 rounded-lg font-bold text-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Generando...' : '🤖 Generar Mi Itinerario'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default GenerarItinerarioPage;