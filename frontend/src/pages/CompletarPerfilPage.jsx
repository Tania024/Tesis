import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { visitantesAPI } from '../services/api';
import LoadingSpinner from '../components/Layout/LoadingSpinner';

const CompletarPerfilPage = () => {
  const navigate = useNavigate();
  const { user, updateUser } = useAuth();
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Estado del formulario (SOLO DATOS PERMANENTES)
  const [formData, setFormData] = useState({
    pais_origen: '',
    ciudad_origen: '',
    tipo_visitante: 'internacional',
    telefono: ''
  });

  // ✅ PAÍSES COMUNES
  const paises = [
    'Ecuador', 'Estados Unidos', 'España', 'México', 'Colombia',
    'Argentina', 'Chile', 'Perú', 'Brasil', 'Francia',
    'Italia', 'Alemania', 'Reino Unido', 'Canadá', 'Japón',
    'China', 'Australia', 'Venezuela', 'Bolivia', 'Paraguay'
  ];

  useEffect(() => {
    // Si el usuario ya completó su perfil, redirigir
    if (user && user.datos_completos) {
      navigate('/generar-itinerario');
    }
  }, [user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // ✅ VALIDAR CAMPOS OBLIGATORIOS
      if (!formData.pais_origen || !formData.ciudad_origen) {
        setError('Por favor, completa país y ciudad de origen');
        setLoading(false);
        return;
      }

      // ✅ ACTUALIZAR PERFIL EN BACKEND
      const updatedData = await visitantesAPI.update(user.visitante_id, {
        pais_origen: formData.pais_origen,
        ciudad_origen: formData.ciudad_origen,
        tipo_visitante: formData.tipo_visitante,
        telefono: formData.telefono || null
        // ❌ ELIMINADO: tipo_entrada y acompanantes
      });

      console.log('✅ Perfil actualizado:', updatedData);

      // ✅ ACTUALIZAR USUARIO EN CONTEXT Y LOCAL STORAGE
      updateUser({ 
        ...user, 
        datos_completos: true,
        ...formData 
      });
      
      // ✅ REDIRIGIR AL GENERADOR DE ITINERARIO
      navigate('/generar-itinerario', { replace: true });
      
    } catch (err) {
      console.error('❌ Error guardando perfil:', err);
      setError(err.response?.data?.detail || 'Error al guardar tu perfil. Intenta de nuevo.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4 mx-auto">
            <span className="text-4xl">👋</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">
            ¡Hola, {user?.nombre}! 👋
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Seria de gran ayuda si nos ayudas a rellenar estes datos
          </p>
        </div>

        {/* Card Principal */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="bg-gradient-to-r from-primary-600 to-primary-700 p-6 text-white">
            <h2 className="text-2xl font-bold flex items-center gap-3">
              <span>📋</span>
              <span>Completa tu Perfil</span>
            </h2>
            <p className="text-primary-100 mt-2">
              Esto nos ayudará a personalizar mejor tu experiencia en el museo
            </p>
          </div>

          <div className="p-6 md:p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* País y Ciudad */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    🌍 País de Origen <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={formData.pais_origen}
                    onChange={(e) => setFormData({ ...formData, pais_origen: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    required
                  >
                    <option value="">Selecciona tu país</option>
                    {paises.map((pais) => (
                      <option key={pais} value={pais}>{pais}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    🏙️ Ciudad de Origen <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.ciudad_origen}
                    onChange={(e) => setFormData({ ...formData, ciudad_origen: e.target.value })}
                    placeholder="Ej: Quito, Guayaquil, Madrid..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    required
                  />
                </div>
              </div>

              {/* Tipo de Visitante */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  👤 Tipo de Visitante <span className="text-red-500">*</span>
                </label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {[
                    { value: 'local', label: 'Local', icon: '🏠', desc: 'Residente de la ciudad' },
                    { value: 'nacional', label: 'Nacional', icon: '🇨🇴', desc: 'De otro estado/país' },
                    { value: 'internacional', label: 'Internacional', icon: '✈️', desc: 'De otro país' }
                  ].map((tipo) => (
                    <button
                      key={tipo.value}
                      type="button"
                      onClick={() => setFormData({ ...formData, tipo_visitante: tipo.value })}
                      className={`p-4 rounded-xl border-2 transition-all text-left ${
                        formData.tipo_visitante === tipo.value
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{tipo.icon}</span>
                        <div>
                          <div className="font-medium text-gray-900">{tipo.label}</div>
                          <div className="text-xs text-gray-600">{tipo.desc}</div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Teléfono (opcional) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  📱 Teléfono (opcional)
                </label>
                <input
                  type="tel"
                  value={formData.telefono}
                  onChange={(e) => setFormData({ ...formData, telefono: e.target.value })}
                  placeholder="+593 999 999 999"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Para enviarte tu itinerario por WhatsApp
                </p>
              </div>

              {/* Botón Submit */}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-primary-600 to-primary-700 text-white py-4 rounded-xl font-bold text-lg hover:from-primary-700 hover:to-primary-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="inline-block w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    Guardando tu perfil...
                  </span>
                ) : (
                  '✅ Completar Perfil y Generar Mi Itinerario'
                )}
              </button>
            </form>

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                <div className="flex items-start gap-2">
                  <span className="text-xl">⚠️</span>
                  <span>{error}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-6 text-sm text-gray-500">
          <p>🔒 Tus datos son confidenciales y solo se usan para mejorar tu experiencia</p>
        </div>
      </div>
    </div>
  );
};

export default CompletarPerfilPage;