// components/UI/SuccessModal.jsx
import { useEffect } from 'react';

const SuccessModal = ({ isOpen, onClose }) => {
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
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 transition-opacity duration-300"
      style={{ zIndex: 100 }}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="success-modal-title"
    >
      <div 
        className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden transform transition-all duration-300 scale-100 animate-fade-in"
        onClick={e => e.stopPropagation()}
      >
        {/* Barra superior decorativa */}
        <div className="h-1.5 bg-gradient-to-r from-green-400 to-emerald-500" />
        
        <div className="p-6">
          {/* Header con icono animado */}
          <div className="flex flex-col items-center mb-5">
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 w-20 h-20 rounded-2xl flex items-center justify-center mb-4 border-2 border-green-200 animate-bounce">
              <span className="text-5xl">🎉</span>
            </div>
            <h2 
              id="success-modal-title" 
              className="text-2xl font-bold text-gray-900 text-center"
            >
              ¡Gracias por tu evaluación!
            </h2>
          </div>

          {/* Mensaje principal */}
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-xl p-6 text-center space-y-4">
            <div className="text-green-900 font-medium leading-relaxed">
              <p className="text-lg mb-3">
                Tu opinión es muy valiosa para nosotros
              </p>
              <p className="text-sm text-green-700">
                Hemos enviado tu certificado de visita a tu correo electrónico 📧
              </p>
            </div>
            
            {/* Iconos decorativos */}
            <div className="flex justify-center gap-4 pt-3">
              <span className="text-3xl animate-pulse">✨</span>
              <span className="text-3xl">📜</span>
              <span className="text-3xl animate-pulse">✨</span>
            </div>
          </div>

          {/* Mensaje de despedida */}
          <div className="mt-4 text-center text-gray-600 text-sm">
            ¡Esperamos verte pronto de nuevo en el Museo Pumapungo! 🏛️
          </div>

          {/* Botón de acción */}
          <div className="mt-6 flex justify-center">
            <button
              onClick={() => {onClose(); navigate('/');
          }}
              className="px-8 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-semibold hover:from-green-600 hover:to-emerald-700 transition-all duration-200 shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-green-400 focus:ring-offset-2 w-full transform hover:scale-105"
            >
              🚀 Continuar
            </button>
          </div>
        </div>

        {/* Botón de cierre elegante */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 w-9 h-9 rounded-full bg-white/80 backdrop-blur-sm text-gray-500 hover:text-gray-700 hover:bg-white transition-all duration-200 shadow-sm flex items-center justify-center"
          aria-label="Cerrar mensaje de éxito"
        >
          <span className="text-xl">×</span>
        </button>
      </div>
    </div>
  );
};

export default SuccessModal;