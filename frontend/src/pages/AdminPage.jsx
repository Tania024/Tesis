// src/pages/AdminPage.jsx


import { useState, useEffect } from 'react';
import { visitantesAPI, itinerariosAPI, historialAPI, evaluacionesAPI } from '../services/api';
import LoadingSpinner from '../components/Layout/LoadingSpinner';

const AdminPage = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [periodo, setPeriodo] = useState('hoy');
  
  // Estados para las estadísticas
  const [estadisticasVisitantes, setEstadisticasVisitantes] = useState(null);
  const [estadisticasItinerarios, setEstadisticasItinerarios] = useState(null);
  const [estadisticasHoy, setEstadisticasHoy] = useState(null);
  const [estadisticasEvaluaciones, setEstadisticasEvaluaciones] = useState(null);
  const [horasPico, setHorasPico] = useState([]);
  const [visitantesRecientes, setVisitantesRecientes] = useState([]);

  useEffect(() => {
    cargarEstadisticas();
  }, [periodo]);

  const cargarEstadisticas = async () => {
    try {
      setLoading(true);
      setError(null);

      const [
        visitantesStats,
        itinerariosStats,
        hoyStats,
        evaluacionesStats,
        pico,
        visitantesResponse
      ] = await Promise.all([
        visitantesAPI.estadisticas(),
        itinerariosAPI.estadisticas(),
        historialAPI.estadisticasHoy(),
        evaluacionesAPI.obtenerEstadisticas(),
        historialAPI.horasPico(),
        visitantesAPI.listar({ limit: 10 })
      ]);

      console.log('═══════════════════════════════════════');
      console.log('📊 DEBUG: Respuesta de visitantes');
      console.log('Tipo:', typeof visitantesResponse);
      console.log('Es array:', Array.isArray(visitantesResponse));
      if (visitantesResponse && !Array.isArray(visitantesResponse)) {
        console.log('Keys del objeto:', Object.keys(visitantesResponse));
      }
      console.log('═══════════════════════════════════════');

      setEstadisticasVisitantes(visitantesStats);
      setEstadisticasItinerarios(itinerariosStats);
      setEstadisticasEvaluaciones(evaluacionesStats);

      let visitantesArray = [];

      if (Array.isArray(visitantesResponse)) {
        visitantesArray = visitantesResponse;
        console.log('✅ Formato detectado: Array directo');
      } else if (visitantesResponse?.visitantes && Array.isArray(visitantesResponse.visitantes)) {
        visitantesArray = visitantesResponse.visitantes;
        console.log('✅ Formato detectado: {visitantes: [...]}');
      } else if (visitantesResponse?.data && Array.isArray(visitantesResponse.data)) {
        visitantesArray = visitantesResponse.data;
        console.log('✅ Formato detectado: {data: [...]}');
      } else if (visitantesResponse?.items && Array.isArray(visitantesResponse.items)) {
        visitantesArray = visitantesResponse.items;
        console.log('✅ Formato detectado: {items: [...]}');
      } else {
        console.warn('⚠️ Formato desconocido de respuesta');
      }

      console.log(`✅ Total visitantes procesados: ${visitantesArray.length}`);
      if (visitantesArray.length > 0) {
        console.log('👤 Primer visitante:', visitantesArray[0]);
      }

      setVisitantesRecientes(visitantesArray);

      const visitantesHoyCalculado = calcularVisitantesHoy(visitantesArray);
      console.log(`🌟 Visitantes de HOY (calculado en frontend): ${visitantesHoyCalculado}`);

      setEstadisticasHoy({
        visitantes_hoy: visitantesHoyCalculado,
        itinerarios_activos: hoyStats?.itinerarios_activos || 0,
        hora_entrada_promedio: hoyStats?.hora_entrada_promedio || null
      });

      setHorasPico(pico);

    } catch (err) {
      console.error('❌ Error al cargar estadísticas:', err);
      console.error('Error completo:', err.response?.data || err.message);
      setError('No se pudieron cargar las estadísticas del museo.');
    } finally {
      setLoading(false);
    }
  };

const formatearFecha = (fecha) => {
  if (!fecha) return 'N/A';
  // DB guarda UTC sin 'Z' → agregamos Z → convertimos a Ecuador (UTC-5)
  const fechaISO = fecha.replace(' ', 'T') + 'Z';
  return new Date(fechaISO).toLocaleString('es-EC', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
    timeZone: 'America/Guayaquil'  // UTC-5 → resta 5h → 04:30 → 23:30 ✅
  });
};

  const formatearTipoVisitante = (tipo) => {
    const tipos = {
      'local': 'Local',
      'nacional': 'Nacional',
      'internacional': 'Internacional'
    };
    return tipos[tipo] || tipo;
  };

  // ✅ NUEVO: Calcular edad desde fecha_nacimiento
  const calcularEdad = (fechaNacimiento) => {
    if (!fechaNacimiento) return 'N/A';
    const hoy = new Date();
    const nacimiento = new Date(fechaNacimiento);
    let edad = hoy.getFullYear() - nacimiento.getFullYear();
    const mes = hoy.getMonth() - nacimiento.getMonth();
    if (mes < 0 || (mes === 0 && hoy.getDate() < nacimiento.getDate())) {
      edad--;
    }
    return edad > 0 ? `${edad} años` : 'N/A';
  };

  // ✅ Proteger privacidad de emails
  const ofuscarEmail = (email) => {
    if (!email || typeof email !== 'string') return 'N/A';
    const partes = email.split('@');
    if (partes.length !== 2) return email;
    const [usuario, dominio] = partes;
    let usuarioOfuscado;
    if (usuario.length <= 3) {
      usuarioOfuscado = usuario.charAt(0) + '***';
    } else if (usuario.length <= 6) {
      usuarioOfuscado = usuario.substring(0, 2) + '***';
    } else {
      usuarioOfuscado = usuario.substring(0, 3) + '***';
    }
    return `${usuarioOfuscado}@${dominio}`;
  };

  // ✅ Calcular visitantes de hoy con zona horaria Ecuador
  const calcularVisitantesHoy = (visitantes) => {
    if (!visitantes || visitantes.length === 0) {
      console.log('⚠️ No hay visitantes para calcular');
      return 0;
    }

    const ahora = new Date();
    const hoyDia = ahora.getDate();
    const hoyMes = ahora.getMonth();
    const hoyAnio = ahora.getFullYear();

    console.log(`📅 Fecha de HOY: ${hoyDia}/${hoyMes + 1}/${hoyAnio}`);

    const visitantesDeHoy = visitantes.filter(v => {
      if (!v.fecha_registro) {
        console.log('⚠️ Visitante sin fecha_registro:', v.nombre);
        return false;
      }
      
      const fechaVisitante = new Date(v.fecha_registro);
      const visitanteDia = fechaVisitante.getDate();
      const visitanteMes = fechaVisitante.getMonth();
      const visitanteAnio = fechaVisitante.getFullYear();
      
      const esHoy = (
        visitanteDia === hoyDia &&
        visitanteMes === hoyMes &&
        visitanteAnio === hoyAnio
      );

      console.log(`👤 ${v.nombre}: ${visitanteDia}/${visitanteMes + 1}/${visitanteAnio} → ${esHoy ? '✅ ES HOY' : '❌ NO ES HOY'}`);
      
      return esHoy;
    });

    console.log(`🌟 RESULTADO: ${visitantesDeHoy.length} visitante(s) de hoy`);
    return visitantesDeHoy.length;
  };

  const obtenerEmojiCalificacion = (calificacion) => {
    if (calificacion >= 4.5) return '🤩';
    if (calificacion >= 3.5) return '😊';
    if (calificacion >= 2.5) return '😐';
    if (calificacion >= 1.5) return '😕';
    return '😡';
  };

  const obtenerColorPorcentaje = (porcentaje) => {
    if (porcentaje >= 80) return 'bg-green-500';
    if (porcentaje >= 60) return 'bg-blue-500';
    if (porcentaje >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (loading) return <LoadingSpinner />;

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <div className="text-4xl mb-4">❌</div>
          <h2 className="text-xl font-semibold text-red-800 mb-2">Error</h2>
          <p className="text-red-600 mb-4">{error}</p>
          <button onClick={cargarEstadisticas} className="btn-primary">
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-museo-cream to-white py-8">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
                <span className="text-4xl">📊</span>
                Panel Administrativo
              </h1>
              <p className="text-gray-600">
                Museo Pumapungo - Estadísticas y Análisis
              </p>
            </div>
            <button
              onClick={cargarEstadisticas}
              className="btn-secondary flex items-center gap-2"
            >
              <span>🔄</span>
              Actualizar Datos
            </button>
          </div>
        </div>

        {/* Tarjetas de Estadísticas Principales */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Visitantes */}
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-primary-500">
            <div className="flex items-center justify-between mb-2">
              <span className="text-3xl">👥</span>
              <span className="text-sm text-gray-500">Total</span>
            </div>
            <h3 className="text-3xl font-bold text-gray-900 mb-1">
              {estadisticasVisitantes?.total_visitantes || 0}
            </h3>
            <p className="text-sm text-gray-600">Visitantes Registrados</p>
          </div>

          {/* Visitantes Hoy */}
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
            <div className="flex items-center justify-between mb-2">
              <span className="text-3xl">🌟</span>
              <span className="text-sm text-gray-500">Hoy</span>
            </div>
            <h3 className="text-3xl font-bold text-gray-900 mb-1">
              {estadisticasHoy?.visitantes_hoy || 0}
            </h3>
            <p className="text-sm text-gray-600">Visitantes Hoy</p>
          </div>

          {/* Itinerarios Generados */}
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-purple-500">
            <div className="flex items-center justify-between mb-2">
              <span className="text-3xl">🤖</span>
              <span className="text-sm text-gray-500">IA</span>
            </div>
            <h3 className="text-3xl font-bold text-gray-900 mb-1">
              {estadisticasItinerarios?.total_itinerarios || 0}
            </h3>
            <p className="text-sm text-gray-600">Itinerarios con IA</p>
          </div>

          {/* Satisfacción Promedio */}
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-yellow-500">
            <div className="flex items-center justify-between mb-2">
              <span className="text-3xl">
                {estadisticasEvaluaciones?.calificacion_promedio 
                  ? obtenerEmojiCalificacion(estadisticasEvaluaciones.calificacion_promedio)
                  : '⭐'}
              </span>
              <span className="text-sm text-gray-500">Rating</span>
            </div>
            <h3 className="text-3xl font-bold text-gray-900 mb-1">
              {estadisticasEvaluaciones?.calificacion_promedio 
                ? estadisticasEvaluaciones.calificacion_promedio.toFixed(1)
                : 'N/A'}
            </h3>
            <p className="text-sm text-gray-600">
              {estadisticasEvaluaciones?.satisfaccion_general || 'Satisfacción Promedio'}
            </p>
            {estadisticasEvaluaciones?.total_evaluaciones > 0 && (
              <p className="text-xs text-gray-500 mt-1">
                {estadisticasEvaluaciones.total_evaluaciones} evaluaciones
              </p>
            )}
          </div>
        </div>

        {/* Estadísticas Detalladas de Evaluaciones */}
        {estadisticasEvaluaciones && estadisticasEvaluaciones.total_evaluaciones > 0 && (
          <div className="bg-white rounded-xl shadow-md p-6 mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
              <span>📋</span>
              Evaluación de Experiencia del Visitante
            </h2>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Columna 1: Métricas Principales */}
              <div className="space-y-4">
                <div className="p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border-2 border-purple-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-gray-700">Calificación General</span>
                    <span className="text-4xl">
                      {obtenerEmojiCalificacion(estadisticasEvaluaciones.calificacion_promedio)}
                    </span>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-bold text-purple-600">
                      {estadisticasEvaluaciones.calificacion_promedio.toFixed(1)}
                    </span>
                    <span className="text-2xl text-gray-500">/ 5.0</span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    {estadisticasEvaluaciones.satisfaccion_general}
                  </p>
                </div>

                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-700">Total de Evaluaciones</span>
                    <span className="text-2xl font-bold text-gray-900">
                      {estadisticasEvaluaciones.total_evaluaciones}
                    </span>
                  </div>
                </div>
              </div>

              {/* Columna 2: Preguntas Específicas */}
              <div className="space-y-3">
                <h3 className="font-semibold text-gray-900 mb-3">Respuestas Positivas</h3>
                
                {[
                  { label: '¿Fue personalizado?', valor: estadisticasEvaluaciones.porcentaje_personalizado },
                  { label: '¿Buenas decisiones de áreas?', valor: estadisticasEvaluaciones.porcentaje_buenas_decisiones },
                  { label: '¿Guía inteligente?', valor: estadisticasEvaluaciones.porcentaje_acompaniamiento },
                  { label: '¿Mejoró comprensión?', valor: estadisticasEvaluaciones.porcentaje_comprension },
                  { label: '¿Contenido relevante?', valor: estadisticasEvaluaciones.porcentaje_relevante },
                  { label: '¿Usaría nuevamente?', valor: estadisticasEvaluaciones.porcentaje_usaria_nuevamente },
                ].map((item, idx) => (
                  <div key={idx}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-700">{item.label}</span>
                      <span className="text-sm font-semibold text-gray-900">
                        {item.valor?.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${obtenerColorPorcentaje(item.valor)}`}
                        style={{ width: `${item.valor}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Fila 2: Estadísticas Detalladas */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Distribución por Tipo de Visitante */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span>🌍</span>
              Distribución de Visitantes
            </h2>
            {estadisticasVisitantes?.visitantes_por_tipo && Object.keys(estadisticasVisitantes.visitantes_por_tipo).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(estadisticasVisitantes.visitantes_por_tipo).map(([tipo, cantidad]) => {
                  const total = estadisticasVisitantes.total_visitantes;
                  const porcentaje = total > 0 ? ((cantidad / total) * 100).toFixed(1) : 0;
                  
                  return (
                    <div key={tipo}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-gray-700">
                          {formatearTipoVisitante(tipo)}
                        </span>
                        <span className="text-sm text-gray-600">
                          {cantidad} ({porcentaje}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div
                          className="bg-gradient-to-r from-primary-500 to-primary-600 h-3 rounded-full transition-all duration-500"
                          style={{ width: `${porcentaje}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                No hay datos de distribución disponibles
              </p>
            )}
          </div>

          {/* ✅ CORREGIDO: Solo 3 estados en Itinerarios */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span>📈</span>
              Estado de Itinerarios
            </h2>
            {estadisticasItinerarios?.itinerarios_por_estado && Object.keys(estadisticasItinerarios.itinerarios_por_estado).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(estadisticasItinerarios.itinerarios_por_estado)
                  .filter(([estado]) => ['generado', 'activo', 'completado'].includes(estado)) // ✅ Solo 3 estados
                  .map(([estado, cantidad]) => {
                    const total = estadisticasItinerarios.total_itinerarios;
                    const porcentaje = total > 0 ? ((cantidad / total) * 100).toFixed(1) : 0;
                    
                    const estadoConfig = {
                      'generado':   { color: 'from-blue-500 to-blue-600',   emoji: '📝', label: 'Generados'   },
                      'activo':     { color: 'from-green-500 to-green-600', emoji: '✅', label: 'Activos'     },
                      'completado': { color: 'from-purple-500 to-purple-600', emoji: '🎉', label: 'Completados' }
                    };
                    
                    const config = estadoConfig[estado] || { color: 'from-gray-500 to-gray-600', emoji: '📋', label: estado };
                    
                    return (
                      <div key={estado}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-gray-700 flex items-center gap-2">
                            <span>{config.emoji}</span>
                            {config.label}
                          </span>
                          <span className="text-sm text-gray-600">
                            {cantidad} ({porcentaje}%)
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3">
                          <div
                            className={`bg-gradient-to-r ${config.color} h-3 rounded-full transition-all duration-500`}
                            style={{ width: `${porcentaje}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                No hay datos de estado de itinerarios disponibles
              </p>
            )}
          </div>
        </div>

        {/* Fila 3: Horas Pico y Actividad de Hoy */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Horas Pico */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span>⏰</span>
              Horas Pico del Museo
            </h2>
            {horasPico && horasPico.length > 0 ? (
              <div className="space-y-3">
                {horasPico.slice(0, 5).map((hora, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gradient-to-r from-primary-50 to-white rounded-lg border border-primary-100"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl font-bold text-primary-600">
                        #{index + 1}
                      </span>
                      <span className="font-medium text-gray-900">
                        {hora.hora || hora}
                      </span>
                    </div>
                    {hora.visitantes && (
                      <span className="px-3 py-1 bg-primary-500 text-white rounded-full text-sm font-semibold">
                        {hora.visitantes} visitantes
                      </span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-4xl mb-3">⏰</div>
                <p className="text-gray-600 font-medium mb-2">
                  Aún no hay suficientes datos
                </p>
                <p className="text-gray-500 text-sm">
                  Las horas pico se calcularán automáticamente cuando haya más visitas registradas
                </p>
              </div>
            )}
          </div>

          {/* Estadísticas de Hoy */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span>📅</span>
              Actividad de Hoy
            </h2>
            <div className="space-y-4">
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">Visitantes de Hoy</span>
                  <span className="text-2xl font-bold text-blue-600">
                    {estadisticasHoy?.visitantes_hoy || 0}
                  </span>
                </div>
              </div>
              <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">Itinerarios Activos</span>
                  <span className="text-2xl font-bold text-green-600">
                    {estadisticasHoy?.itinerarios_activos || 0}
                  </span>
                </div>
              </div>
              {estadisticasHoy?.hora_entrada_promedio && (
                <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-700">Hora Promedio Entrada</span>
                    <span className="text-xl font-bold text-purple-600">
                      {estadisticasHoy.hora_entrada_promedio}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Tabla de Visitantes Recientes */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span>👤</span>
            Visitantes Recientes
          </h2>
          {visitantesRecientes.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Nombre</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Email</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Tipo</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Edad</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Registro</th>
                  </tr>
                </thead>
                <tbody>
                  {visitantesRecientes.map((visitante, index) => (
                    <tr
                      key={visitante.id}
                      className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                        index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                      }`}
                    >
                      <td className="py-3 px-4 text-sm text-gray-900">
                        {visitante.nombre}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600 font-mono">
                        {ofuscarEmail(visitante.email)}
                      </td>
                      <td className="py-3 px-4">
  {visitante.tipo_visitante ? (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
      visitante.tipo_visitante === 'internacional'
        ? 'bg-purple-100 text-purple-700'
        : visitante.tipo_visitante === 'nacional'
        ? 'bg-blue-100 text-blue-700'
        : 'bg-green-100 text-green-700'
    }`}>
      {formatearTipoVisitante(visitante.tipo_visitante)}
    </span>
  ) : (
    <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
      Sin definir
    </span>
  )}
</td>
                      {/* ✅ CORREGIDO: Edad calculada desde fecha_nacimiento */}
                      <td className="py-3 px-4 text-sm text-gray-600">
                        {calcularEdad(visitante.fecha_nacimiento)}
                      </td>
                      {/* ✅ CORREGIDO: Fecha con zona horaria Ecuador */}
                      <td className="py-3 px-4 text-sm text-gray-600">
                        {formatearFecha(visitante.fecha_registro)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">
              No hay visitantes registrados aún
            </p>
          )}
        </div>

        {/* Resumen Final */}
        <div className="mt-8 bg-gradient-to-r from-museo-brown to-museo-gold text-white rounded-xl shadow-lg p-8">
          <div className="text-center">
            <h3 className="text-2xl font-bold mb-2">
              Sistema de Itinerarios con IA
            </h3>
            <p className="text-museo-cream mb-4">
              Museo Pumapungo - Universidad Politécnica Salesiana
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
              <div>
                <div className="text-3xl font-bold mb-1">
                  {estadisticasItinerarios?.generados_con_ia || 0}
                </div>
                <div className="text-sm text-museo-cream">
                  Itinerarios Personalizados
                </div>
              </div>
              <div>
                <div className="text-3xl font-bold mb-1">
                  {estadisticasVisitantes?.total_visitantes || 0}
                </div>
                <div className="text-sm text-museo-cream">
                  Visitantes Únicos
                </div>
              </div>
              <div>
                <div className="text-3xl font-bold mb-1">
                  {estadisticasEvaluaciones?.calificacion_promedio 
                    ? `${estadisticasEvaluaciones.calificacion_promedio.toFixed(1)}⭐`
                    : 'N/A'}
                </div>
                <div className="text-sm text-museo-cream">
                  Satisfacción General
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;