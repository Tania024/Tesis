import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';

const Navbar = ({ user, onLogout }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <nav className="bg-white shadow-lg sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo y nombre */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-museo-brown to-museo-gold rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">MP</span>
                
              </div>
              <div className="hidden sm:block">
                <h1 className="text-xl font-bold text-gray-900">Museo Pumapungo</h1>
                <p className="text-xs text-gray-500">Sistema de Itinerarios</p>
              </div>
            </Link>
          </div>

          {/* Navegación Desktop */}
          <div className="hidden md:flex items-center space-x-4">
            <Link
              to="/areas"
              className="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
            >
              📍 Áreas
            </Link>
            
            {user ? (
              <>
                <Link
                  to="/generar"
                  className="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  🤖 Generar Itinerario
                </Link>
                <Link
                  to="/mis-itinerarios"
                  className="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  📋 Mis Itinerarios
                </Link>
                <Link
                  to="/admin"
                  className="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  ⚙️ Admin
                </Link>
                
                {/* Usuario */}
                <div className="flex items-center space-x-3 border-l pl-4">
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{user.nombre}</p>
                    <p className="text-xs text-gray-500">{user.codigo_visita}</p>
                  </div>
                  <button
                    onClick={onLogout}
                    className="text-red-600 hover:text-red-700 text-sm font-medium"
                  >
                    Salir
                  </button>
                </div>
              </>
            ) : (
              <Link
                to="/login"
                className="btn-primary"
              >
                Iniciar Sesión
              </Link>
            )}
          </div>

          {/* Botón menú móvil */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-gray-700 hover:text-primary-600"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {isMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Menú móvil */}
      {isMenuOpen && (
        <div className="md:hidden bg-white border-t">
          <div className="px-2 pt-2 pb-3 space-y-1">
            <Link
              to="/areas"
              className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-100"
              onClick={() => setIsMenuOpen(false)}
            >
              📍 Áreas del Museo
            </Link>
            
            {user ? (
              <>
                <Link
                  to="/generar"
                  className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-100"
                  onClick={() => setIsMenuOpen(false)}
                >
                  🤖 Generar Itinerario
                </Link>
                <Link
                  to="/mis-itinerarios"
                  className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-100"
                  onClick={() => setIsMenuOpen(false)}
                >
                  📋 Mis Itinerarios
                </Link>
                <Link
                  to="/admin"
                  className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-100"
                  onClick={() => setIsMenuOpen(false)}
                >
                  ⚙️ Panel Admin
                </Link>
                <button
                  onClick={() => {
                    onLogout();
                    setIsMenuOpen(false);
                  }}
                  className="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-red-600 hover:bg-red-50"
                >
                  Cerrar Sesión
                </button>
              </>
            ) : (
              <Link
                to="/login"
                className="block px-3 py-2 rounded-md text-base font-medium text-primary-600 hover:bg-primary-50"
                onClick={() => setIsMenuOpen(false)}
              >
                Iniciar Sesión con Google
              </Link>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;