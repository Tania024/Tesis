import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useState } from 'react';

const Navbar = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    setMenuOpen(false);
    navigate('/');
  };

  return (
    <nav className="bg-white shadow-lg sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">

          {/* Logo */}
          <Link
            to="/"
            className="flex items-center space-x-3 hover:opacity-80 transition-opacity"
            onClick={() => setMenuOpen(false)}
          >
            <img
              src={`${import.meta.env.BASE_URL}images/logo-museo.png`}
              alt="Museo Pumapungo"
              className="w-14 h-15 object-contain"
            />
            <div>
              <h1 className="text-xl font-bold text-museo-brown">
                Museo Pumapungo
              </h1>
              <p className="text-xs text-gray-600">
                Sistema de Itinerarios IA
              </p>
            </div>
          </Link>

          {/* Botón hamburguesa (mobile) */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden text-2xl focus:outline-none"
          >
            ☰
          </button>

          {/* Menú Desktop */}
          <div className="hidden md:flex items-center space-x-6">
            {isAuthenticated ? (
              <>
                <Link to="/areas" className="text-gray-700 hover:text-primary-600 font-medium flex gap-1">
                  📍 Áreas
                </Link>
                <Link to="/generar-itinerario" className="text-gray-700 hover:text-primary-600 font-medium flex gap-1">
                  🤖 Generar Itinerario
                </Link>
                <Link to="/mis-itinerarios" className="text-gray-700 hover:text-primary-600 font-medium flex gap-1">
                  📋 Mis Itinerarios
                </Link>
                <Link to="/admin" className="text-gray-700 hover:text-primary-600 font-medium flex gap-1">
                  📊 Admin
                </Link>

                {/* Usuario */}
                <div className="flex items-center space-x-3 border-l pl-6 ml-2">
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

                  <div className="hidden lg:block">
                    <p className="text-sm font-medium">{user.nombre}</p>
                    <p className="text-xs text-gray-500">{user.email}</p>
                  </div>

                  <button
                    onClick={handleLogout}
                    className="text-sm text-red-600 hover:text-red-700 px-3 py-1 rounded-lg hover:bg-red-50"
                  >
                    Salir
                  </button>
                </div>
              </>
            ) : (
              <>
                <Link to="/" className="text-gray-700 hover:text-primary-600 font-medium">
                  Inicio
                </Link>
                <Link to="/areas" className="text-gray-700 hover:text-primary-600 font-medium">
                  Áreas
                </Link>
                <Link to="/login" className="btn-primary px-6 py-2">
                  Iniciar Sesión
                </Link>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Menú Mobile */}
      {menuOpen && (
        <div className="md:hidden bg-white shadow-lg px-4 py-4 space-y-4 animate-fade-in">
          {isAuthenticated ? (
            <>
              <Link to="/areas" onClick={() => setMenuOpen(false)} className="block">
                📍 Áreas
              </Link>
              <Link to="/generar-itinerario" onClick={() => setMenuOpen(false)} className="block">
                🤖 Generar Itinerario
              </Link>
              <Link to="/mis-itinerarios" onClick={() => setMenuOpen(false)} className="block">
                📋 Mis Itinerarios
              </Link>
              <Link to="/admin" onClick={() => setMenuOpen(false)} className="block">
                📊 Admin
              </Link>

              <button
                onClick={handleLogout}
                className="text-red-600 font-medium w-full text-left"
              >
                Salir
              </button>
            </>
          ) : (
            <>
              <Link to="/" onClick={() => setMenuOpen(false)} className="block">
                Inicio
              </Link>
              <Link to="/areas" onClick={() => setMenuOpen(false)} className="block">
                Áreas
              </Link>
              <Link
                to="/login"
                onClick={() => setMenuOpen(false)}
                className="btn-primary w-full text-center"
              >
                Iniciar Sesión
              </Link>
            </>
          )}
        </div>
      )}
    </nav>
  );
};

export default Navbar;
