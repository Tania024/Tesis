import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../services/api';
import LoadingSpinner from '../components/Layout/LoadingSpinner';

const Login = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, isAuthenticated } = useAuth();
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [processingCallback, setProcessingCallback] = useState(false);

  // Redirigir si ya está autenticado
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/generar');
    }
  }, [isAuthenticated, navigate]);

  // Procesar callback de Google (si viene del redirect)
  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    
    if (code && !processingCallback) {
      handleGoogleCallback(code, state);
    }
  }, [searchParams]);

  const handleGoogleLogin = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Obtener URL de autorización de Google
      const response = await authAPI.getGoogleLoginUrl();
      
      // Redirigir a Google
      window.location.href = response.authorization_url;
      
    } catch (err) {
      console.error('Error iniciando login:', err);
      setError('Error al conectar con Google. Inténtalo de nuevo.');
      setLoading(false);
    }
  };

  const handleGoogleCallback = async (code, state) => {
    setProcessingCallback(true);
    setLoading(true);
    
    try {
      // El backend procesa el código automáticamente en el callback
      // Solo esperamos que la URL actual contenga la respuesta
      
      // Simular pequeña espera mientras el backend procesa
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Aquí deberías obtener los datos del visitante desde el backend
      // Por ahora, simulamos que el login fue exitoso
      
      const mockUser = {
        visitante_id: 1,
        nombre: 'Usuario',
        codigo_visita: 'PMP-20241223-0001',
        email: 'usuario@gmail.com'
      };
      
      login(mockUser);
      navigate('/generar');
      
    } catch (err) {
      console.error('Error procesando callback:', err);
      setError('Error al procesar la autenticación. Inténtalo de nuevo.');
      setProcessingCallback(false);
      setLoading(false);
    }
  };

  if (processingCallback || loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner message="Procesando autenticación con Google..." />
          <p className="mt-4 text-gray-600">
            Analizando tus subscripciones de YouTube...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {/* Card */}
        <div className="card">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="w-20 h-20 bg-gradient-to-br from-museo-brown to-museo-gold rounded-2xl flex items-center justify-center mx-auto mb-4">
              <span className="text-white font-bold text-3xl">MP</span>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Museo Pumapungo
            </h1>
            <p className="text-gray-600">
              Inicia sesión para generar tu itinerario personalizado
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {/* Google Login Button */}
          <button
            onClick={handleGoogleLogin}
            disabled={loading}
            className="w-full bg-white border-2 border-gray-300 text-gray-700 px-6 py-4 rounded-lg font-semibold hover:bg-gray-50 hover:border-gray-400 transition-all flex items-center justify-center space-x-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-6 h-6" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span>Continuar con Google</span>
          </button>

          {/* Info */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <p className="text-sm text-gray-600 text-center mb-4">
              Al iniciar sesión, autorizas el acceso a:
            </p>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-start">
                <span className="text-green-500 mr-2">✓</span>
                <span>Tu perfil básico de Google</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-500 mr-2">✓</span>
                <span>Tus subscripciones de YouTube (para detectar intereses)</span>
              </li>
            </ul>
            <p className="text-xs text-gray-500 text-center mt-4">
              Tus datos están protegidos y no se comparten con terceros
            </p>
          </div>
        </div>

        {/* Link alternativo */}
        <p className="text-center mt-6 text-gray-600">
          ¿Solo quieres explorar?{' '}
          <button
            onClick={() => navigate('/areas')}
            className="text-primary-600 hover:text-primary-700 font-semibold"
          >
            Ver áreas del museo
          </button>
        </p>
      </div>
    </div>
  );
};

export default Login;