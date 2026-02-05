// C:\Users\Tania\Documents\Tesis\frontend\src\components\PWAInstallPrompt.tsx
import React, { useState, useEffect } from 'react';

const PWAInstallPrompt: React.FC = () => {
  const [showInstall, setShowInstall] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);

  useEffect(() => {
    // Escuchar el evento beforeinstallprompt
    const handleBeforeInstallPrompt = (e: any) => {
      // Prevenir la instalación automática
      e.preventDefault();
      // Guardar el evento para usarlo después
      setDeferredPrompt(e);
      // Mostrar el botón de instalación
      setShowInstall(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, []);

  const handleInstallClick = async () => {
    if (deferredPrompt) {
      // Mostrar el diálogo de instalación
      deferredPrompt.prompt();
      
      // Esperar la respuesta del usuario
      const { outcome } = await deferredPrompt.userChoice;
      
      // Ocultar el botón
      setShowInstall(false);
      setDeferredPrompt(null);

      // Log del resultado
      console.log(`User response to the install prompt: ${outcome}`);
    }
  };

  // Si ya está instalado como PWA, no mostrar nada
  if (window.matchMedia('(display-mode: standalone)').matches) {
    return null;
  }

  if (!showInstall) {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 right-4 bg-white border border-gray-200 rounded-xl shadow-lg p-4 z-50 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-900">
            📱 ¡Instala esta app en tu dispositivo!
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Obtén acceso rápido y funciona offline
          </p>
        </div>
        <button
          onClick={handleInstallClick}
          className="ml-3 bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-primary-700 transition-colors shadow"
        >
          Instalar
        </button>
      </div>
    </div>
  );
};

export default PWAInstallPrompt;