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

  // 🔥 ESTADOS PARA MODALES BONITOS
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
    // ✅ VALIDACIÓN 1: Calificación general (CON MODAL BONITO)
    if (!calificacionGeneral) {
      setWarningModal({
        isOpen: true,
        message: '👆 Por favor selecciona una calificación general usando los emojis de arriba'
      });
      return;
    }

    // ✅ VALIDACIÓN 2: Todas las preguntas respondidas (CON MODAL BONITO)
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
      // 1. Enviar evaluación
      await onSubmit(evaluacion);
      
      // 2. Generar y enviar certificado
      console.log('📨 Generando certificado para itinerario:', itinerarioId);
      const response = await itinerariosAPI.generarCertificado(itinerarioId);
      
      console.log('✅ Certificado generado:', response);
      
      // 3. ✅ MOSTRAR MODAL DE ÉXITO (en lugar de alert feo)
      setSuccessModal(true);
      
    } catch (error) {
      console.error('❌ Error enviando evaluación o certificado:', error);
      console.error('Response:', error.response?.data);
      
      // ✅ MOSTRAR MODAL DE ERROR (en lugar de alert feo)
      const errorMessage = error.response?.data?.detail || 
                          error.message || 
                          'Error al procesar tu evaluación. Por favor, intenta de nuevo.';
      
      setErrorModal({
        isOpen: true,
        message: errorMessage
      });
    } finally {
      setEnviando(false);
    }
  };

  // ✅ CERRAR SUCCESS MODAL Y EL MODAL DE EVALUACIÓN
  const handleSuccessClose = () => {
    setSuccessModal(false);
    onClose(); // Cerrar el modal de evaluación también
  };

  if (!isOpen) return null;

  return (
    <>
      {/* MODAL PRINCIPAL DE EVALUACIÓN */}
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="sticky top-0 bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6 rounded-t-xl">
            <h2 className="text-2xl font-bold mb-2">¡Gracias por tu visita! 🎉</h2>
            <p className="text-purple-100">Tu opinión nos ayuda a mejorar la experiencia para futuros visitantes</p>
          </div>

          <div className="p-6 space-y-8">
            {/* Calificación general con emojis */}
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-4 text-center">
                ¿Cómo fue tu experiencia?
              </h3>
              
              <div className="flex justify-center gap-4">
                {emojis.map(({ valor, emoji, label, color }) => (
                  <button
                    key={valor}
                    onClick={() => setCalificacionGeneral(valor)}
                    className={`flex flex-col items-center p-4 rounded-xl transition-all transform hover:scale-110 ${
                      calificacionGeneral === valor
                        ? 'bg-purple-100 ring-4 ring-purple-500 scale-110'
                        : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                  >
                    <span className={`text-5xl ${color}`}>{emoji}</span>
                    <span className="text-xs font-medium text-gray-600 mt-2">{label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Separador */}
            <div className="border-t border-gray-200"></div>

            {/* Preguntas con thumbs */}
            <div className="space-y-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                Ayúdanos a mejorar respondiendo estas preguntas:
              </h3>

              {preguntas.map(({ id, texto }) => (
                <div key={id} className="bg-gray-50 rounded-lg p-4">
                  <p className="text-gray-800 font-medium mb-3">{texto}</p>
                  
                  <div className="flex justify-center gap-6">
                    {/* Thumbs Down */}
                    <button
                      onClick={() => handleRespuesta(id, false)}
                      className={`flex flex-col items-center p-3 rounded-lg transition-all transform hover:scale-105 ${
                        respuestas[id] === false
                          ? 'bg-red-100 ring-2 ring-red-500'
                          : 'bg-white hover:bg-gray-100'
                      }`}
                    >
                      <span className="text-3xl">👎</span>
                      <span className="text-xs font-medium text-gray-600 mt-1">No</span>
                    </button>

                    {/* Thumbs Up */}
                    <button
                      onClick={() => handleRespuesta(id, true)}
                      className={`flex flex-col items-center p-3 rounded-lg transition-all transform hover:scale-105 ${
                        respuestas[id] === true
                          ? 'bg-green-100 ring-2 ring-green-500'
                          : 'bg-white hover:bg-gray-100'
                      }`}
                    >
                      <span className="text-3xl">👍</span>
                      <span className="text-xs font-medium text-gray-600 mt-1">Sí</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Comentarios opcionales */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ¿Algo más que quieras compartir? (Opcional)
              </label>
              <textarea
                value={comentarios}
                onChange={(e) => setComentarios(e.target.value)}
                placeholder="Cuéntanos más sobre tu experiencia..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                rows="4"
              />
            </div>

            {/* Botones */}
            <div className="flex gap-4">
              <button
                onClick={onClose}
                disabled={enviando}
                className="flex-1 px-6 py-3 border-2 border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancelar
              </button>
              
              <button
                onClick={handleSubmit}
                disabled={enviando || !calificacionGeneral || Object.values(respuestas).some(r => r === null)}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
              >
                {enviando ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Enviando evaluación...
                  </span>
                ) : (
                  'Enviar Evaluación'
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 🔥 MODALES DE NOTIFICACIÓN BONITOS (REEMPLAZAN LOS ALERTS) */}
      <WarningModal 
        isOpen={warningModal.isOpen}
        message={warningModal.message}
        onClose={() => setWarningModal({ isOpen: false, message: '' })}
      />

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