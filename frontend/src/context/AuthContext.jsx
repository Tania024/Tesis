import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Cargar usuario del localStorage al iniciar
  useEffect(() => {
    const loadUser = () => {
      try {
        const savedUser = localStorage.getItem('museo_user');
        if (savedUser) {
          const userData = JSON.parse(savedUser);
          console.log('👤 Usuario cargado del localStorage:', userData);
          setUser(userData);
        }
      } catch (error) {
        console.error('❌ Error al cargar usuario:', error);
        localStorage.removeItem('museo_user');
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, []);

  // Login con Google - guardar datos del usuario
  const loginWithGoogle = (userData) => {
    console.log('🔐 Guardando usuario en sesión:', userData);
    
    const userToSave = {
      visitante_id: userData.visitante_id,
      nombre: userData.nombre,
      email: userData.email,
      picture: userData.picture || null,
      authenticated: true,
      loginTime: new Date().toISOString()
    };

    setUser(userToSave);
    localStorage.setItem('museo_user', JSON.stringify(userToSave));
    
    console.log('✅ Usuario autenticado y guardado');
    return userToSave;
  };

  // Logout - NO usa navigate, el componente que llama logout debe hacerlo
  const logout = () => {
    console.log('👋 Cerrando sesión');
    setUser(null);
    localStorage.removeItem('museo_user');
    // NO navegamos aquí - el componente que llama logout lo hará
  };

  // Actualizar datos del usuario
  const updateUser = (newData) => {
    const updatedUser = { ...user, ...newData };
    setUser(updatedUser);
    localStorage.setItem('museo_user', JSON.stringify(updatedUser));
    console.log('✅ Usuario actualizado:', updatedUser);
  };

  const value = {
    user,
    loading,
    loginWithGoogle,
    logout,
    updateUser,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe usarse dentro de AuthProvider');
  }
  return context;
};