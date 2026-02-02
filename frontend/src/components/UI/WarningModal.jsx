// components/UI/WarningModal.jsx
import { useEffect } from 'react';

const WarningModal = ({ isOpen, message, onClose }) => {
  // Cerrar modal con tecla Escape
  useEffect(() => {
    if (!isOpen) return;
    
    const handleEsc = (event) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 transition-opacity duration-300"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="warning-modal-title"
    >
      <div 
        className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden transform transition-all duration-300 scale-100 animate-fade-in"
        onClick={e => e.stopPropagation()}
      >
        {/* Barra superior decorativa */}
        <div className="h-1.5 bg-gradient-to-r from-yellow-400 to-orange-500" />
        
        <div className="p-6">
          {/* Header con icono */}
          <div className="flex flex-col items-center mb-5">
            <div className="bg-gradient-to-br from-yellow-50 to-orange-50 w-16 h-16 rounded-2xl flex items-center justify-center mb-4 border-2 border-yellow-200">
              <span className="text-4xl">⚠️</span>
            </div>
            <h2 
              id="warning-modal-title" 
              className="text-xl font-bold text-gray-900 text-center"
            >
              Oops, falta algo
            </h2>
          </div>

          {/* Mensaje */}
          <div className="bg-gradient-to-br from-yellow-50 to-orange-50 border border-yellow-200 rounded-xl p-5 text-yellow-900 text-center leading-relaxed font-medium">
            {message}
          </div>

          {/* Botón de acción */}
          <div className="mt-6 flex justify-center">
            <button
              onClick={onClose}
              className="px-6 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 text-white rounded-xl font-medium hover:from-yellow-600 hover:to-orange-600 transition-all duration-200 shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:ring-offset-2 w-full"
            >
              ✅ Entendido
            </button>
          </div>
        </div>

        {/* Botón de cierre elegante */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 w-9 h-9 rounded-full bg-white/80 backdrop-blur-sm text-gray-500 hover:text-gray-700 hover:bg-white transition-all duration-200 shadow-sm flex items-center justify-center"
          aria-label="Cerrar advertencia"
        >
          <span className="text-xl">×</span>
        </button>
      </div>
    </div>
  );
};

export default WarningModal;