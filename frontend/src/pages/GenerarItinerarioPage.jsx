import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { itinerariosAPI, perfilesAPI } from '../services/api';
import LoadingSpinner from '../components/Layout/LoadingSpinner';

const GenerarItinerarioPage = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  
  const [loading, setLoading] = useState(false);
  const [loadingPerfil, setLoadingPerfil] = useState(true);
  const [error, setError] = useState(null);
  const [perfil, setPerfil] = useState(null);
  
  // Estados del formulario
  const [tiempoDisponible, setTiempoDisponible] = useState(null);
  const [tiempoPersonalizado, setTiempoPersonalizado] = useState('');
  const [sinPrisa, setSinPrisa] = useState(false);
  const [nivelDetalle, setNivelDetalle] = useState('medio');

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    cargarPerfil();
  }, [user, isAuthenticated]);

  const cargarPerfil = async () => {
    try {
      setLoadingPerfil(true);
      console.log('📊 Cargando perfil del visitante:', user.visitante_id);
      
      const data = await perfilesAPI.obtener(user.visitante_id);
      
      
      console.log('✅ Perfil cargado:', data);
      
      if (data) {
        setPerfil(data);
      } else {
        setPerfil({
          intereses: ['cultura'],
          tiempo_disponible: null,
          nivel_detalle: 'medio'
        });
      }
    } catch (err) {
      console.error('❌ Error cargando perfil:', err);
      
      if (err.response?.status === 404) {
        console.log('ℹ️ Perfil no encontrado, usando perfil por defecto');
        setPerfil({
          intereses: ['cultura'],
          tiempo_disponible: null,
          nivel_detalle: 'medio'
        });
      } else {
        setPerfil({
          intereses: [],
          tiempo_disponible: null,
          nivel_detalle: 'medio'
        });
      }
    } finally {
      setLoadingPerfil(false);
    }
  };

  const handleGenerarItinerario = async () => {
    try {
      setLoading(true);
      setError(null);

      // Determinar tiempo final
      let tiempoFinal = null;
      
      if (sinPrisa) {
        tiempoFinal = null; // Sin límite de tiempo
      } else if (tiempoDisponible === 'personalizado' && tiempoPersonalizado) {
        tiempoFinal = parseInt(tiempoPersonalizado);
      } else if (tiempoDisponible) {
        tiempoFinal = parseInt(tiempoDisponible);
      }

      console.log('🤖 Generando itinerario...');
      console.log('Tiempo disponible:', tiempoFinal === null ? 'Sin límite' : `${tiempoFinal} minutos`);
      console.log('Nivel de detalle:', nivelDetalle);
      console.log('Intereses:', perfil?.intereses || []);

      const MAPA_INTERESES = {
        cultura: ['arqueologia', 'etnografia', 'historia', 'arte'],
        naturaleza: ['aves', 'plantas', 'biodiversidad'],
        historia: ['arqueologia', 'historia'],
      };

      // Asegurar que intereses sea un array de strings
      const interesesArray = [];

      if (Array.isArray(perfil?.intereses)) {
        perfil.intereses.forEach(interes => {
          if (MAPA_INTERESES[interes]) {
            interesesArray.push(...MAPA_INTERESES[interes]);
          } else {
            interesesArray.push(interes);
          }
        });
      }

      // fallback seguro
      if (interesesArray.length === 0) {
        interesesArray.push('arqueologia');
      }

      const MAPA_NIVEL_DETALLE = {
        basico: 'rapido',
        medio: 'normal',
        detallado: 'profundo'
      };
  
      // ✅ PAYLOAD CORREGIDO
      const payload = {
        visitante_id: user.visitante_id,
        intereses: interesesArray.length > 0 ? interesesArray : ['cultura'],
        tiempo_disponible: tiempoFinal,
        nivel_detalle: MAPA_NIVEL_DETALLE[nivelDetalle],
        incluir_descansos: tiempoFinal ? tiempoFinal > 90 : true,
        areas_evitar: []
      };

      console.log('📤 Payload enviado:', JSON.stringify(payload, null, 2));

      // 🔥🔥🔥 CAMBIO CRÍTICO: Usar endpoint PROGRESIVO 🔥🔥🔥
      const response = await itinerariosAPI.generarProgresivo(user.visitante_id, payload);
      
      console.log('✅ Respuesta del backend:', response);

      // Redirigir al itinerario generado
      const itinerarioId = response.id;
      
      if (itinerarioId) {
        console.log('↪️ Redirigiendo a itinerario:', itinerarioId);
        navigate(`/itinerario/${itinerarioId}`);
      } else {
        throw new Error('El backend no retornó un ID de itinerario');
      }

    } catch (err) {
      console.error('❌ Error generando itinerario:', err);
      console.error('Response data:', err.response?.data);
      
      // ✅ MANEJO CORRECTO DE ERRORES
      let errorMessage = 'Error al generar el itinerario. Intenta de nuevo.';
      
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        
        // Si detail es un array (errores de validación de Pydantic)
        if (Array.isArray(detail)) {
          errorMessage = detail.map(e => {
            const field = e.loc?.join('.') || 'unknown';
            const msg = e.msg || 'Error de validación';
            return `${field}: ${msg}`;
          }).join(', ');
        } 
        // Si detail es un string
        else if (typeof detail === 'string') {
          errorMessage = detail;
        }
        // Si detail es un objeto
        else if (typeof detail === 'object') {
          errorMessage = JSON.stringify(detail);
        }
      }
      
      setError(errorMessage);
      setLoading(false);
    }
  };

  if (loadingPerfil) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner message="Cargando tu perfil..." />
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <LoadingSpinner message="Generando tu itinerario personalizado..." />
          <div className="mt-6 space-y-3 text-gray-600">
            <p className="flex items-center justify-center gap-2">
              <span>🤖</span>
              <span>Analizando tus intereses...</span>
            </p>
            <p className="flex items-center justify-center gap-2">
              <span>📍</span>
              <span>Seleccionando las mejores áreas...</span>
            </p>
            <p className="flex items-center justify-center gap-2">
              <span>✨</span>
              <span>Creando tu primera área...</span>
            </p>
            <p className="text-sm text-primary-600 font-semibold mt-4">
              ⚡ Esto tomará solo 2 minutos...
            </p>
            <p className="text-xs text-gray-500">
              El resto se generará mientras exploras 🔄
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-3xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <span className="text-5xl">🤖</span>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-3">
            Generar Itinerario Personalizado
          </h1>
          <p className="text-gray-600 text-lg">
            Responde algunas preguntas y la IA creará el itinerario perfecto para ti
          </p>
        </div>

        {/* Card principal */}
        <div className="card">
          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <span className="text-xl text-red-600 flex-shrink-0">⚠️</span>
                <div className="flex-1">
                  <p className="font-semibold text-red-900 mb-1">Error al generar itinerario</p>
                  <p className="text-sm text-red-700 whitespace-pre-wrap">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Intereses detectados */}
          <div className="mb-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
              <span>📺</span>
              <span>Tus intereses detectados de YouTube:</span>
            </h3>
            <div className="flex flex-wrap gap-2">
              {perfil && perfil.intereses && perfil.intereses.length > 0 ? (
                perfil.intereses.map((interes, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium"
                  >
                    {interes}
                  </span>
                ))
              ) : (
                <span className="text-blue-600 text-sm">
                  No se detectaron intereses específicos. Se usará un itinerario general.
                </span>
              )}
            </div>
          </div>

          {/* Pregunta 1: Tiempo disponible */}
          <div className="mb-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span>⏱️</span>
              <span>¿Cuánto tiempo tienes disponible?</span>
            </h3>
            
            {/* Checkbox: Sin prisa */}
            <div className="mb-4 p-4 bg-green-50 border-2 border-green-200 rounded-lg">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={sinPrisa}
                  onChange={(e) => {
                    setSinPrisa(e.target.checked);
                    if (e.target.checked) {
                      setTiempoDisponible(null);
                    }
                  }}
                  className="mt-1 w-5 h-5 text-green-600 rounded focus:ring-green-500"
                />
                <div>
                  <p className="font-semibold text-green-900">
                    ✨ No tengo prisa, quiero ver todo el museo
                  </p>
                  <p className="text-sm text-green-700 mt-1">
                    Te generaremos un itinerario completo con todas las áreas personalizadas según tus intereses
                  </p>
                </div>
              </label>
            </div>

            {/* Opciones de tiempo */}
            {!sinPrisa && (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {[
                  { value: '30', label: '30 minutos', icon: '⚡' },
                  { value: '60', label: '1 hora', icon: '⏰' },
                  { value: '90', label: '1.5 horas', icon: '🕐' },
                  { value: '120', label: '2 horas', icon: '🕑' },
                  { value: '180', label: '3 horas', icon: '🕒' },
                  { value: 'personalizado', label: 'Personalizado', icon: '✏️' }
                ].map((opcion) => (
                  <button
                    key={opcion.value}
                    onClick={() => setTiempoDisponible(opcion.value)}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      tiempoDisponible === opcion.value
                        ? 'border-primary-500 bg-primary-50 text-primary-700'
                        : 'border-gray-200 bg-white hover:border-gray-300'
                    }`}
                  >
                    <div className="text-2xl mb-1">{opcion.icon}</div>
                    <div className="text-sm font-semibold">{opcion.label}</div>
                  </button>
                ))}
              </div>
            )}

            {/* Input personalizado */}
            {tiempoDisponible === 'personalizado' && !sinPrisa && (
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Ingresa los minutos disponibles:
                </label>
                <input
                  type="number"
                  min="15"
                  max="480"
                  value={tiempoPersonalizado}
                  onChange={(e) => setTiempoPersonalizado(e.target.value)}
                  placeholder="Ej: 45"
                  className="input-field"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Entre 15 y 480 minutos (8 horas)
                </p>
              </div>
            )}
          </div>

          {/* Pregunta 2: Nivel de detalle */}
          <div className="mb-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span>🔍</span>
              <span>¿Cuánto detalle quieres en cada área?</span>
            </h3>
            
            <div className="grid gap-3">
              {[
                { 
                  value: 'basico', 
                  label: 'Básico', 
                  icon: '⚡', 
                  desc: 'Vista rápida de lo esencial (3 datos curiosos)' 
                },
                { 
                  value: 'medio', 
                  label: 'Medio', 
                  icon: '👌', 
                  desc: 'Balance entre rapidez y detalle (4-5 datos)' 
                },
                { 
                  value: 'detallado', 
                  label: 'Detallado', 
                  icon: '🔬', 
                  desc: 'Explicaciones profundas y completas (7 datos + 8 observaciones)' 
                }
              ].map((opcion) => (
                <button
                  key={opcion.value}
                  onClick={() => setNivelDetalle(opcion.value)}
                  className={`p-4 rounded-lg border-2 transition-all text-left ${
                    nivelDetalle === opcion.value
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{opcion.icon}</span>
                    <div>
                      <div className="font-semibold text-gray-900">{opcion.label}</div>
                      <div className="text-sm text-gray-600">{opcion.desc}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Resumen */}
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg mb-6">
            <h4 className="font-semibold text-gray-900 mb-2">📝 Resumen de tu itinerario:</h4>
            <ul className="space-y-1 text-sm text-gray-700">
              <li>
                <span className="font-medium">Tiempo:</span>{' '}
                {sinPrisa 
                  ? 'Sin límite (itinerario completo)' 
                  : tiempoDisponible === 'personalizado' 
                    ? `${tiempoPersonalizado || '...'} minutos` 
                    : tiempoDisponible 
                      ? `${tiempoDisponible} minutos` 
                      : 'No especificado'}
              </li>
              <li>
                <span className="font-medium">Detalle:</span> {nivelDetalle.charAt(0).toUpperCase() + nivelDetalle.slice(1)}
              </li>
              <li>
                <span className="font-medium">Intereses:</span> {perfil?.intereses?.join(', ') || 'General'}
              </li>
            </ul>
          </div>

          {/* Botón generar */}
          <button
            onClick={handleGenerarItinerario}
            disabled={!sinPrisa && !tiempoDisponible}
            className="w-full btn-primary py-4 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="flex items-center justify-center gap-3">
              <span>⚡</span>
              <span>Generar Mi Itinerario (2 minutos)</span>
            </span>
          </button>

          {!sinPrisa && !tiempoDisponible && (
            <p className="text-center text-sm text-gray-500 mt-3">
              Por favor, selecciona cuánto tiempo tienes disponible
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default GenerarItinerarioPage;