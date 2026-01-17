import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const Navbar = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout(); // Llamar logout del context
    navigate('/'); // Navegar desde aquí (dentro del Router)
  };

  return (
    <nav className="bg-white shadow-lg sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo y Nombre */}
          <Link to="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
            <span className="text-3xl">🏛️</span>
            <div>
              <h1 className="text-xl font-bold text-museo-brown">
                Museo Pumapungo
              </h1>
              <p className="text-xs text-gray-600">Sistema de Itinerarios IA</p>
            </div>
          </Link>

          {/* Menú de Navegación */}
          <div className="flex items-center space-x-6">
            {isAuthenticated ? (
              <>
                {/* Enlaces para usuarios autenticados */}
                <Link
                  to="/areas"
                  className="text-gray-700 hover:text-primary-600 transition-colors font-medium flex items-center gap-1"
                >
                  <span>📍</span>
                  Áreas
                </Link>
                <Link
                  to="/generar-itinerario"
                  className="text-gray-700 hover:text-primary-600 transition-colors font-medium flex items-center gap-1"
                >
                  <span>🤖</span>
                  Generar Itinerario
                </Link>
                <Link
                  to="/mis-itinerarios"
                  className="text-gray-700 hover:text-primary-600 transition-colors font-medium flex items-center gap-1"
                >
                  <span>📋</span>
                  Mis Itinerarios
                </Link>
                <Link
                  to="/admin"
                  className="text-gray-700 hover:text-primary-600 transition-colors font-medium flex items-center gap-1"
                >
                  <span>📊</span>
                  Admin
                </Link>

                {/* Información del Usuario */}
                <div className="flex items-center space-x-3 border-l pl-6 ml-2">
                  <div className="flex items-center gap-2">
                    {user.picture ? (
                      <img
                        src={user.picture}
                        alt={user.nombre}
                        className="w-8 h-8 rounded-full border-2 border-primary-500"
                      />
                    ) : (
                      <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center text-white font-bold">
                        {user.nombre ? user.nombre[0].toUpperCase() : '👤'}
                      </div>
                    )}
                    <div className="hidden md:block">
                      <p className="text-sm font-medium text-gray-900">
                        {user.nombre || 'Usuario'}
                      </p>
                      <p className="text-xs text-gray-500">
                        {user.email || ''}
                      </p>
                    </div>
                  </div>
                  
                  <button
                    onClick={handleLogout}
                    className="text-sm text-red-600 hover:text-red-700 font-medium transition-colors px-3 py-1 rounded-lg hover:bg-red-50"
                  >
                    Salir
                  </button>
                </div>
              </>
            ) : (
              <>
                {/* Enlaces para usuarios NO autenticados */}
                <Link
                  to="/"
                  className="text-gray-700 hover:text-primary-600 transition-colors font-medium"
                >
                  Inicio
                </Link>
                <Link
                  to="/areas"
                  className="text-gray-700 hover:text-primary-600 transition-colors font-medium"
                >
                  Áreas
                </Link>
                <Link
                  to="/login"
                  className="btn-primary px-6 py-2"
                >
                  Iniciar Sesión
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;