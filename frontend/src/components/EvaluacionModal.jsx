import { useState } from 'react';
import { itinerariosAPI } from '../services/api';
import WarningModal from './UI/WarningModal';
import SuccessModal from './UI/SuccessModal';
import ErrorModal from './UI/ErrorModal';

const EvaluacionModal = ({ isOpen, onClose, onSubmit, itinerarioId }) => {
  const [calificacionGeneral, setCalificacionGeneral] = useState(null);
  const [respuestas, setRespuestas] = useState({
    personalizado: null,
    buenas_decisiones: null,
    acompaniamiento: null,
    comprension: null,
    relevante: null,
    usaria_nuevamente: null,
  });
  const [comentarios, setComentarios] = useState('');
  const [enviando, setEnviando] = useState(false);

  // Estados para modales
  const [warningModal, setWarningModal] = useState({ isOpen: false, message: '' });
  const [successModal, setSuccessModal] = useState(false);
  const [errorModal, setErrorModal] = useState({ isOpen: false, message: '' });

  const emojis = [
    { valor: 1, emoji: '😡', label: 'Muy mal', color: 'text-red-500' },
    { valor: 2, emoji: '😕', label: 'Mal', color: 'text-orange-500' },
    { valor: 3, emoji: '😐', label: 'Regular', color: 'text-yellow-500' },
    { valor: 4, emoji: '😊', label: 'Bien', color: 'text-green-500' },
    { valor: 5, emoji: '🤩', label: 'Excelente', color: 'text-purple-500' },
  ];

  const preguntas = [
    { id: 'personalizado', texto: '¿Sentiste que el itinerario fue personalizado para ti?' },
    { id: 'buenas_decisiones', texto: '¿El sistema tomó buenas decisiones al elegir las áreas del museo?' },
    { id: 'acompaniamiento', texto: '¿Te sentiste acompañado por una guía inteligente durante la visita?' },
    { id: 'comprension', texto: '¿El recorrido te ayudó a comprender mejor la historia y cultura del museo?' },
    { id: 'relevante', texto: '¿Sentiste que el contenido fue relevante para ti?' },
    { id: 'usaria_nuevamente', texto: '¿Usarías nuevamente este sistema para otra visita?' },
  ];

  const handleRespuesta = (preguntaId, valor) => {
    setRespuestas(prev => ({
      ...prev,
      [preguntaId]: valor,
    }));
  };

  const handleSubmit = async () => {
    if (!calificacionGeneral) {
      setWarningModal({
        isOpen: true,
        message: '👆 Por favor selecciona una calificación general usando los emojis de arriba'
      });
      return;
    }

    const todasRespondidas = Object.values(respuestas).every(r => r !== null);
    if (!todasRespondidas) {
      setWarningModal({
        isOpen: true,
        message: '📝 Por favor responde todas las preguntas con 👍 o 👎'
      });
      return;
    }

    setEnviando(true);

    const evaluacion = {
      itinerario_id: itinerarioId,
      calificacion_general: calificacionGeneral,
      ...respuestas,
      comentarios: comentarios || null,
      fecha: new Date().toISOString(),
    };

    try {
      // 1. Guardar evaluación
      await onSubmit(evaluacion);
      
      // 2. Marcar itinerario como completado
      await itinerariosAPI.actualizarItinerario(itinerarioId, { 
        estado: 'completado',
        fecha_fin: new Date().toISOString()
      });
      
      // 3. Intentar generar certificado (NO CRÍTICO)
      try {
        await itinerariosAPI.generarCertificado(itinerarioId);
      } catch (certError) {
        console.warn('⚠️ Certificado falló (no crítico)');
      }
      
      // 4. ✅ MOSTRAR MODAL DE ÉXITO SIEMPRE
      setSuccessModal(true);
      
    } catch (error) {
      console.error('❌ Error:', error);
      
      const errorMessage = error.response?.data?.detail || 
                          error.message || 
                          'Error al procesar tu evaluación';
      
      setErrorModal({
        isOpen: true,
        message: errorMessage
      });
    } finally {
      setEnviando(false);
    }
  };

  const handleSuccessClose = () => {
    setSuccessModal(false);
    onClose();
  };

  // ⚠️ IMPORTANTE: No cerrar el componente si el modal de éxito está abierto
  if (!isOpen && !successModal) return null;

  return (
    <>
      {/* MODAL DE EVALUACIÓN - Solo mostrar si NO está el modal de éxito */}
      {isOpen && !successModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-3 sm:p-4 md:p-6">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[95vh] sm:max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-gradient-to-r from-purple-600 to-blue-600 text-white p-4 sm:p-6 rounded-t-xl">
              <h2 className="text-lg sm:text-xl md:text-2xl font-bold mb-1 sm:mb-2">¡Gracias por tu visita! 🎉</h2>
              <p className="text-xs sm:text-sm md:text-base text-purple-100">Tu opinión nos ayuda a mejorar</p>
            </div>

            <div className="p-4 sm:p-6 space-y-6 sm:space-y-8">
              {/* Calificación */}
              <div>
                <h3 className="text-base sm:text-lg md:text-xl font-bold text-gray-900 mb-3 sm:mb-4 text-center">
                  ¿Cómo fue tu experiencia?
                </h3>
                
                <div className="flex justify-center gap-2 sm:gap-3 md:gap-4 flex-wrap">
                  {emojis.map(({ valor, emoji, label, color }) => (
                    <button
                      key={valor}
                      onClick={() => setCalificacionGeneral(valor)}
                      className={`flex flex-col items-center p-2 sm:p-3 md:p-4 rounded-xl transition-all ${
                        calificacionGeneral === valor
                          ? 'bg-purple-100 ring-2 sm:ring-4 ring-purple-500 scale-105'
                          : 'bg-gray-50'
                      }`}
                    >
                      <span className={`text-3xl sm:text-4xl md:text-5xl ${color}`}>{emoji}</span>
                      <span className="text-[10px] sm:text-xs font-medium text-gray-600 mt-1">{label}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="border-t border-gray-200"></div>

              {/* Preguntas */}
              <div className="space-y-4 sm:space-y-6">
                <h3 className="text-sm sm:text-base md:text-lg font-bold text-gray-900">
                  Ayúdanos a mejorar:
                </h3>

                {preguntas.map(({ id, texto }) => (
                  <div key={id} className="bg-gray-50 rounded-lg p-3 sm:p-4">
                    <p className="text-xs sm:text-sm md:text-base text-gray-800 font-medium mb-2 sm:mb-3">{texto}</p>
                    
                    <div className="flex justify-center gap-4 sm:gap-6">
                      <button
                        onClick={() => handleRespuesta(id, false)}
                        className={`flex flex-col items-center p-2 sm:p-3 rounded-lg transition-all ${
                          respuestas[id] === false
                            ? 'bg-red-100 ring-2 ring-red-500'
                            : 'bg-white'
                        }`}
                      >
                        <span className="text-2xl sm:text-3xl">👎</span>
                        <span className="text-[10px] sm:text-xs font-medium text-gray-600 mt-1">No</span>
                      </button>

                      <button
                        onClick={() => handleRespuesta(id, true)}
                        className={`flex flex-col items-center p-2 sm:p-3 rounded-lg transition-all ${
                          respuestas[id] === true
                            ? 'bg-green-100 ring-2 ring-green-500'
                            : 'bg-white'
                        }`}
                      >
                        <span className="text-2xl sm:text-3xl">👍</span>
                        <span className="text-[10px] sm:text-xs font-medium text-gray-600 mt-1">Sí</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Comentarios */}
              <div>
                <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-2">
                  ¿Algo más? (Opcional)
                </label>
                <textarea
                  value={comentarios}
                  onChange={(e) => setComentarios(e.target.value)}
                  placeholder="Cuéntanos más..."
                  className="w-full px-3 sm:px-4 py-2 sm:py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 resize-none text-sm sm:text-base"
                  rows="3"
                />
              </div>

              {/* Botones */}
              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                <button
                  onClick={onClose}
                  disabled={enviando}
                  className="w-full sm:flex-1 px-4 py-3 border-2 border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 disabled:opacity-50 text-sm sm:text-base"
                >
                  Cancelar
                </button>
                
                <button
                  onClick={handleSubmit}
                  disabled={enviando || !calificacionGeneral || Object.values(respuestas).some(r => r === null)}
                  className="w-full sm:flex-1 px-4 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 shadow-lg text-sm sm:text-base"
                >
                  {enviando ? 'Procesando...' : 'Enviar Evaluación'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODALES */}
      <WarningModal 
        isOpen={warningModal.isOpen}
        message={warningModal.message}
        onClose={() => setWarningModal({ isOpen: false, message: '' })}
      />

      {/* ✅ MODAL DE ÉXITO - SIEMPRE RENDERIZADO */}
      <SuccessModal 
        isOpen={successModal}
        onClose={handleSuccessClose}
      />

      <ErrorModal 
        error={errorModal.isOpen ? errorModal.message : null}
        onClose={() => setErrorModal({ isOpen: false, message: '' })}
      />
    </>
  );
};

export default EvaluacionModal;