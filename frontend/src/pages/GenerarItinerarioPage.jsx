// frontend/src/pages/GenerarItinerarioPage.jsx
// ✅ COMPLETO Y CORREGIDO - Con ErrorModal y WarningModal

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { itinerariosAPI, perfilesAPI } from '../services/api';
import LoadingSpinner from '../components/Layout/LoadingSpinner';
import ErrorModal from '../components/UI/ErrorModal';
import WarningModal from '../components/UI/WarningModal';

const GenerarItinerarioPage = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  
  const [loading, setLoading] = useState(false);
  const [loadingPerfil, setLoadingPerfil] = useState(true);
  const [error, setError] = useState(null);
  const [warning, setWarning] = useState(null);
  const [showWarning, setShowWarning] = useState(false);
  const [perfil, setPerfil] = useState(null);
  
  // Estados del formulario
  const [tiempoDisponible, setTiempoDisponible] = useState(null);
  const [tiempoPersonalizado, setTiempoPersonalizado] = useState('');
  const [sinPrisa, setSinPrisa] = useState(false);
  const [nivelDetalle, setNivelDetalle] = useState('medio');
  const [tipoEntrada, setTipoEntrada] = useState('individual');
  const [acompanantes, setAcompanantes] = useState(0);
  const [seleccionManual, setSeleccionManual] = useState(false);
  const [areasSeleccionadas, setAreasSeleccionadas] = useState([]);

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
      const data = await perfilesAPI.obtener(user.visitante_id);
      
      if (data) {
        setPerfil(data);
        if (data.intereses && data.intereses.length > 0) {
          const areasIniciales = mapearInteresesAAreas(data.intereses);
          setAreasSeleccionadas(areasIniciales);
        }
      } else {
        setPerfil({ intereses: ['cultura'], tiempo_disponible: null, nivel_detalle: 'medio' });
        setAreasSeleccionadas(['ARQ-01', 'ETN-01', 'ART-01']);
      }
    } catch (err) {
      if (err.response?.status === 404) {
        setPerfil({ intereses: ['cultura'], tiempo_disponible: null, nivel_detalle: 'medio' });
        setAreasSeleccionadas(['ARQ-01', 'ETN-01', 'ART-01']);
      } else {
        setPerfil({ intereses: [], tiempo_disponible: null, nivel_detalle: 'medio' });
        setAreasSeleccionadas(['ARQ-01', 'ETN-01', 'ART-01']);
      }
    } finally {
      setLoadingPerfil(false);
    }
  };

  const mapearInteresesAAreas = (intereses) => {
    const mapaInteresesAreas = {
      arqueologia: ['ARQ-01', 'RUIN-01'],
      etnografia: ['ETN-01'],
      aves: ['AVE-01'],
      plantas: ['BOT-01'],
      arte: ['ART-01'],
      historia: ['ARQ-01', 'RUIN-01'],
      cultura: ['ARQ-01', 'ETN-01', 'ART-01'],
      naturaleza: ['BOT-01', 'AVE-01'],      
      biodiversidad: ['BOT-01', 'AVE-01'],   
      botanica: ['BOT-01'],                  
      ornitologia: ['AVE-01'],               
      temporal: ['TEMP-01']
    };
    
    const areas = new Set();
    intereses.forEach(interes => {
      if (mapaInteresesAreas[interes]) {
        mapaInteresesAreas[interes].forEach(area => areas.add(area));
      }
    });
    return Array.from(areas);
  };

  const mapearAreasAIntereses = (areas) => {
    const mapaAreasIntereses = {
      'ARQ-01': ['arqueologia', 'historia'],
      'ETN-01': ['etnografia', 'cultura'],
      'AVE-01': ['aves', 'naturaleza', 'biodiversidad'],           
      'BOT-01': ['plantas', 'naturaleza', 'biodiversidad'],        
      'ART-01': ['arte', 'cultura'],
      'RUIN-01': ['arqueologia', 'historia'],
      'TEMP-01': ['arte', 'cultura']
    };
    
    const intereses = new Set();
    areas.forEach(area => {
      if (mapaAreasIntereses[area]) {
        mapaAreasIntereses[area].forEach(interes => intereses.add(interes));
      }
    });
    return Array.from(intereses);
  };

  const toggleSeleccionManual = () => {
    setSeleccionManual(!seleccionManual);
    if (!seleccionManual) {
      if (perfil?.intereses && perfil.intereses.length > 0) {
        const areasIniciales = mapearInteresesAAreas(perfil.intereses);
        setAreasSeleccionadas(areasIniciales);
      }
    }
  };

  const toggleArea = (areaCode) => {
    setAreasSeleccionadas(prev => {
      if (prev.includes(areaCode)) {
        return prev.filter(a => a !== areaCode);
      } else {
        return [...prev, areaCode];
      }
    });
  };

  const AREAS_DISPONIBLES = [
    { code: 'ARQ-01', nombre: 'Sala Arqueológica Cañari', icon: '🏺', color: 'bg-orange-100 text-orange-700', desc: 'Descubre la historia prehispánica del pueblo Cañari' },
    { code: 'ETN-01', nombre: 'Sala Etnográfica', icon: '🎭', color: 'bg-purple-100 text-purple-700', desc: 'Conoce las tradiciones y cultura de los pueblos andinos' },
    { code: 'AVE-01', nombre: 'Aviario de Aves Andinas', icon: '🦅', color: 'bg-blue-100 text-blue-700', desc: 'Observa la diversidad de aves nativas de los Andes' },
    { code: 'BOT-01', nombre: 'Jardín Botánico', icon: '🌿', color: 'bg-green-100 text-green-700', desc: 'Explora la flora nativa del Ecuador' },
    { code: 'ART-01', nombre: 'Sala de Arte Colonial', icon: '🎨', color: 'bg-red-100 text-red-700', desc: 'Admira obras de arte del período colonial' },
    { code: 'RUIN-01', nombre: 'Parque Arqueológico Pumapungo', icon: '🏛️', color: 'bg-yellow-100 text-yellow-700', desc: 'Recorre el parque para observar el antiguo complejo inca' },
    { code: 'TEMP-01', nombre: 'Exhibición Temporal', icon: '🎪', color: 'bg-pink-100 text-pink-700', desc: 'Descubre exposiciones especiales y rotativas' }
  ];

  const handleGenerarItinerario = async () => {
    try {
      setLoading(true);
      setError(null);
      setWarning(null);
      setShowWarning(false);

      if (areasSeleccionadas.length === 0) {
        setWarning('Por favor, selecciona al menos una área para visitar');
        setShowWarning(true);
        setLoading(false);
        return;
      }

      if (tipoEntrada === 'grupo' && acompanantes < 1) {
        setWarning('⚠️ Los grupos deben tener al menos 1 acompañante');
        setShowWarning(true);
        setLoading(false);
        return;
      }

      if (tipoEntrada === 'individual' && acompanantes > 0) {
        setWarning('⚠️ La entrada individual no puede tener acompañantes');
        setShowWarning(true);
        setLoading(false);
        return;
      }

      let tiempoFinal = null;
      if (sinPrisa) {
        tiempoFinal = null;
      } else if (tiempoDisponible === 'personalizado' && tiempoPersonalizado) {
        tiempoFinal = parseInt(tiempoPersonalizado);
      } else if (tiempoDisponible) {
        tiempoFinal = parseInt(tiempoDisponible);
      }

      const interesesArray = mapearAreasAIntereses(areasSeleccionadas);
      const MAPA_NIVEL_DETALLE = { basico: 'rapido', medio: 'normal', detallado: 'profundo' };
  
      const payload = {
        visitante_id: user.visitante_id,
        intereses: interesesArray.length > 0 ? interesesArray : ['arqueologia'],
        tiempo_disponible: tiempoFinal,
        nivel_detalle: MAPA_NIVEL_DETALLE[nivelDetalle],
        tipo_entrada: tipoEntrada,
        acompanantes: acompanantes,
        incluir_descansos: tiempoFinal ? tiempoFinal > 90 : true,
        areas_evitar: []
      };

      const response = await itinerariosAPI.generarProgresivo(user.visitante_id, payload);
      
      if (response.id) {
        navigate(`/itinerario/${response.id}`);
      } else {
        throw new Error('El backend no retornó un ID de itinerario');
      }

    } catch (err) {
      console.error('❌ Error generando itinerario:', err);
      
      let errorMessage = 'Error al generar el itinerario. Intenta de nuevo.';
      let isWarning = false;
      
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        
        if (typeof detail === 'object') {
          const mensaje = detail.horarios || detail.mensaje || '';
          
          if (mensaje.includes('cerrado') || mensaje.includes('🚫') || mensaje.includes('No hay tiempo suficiente') || mensaje.includes('ya cerró')) {
            errorMessage = mensaje;
            isWarning = false;
          } else if (mensaje.includes('ajustado') || mensaje.includes('⏰') || mensaje.includes('limitado') || mensaje.includes('cerrará en')) {
            errorMessage = mensaje;
            isWarning = true;
          } else {
            errorMessage = mensaje;
            isWarning = false;
          }
        } 
        else if (typeof detail === 'string') {
          errorMessage = detail;
          if (detail.includes('ajustado') || detail.includes('⏰')) {
            isWarning = true;
          }
        }
      }
      
      if (isWarning) {
        setWarning(errorMessage);
        setShowWarning(true);
      } else {
        setError(errorMessage);
      }
      
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
            <p className="flex items-center justify-center gap-2"><span>🤖</span><span>Analizando tus intereses...</span></p>
            <p className="flex items-center justify-center gap-2"><span>📍</span><span>Seleccionando las mejores áreas...</span></p>
            <p className="flex items-center justify-center gap-2"><span>✨</span><span>Creando tu primera área...</span></p>
            <p className="text-sm text-primary-600 font-semibold mt-4">⚡ Esto tomará solo 2 minutos...</p>
            <p className="text-xs text-gray-500">El resto se generará mientras exploras 🔄</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <span className="text-5xl">🤖</span>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-3">Generar Itinerario Personalizado</h1>
          <p className="text-gray-600 text-lg">Responde algunas preguntas y la IA creará el itinerario perfecto para ti</p>
        </div>

        <div className="card">
          {error && <ErrorModal error={error} onClose={() => setError(null)} />}
          <WarningModal isOpen={showWarning} message={warning} onClose={() => { setShowWarning(false); setWarning(null); }} />

          <div className="mb-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
              <span>📺</span><span>Tus intereses detectados de YouTube:</span>
            </h3>
            <div className="flex flex-wrap gap-2">
              {perfil && perfil.intereses && perfil.intereses.length > 0 ? (
                perfil.intereses.map((interes, index) => (
                  <span key={index} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">{interes}</span>
                ))
              ) : (
                <span className="text-blue-600 text-sm">No se detectaron intereses específicos. Se usará un itinerario general.</span>
              )}
            </div>
          </div>

          <div className="mb-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span>🏛️</span><span>Selecciona las áreas que quieres visitar</span>
            </h3>
            
            <div className="mb-4 p-4 bg-purple-50 border-2 border-purple-200 rounded-lg">
              <label className="flex items-start gap-3 cursor-pointer">
                <input type="checkbox" checked={seleccionManual} onChange={toggleSeleccionManual} className="mt-1 w-5 h-5 text-purple-600 rounded focus:ring-purple-500" />
                <div>
                  <p className="font-semibold text-purple-900">✨ Quiero seleccionar las áreas manualmente</p>
                  <p className="text-sm text-purple-700 mt-1">{seleccionManual ? 'Estás seleccionando áreas manualmente' : 'Usaré tus intereses detectados para recomendarte áreas'}</p>
                </div>
              </label>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {AREAS_DISPONIBLES.map((area) => {
                const isSelected = areasSeleccionadas.includes(area.code);
                return (
                  <button key={area.code} onClick={() => toggleArea(area.code)} disabled={!seleccionManual}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${isSelected ? `${area.color} border-purple-500 ring-2 ring-purple-500` : 'bg-white border-gray-200 hover:border-gray-300'} ${!seleccionManual ? 'opacity-50 cursor-not-allowed' : ''}`}>
                    <div className="flex items-start gap-3">
                      <span className="text-3xl flex-shrink-0">{area.icon}</span>
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900">{area.nombre}</div>
                        <div className="text-sm text-gray-600 mt-1">{area.desc}</div>
                      </div>
                    </div>
                    {isSelected && (<div className="mt-2 flex items-center gap-1 text-green-600 text-sm font-medium"><span>✓</span><span>Seleccionado</span></div>)}
                  </button>
                );
              })}
            </div>

            {seleccionManual && areasSeleccionadas.length === 0 && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                <div className="flex items-start gap-2"><span className="text-xl">⚠️</span><span>Debes seleccionar al menos una área para continuar</span></div>
              </div>
            )}

            {areasSeleccionadas.length > 0 && (
              <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm font-medium text-green-800">📌 Áreas seleccionadas ({areasSeleccionadas.length}):</p>
                <div className="flex flex-wrap gap-2 mt-2">
                  {areasSeleccionadas.map((code) => {
                    const area = AREAS_DISPONIBLES.find(a => a.code === code);
                    return (<span key={code} className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">{area?.nombre || code}</span>);
                  })}
                </div>
              </div>
            )}
          </div>

          <div className="mb-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2"><span>🎫</span><span>Tipo de Entrada</span></h3>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { value: 'individual', label: 'Individual', icon: '👤' },
                { value: 'estudiante', label: 'Estudiante', icon: '🎓' },
                { value: 'adulto_mayor', label: 'Adulto Mayor', icon: '👴' },
                { value: 'grupo', label: 'Grupo', icon: '👥' }
              ].map((tipo) => (
                <button key={tipo.value} onClick={() => { setTipoEntrada(tipo.value); if (tipo.value === 'individual') { setAcompanantes(0); } else if (tipo.value === 'grupo' && acompanantes === 0) { setAcompanantes(1); }}}
                  className={`p-4 rounded-xl border-2 transition-all ${tipoEntrada === tipo.value ? 'border-primary-500 bg-primary-50' : 'border-gray-200 bg-white hover:border-gray-300'}`}>
                  <div className="text-2xl mb-2">{tipo.icon}</div>
                  <div className="font-medium text-sm">{tipo.label}</div>
                </button>
              ))}
            </div>
          </div>

          <div className={`mb-8 rounded-xl p-5 transition-all ${tipoEntrada === 'individual' ? 'bg-gray-100 border-2 border-gray-300' : 'bg-blue-50 border-2 border-blue-200'}`}>
            <label className="block text-sm font-medium mb-3 flex items-center gap-2">
              <span>👨‍👩‍👧‍👦</span><span>¿Viene con acompañantes?</span>
              {tipoEntrada === 'individual' && (<span className="ml-2 px-2 py-0.5 bg-gray-300 text-gray-700 text-xs font-semibold rounded-full">No disponible</span>)}
              {tipoEntrada === 'grupo' && (<span className="ml-2 px-2 py-0.5 bg-blue-200 text-blue-700 text-xs font-semibold rounded-full">Mínimo 1</span>)}
            </label>
            <div className="flex items-center justify-center gap-6">
              <button type="button" onClick={() => { const nuevoValor = Math.max(tipoEntrada === 'grupo' ? 1 : 0, acompanantes - 1); setAcompanantes(nuevoValor); }}
                disabled={tipoEntrada === 'individual' || (tipoEntrada === 'grupo' && acompanantes <= 1)}
                className={`w-12 h-12 rounded-full border-2 transition-colors flex items-center justify-center text-xl font-bold ${tipoEntrada === 'individual' || (tipoEntrada === 'grupo' && acompanantes <= 1) ? 'border-gray-300 bg-gray-200 text-gray-400 cursor-not-allowed' : 'border-gray-300 hover:border-primary-500 hover:bg-primary-50'}`}>
                -
              </button>
              <div className={`text-4xl font-bold w-20 text-center ${tipoEntrada === 'individual' ? 'text-gray-400' : 'text-gray-900'}`}>{acompanantes}</div>
              <button type="button" onClick={() => setAcompanantes(acompanantes + 1)} disabled={tipoEntrada === 'individual'}
                className={`w-12 h-12 rounded-full border-2 transition-colors flex items-center justify-center text-xl font-bold ${tipoEntrada === 'individual' ? 'border-gray-300 bg-gray-200 text-gray-400 cursor-not-allowed' : 'border-gray-300 hover:border-primary-500 hover:bg-primary-50'}`}>
                +
              </button>
            </div>
            <p className={`text-sm mt-3 text-center ${tipoEntrada === 'individual' ? 'text-gray-500' : 'text-gray-600'}`}>
              {tipoEntrada === 'individual' ? 'Entrada individual no incluye acompañantes' : tipoEntrada === 'grupo' ? 'Los grupos requieren al menos 1 acompañante' : 'Incluye familiares, amigos o compañeros de viaje'}
            </p>
          </div>

          <div className="mb-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2"><span>⏱️</span><span>¿Cuánto tiempo tienes disponible?</span></h3>
            
            <div className="mb-4 p-4 bg-green-50 border-2 border-green-200 rounded-lg">
              <label className="flex items-start gap-3 cursor-pointer">
                <input type="checkbox" checked={sinPrisa} onChange={(e) => { setSinPrisa(e.target.checked); if (e.target.checked) { setTiempoDisponible(null); }}} className="mt-1 w-5 h-5 text-green-600 rounded focus:ring-green-500" />
                <div>
                  <p className="font-semibold text-green-900">✨ No tengo prisa, quiero ver todo el museo</p>
                  <p className="text-sm text-green-700 mt-1">Te generaremos un itinerario completo con todas las áreas personalizadas según tus intereses</p>
                </div>
              </label>
            </div>

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
                  <button key={opcion.value} onClick={() => setTiempoDisponible(opcion.value)}
                    className={`p-4 rounded-lg border-2 transition-all ${tiempoDisponible === opcion.value ? 'border-primary-500 bg-primary-50 text-primary-700' : 'border-gray-200 bg-white hover:border-gray-300'}`}>
                    <div className="text-2xl mb-1">{opcion.icon}</div>
                    <div className="text-sm font-semibold">{opcion.label}</div>
                  </button>
                ))}
              </div>
            )}

            {tiempoDisponible === 'personalizado' && !sinPrisa && (
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Ingresa los minutos disponibles:</label>
                <input type="number" min="15" max="480" value={tiempoPersonalizado} onChange={(e) => setTiempoPersonalizado(e.target.value)} placeholder="Ej: 45" className="input-field" />
                <p className="text-sm text-gray-500 mt-1">Entre 15 y 480 minutos (8 horas)</p>
              </div>
            )}
          </div>

          <div className="mb-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2"><span>🔍</span><span>¿Cuánto detalle quieres en cada área?</span></h3>
            
            <div className="grid gap-3">
              {[
                { value: 'basico', label: 'Básico', icon: '⚡', desc: 'Vista rápida de lo esencial (3 datos curiosos)' },
                { value: 'medio', label: 'Medio', icon: '👌', desc: 'Balance entre rapidez y detalle (4-5 datos)' },
                { value: 'detallado', label: 'Detallado', icon: '🔬', desc: 'Explicaciones profundas y completas (7 datos + 8 observaciones)' }
              ].map((opcion) => (
                <button key={opcion.value} onClick={() => setNivelDetalle(opcion.value)}
                  className={`p-4 rounded-lg border-2 transition-all text-left ${nivelDetalle === opcion.value ? 'border-primary-500 bg-primary-50' : 'border-gray-200 bg-white hover:border-gray-300'}`}>
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

          <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg mb-6">
            <h4 className="font-semibold text-gray-900 mb-2">📝 Resumen de tu itinerario:</h4>
            <ul className="space-y-1 text-sm text-gray-700">
              <li><span className="font-medium">Áreas:</span> {areasSeleccionadas.length} seleccionadas</li>
              <li><span className="font-medium">Entrada:</span> {tipoEntrada.charAt(0).toUpperCase() + tipoEntrada.slice(1)}</li>
              <li><span className="font-medium">Acompañantes:</span> {acompanantes} {acompanantes === 1 ? 'persona' : 'personas'}</li>
              <li><span className="font-medium">Tiempo:</span> {sinPrisa ? 'Sin límite (itinerario completo)' : tiempoDisponible === 'personalizado' ? `${tiempoPersonalizado || '...'} minutos` : tiempoDisponible ? `${tiempoDisponible} minutos` : 'No especificado'}</li>
              <li><span className="font-medium">Detalle:</span> {nivelDetalle.charAt(0).toUpperCase() + nivelDetalle.slice(1)}</li>
            </ul>
          </div>

          <button onClick={handleGenerarItinerario} disabled={loading || (seleccionManual && areasSeleccionadas.length === 0)}
            className="w-full btn-primary py-4 text-lg disabled:opacity-50 disabled:cursor-not-allowed">
            <span className="flex items-center justify-center gap-3"><span>⚡</span><span>Generar Mi Itinerario (2 minutos)</span></span>
          </button>

          {seleccionManual && areasSeleccionadas.length === 0 && (
            <p className="text-center text-sm text-red-500 mt-3">Por favor, selecciona al menos una área para continuar</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default GenerarItinerarioPage;