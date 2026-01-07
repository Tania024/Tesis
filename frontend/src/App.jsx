import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Layout/Navbar';
import Footer from './components/Layout/Footer';

// Importar páginas (las crearemos después)
import Home from './pages/Home';
import Login from './pages/Login';
import AreasPage from './pages/AreasPage';
import GenerarItinerarioPage from './pages/GenerarItinerarioPage';
import MisItinerariosPage from './pages/MisItinerariosPage';
import VerItinerarioPage from './pages/VerItinerarioPage';
import VisitaEnProgresoPage from './pages/VisitaEnProgresoPage';
import AdminPage from './pages/AdminPage';

// Componente para rutas protegidas
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

// Layout principal
const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar user={user} onLogout={logout} />
      <main className="flex-grow">
        {children}
      </main>
      <Footer />
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Layout>
          <Routes>
            {/* Rutas públicas */}
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/areas" element={<AreasPage />} />
            
            {/* Rutas protegidas */}
            <Route
              path="/generar"
              element={
                <ProtectedRoute>
                  <GenerarItinerarioPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/mis-itinerarios"
              element={
                <ProtectedRoute>
                  <MisItinerariosPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/itinerario/:id"
              element={
                <ProtectedRoute>
                  <VerItinerarioPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/visita/:id"
              element={
                <ProtectedRoute>
                  <VisitaEnProgresoPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <ProtectedRoute>
                  <AdminPage />
                </ProtectedRoute>
              }
            />
            
            {/* 404 */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </Router>
    </AuthProvider>
  );
}

export default App;