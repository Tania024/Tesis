// components/UI/ErrorModal.jsx (VERSIÓN MEJORADA)
import { useEffect } from 'react';

const ErrorModal = ({ error, onClose }) => {
  // Cerrar modal con tecla Escape
  useEffect(() => {
    if (!error) return;
    
    const handleEsc = (event) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [error, onClose]);

  if (!error) return null;

  // Procesar el mensaje para convertir \n en saltos reales y **texto** en negritas
  const formattedMessage = error
    .replace(/\\n/g, '\n') // Corregir doble escape de Python
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Convertir **texto** a negritas
    .replace(/•/g, '•'); // Mantener viñetas

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 transition-opacity duration-300"
      style={{ zIndex: 100 }}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="error-modal-title"
    >
      <div 
        className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-hidden transform transition-all duration-300 scale-100 animate-fade-in"
        onClick={e => e.stopPropagation()}
      >
        {/* Barra superior decorativa */}
        <div className="h-1.5 bg-gradient-to-r from-rose-400 to-pink-500" />
        
        <div className="p-6">
          {/* Header con icono */}
          <div className="flex flex-col items-center mb-5">
            <div className="bg-gradient-to-br from-rose-50 to-pink-50 w-16 h-16 rounded-2xl flex items-center justify-center mb-4 border-2 border-rose-100">
              <span className="text-4xl">😔</span>
            </div>
            <h2 
              id="error-modal-title" 
              className="text-xl font-bold text-gray-900 text-center"
            >
              Algo salió mal
            </h2>
            <p className="text-gray-500 text-center mt-1 text-sm">
              No pudimos procesar tu solicitud
            </p>
          </div>

          {/* Contenedor de mensaje con scroll */}
          <div 
            className="bg-gradient-to-br from-rose-50 to-pink-50 border border-rose-200 rounded-xl p-5 max-h-72 overflow-y-auto text-rose-800 text-sm leading-relaxed font-medium whitespace-pre-wrap"
            dangerouslySetInnerHTML={{ __html: formattedMessage }}
          />

          {/* Sugerencia */}
          <div className="mt-4 text-center text-gray-600 text-xs">
            💡 Si el problema persiste, contacta a soporte
          </div>

          {/* Botón de acción */}
          <div className="mt-6 flex justify-center">
            <button
              onClick={onClose}
              className="px-6 py-3 bg-gradient-to-r from-rose-500 to-pink-600 text-white rounded-xl font-medium hover:from-rose-600 hover:to-pink-700 transition-all duration-200 shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-rose-400 focus:ring-offset-2 w-full"
            >
              ✨ Entendido
            </button>
          </div>
        </div>

        {/* Botón de cierre elegante */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 w-9 h-9 rounded-full bg-white/80 backdrop-blur-sm text-gray-500 hover:text-gray-700 hover:bg-white transition-all duration-200 shadow-sm flex items-center justify-center"
          aria-label="Cerrar mensaje de error"
        >
          <span className="text-xl">×</span>
        </button>
      </div>
    </div>
  );
};

export default ErrorModal;