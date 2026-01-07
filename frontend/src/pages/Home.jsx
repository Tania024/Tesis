import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Home = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleGoogleLogin = () => {
    navigate('/login');
  };

  const features = [
    {
      icon: '🤖',
      title: 'IA Generativa',
      description: 'Itinerarios personalizados generados por DeepSeek-R1:7b según tus intereses reales'
    },
    {
      icon: '📺',
      title: 'Basado en YouTube',
      description: 'Analizamos tus subscripciones de YouTube para detectar automáticamente tus intereses culturales'
    },
    {
      icon: '🎯',
      title: '100% Personalizado',
      description: 'Cada itinerario es único, adaptado a tu tiempo disponible y nivel de detalle preferido'
    }
  ];

  return (
    <div className="min-h-screen">
      {/* HERO SECTION CON IMAGEN DE FONDO - ESTILO MUSEO OFICIAL */}
      <section className="relative h-screen flex items-center justify-center overflow-hidden">
        {/* Background Image */}
        <div 
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{
            backgroundImage: `url('https://pumapungo.gob.ec/assets/icono-COt22KoM.png')`,
            // NOTA: Reemplaza esta URL con una imagen del Museo Pumapungo real
            // Por ejemplo: backgroundImage: `url('/museo-pumapungo-hero.jpg')`
          }}
        >
          {/* Overlay oscuro para mejorar legibilidad */}
          <div className="absolute inset-0 bg-gradient-to-br from-black/70 via-black/60 to-black/70" />
          
          {/* Patrón decorativo sutil */}
          <div 
            className="absolute inset-0 opacity-10"
            style={{
              backgroundImage: `repeating-linear-gradient(45deg, transparent, transparent 100px, rgba(255,255,255,0.03) 100px, rgba(255,255,255,0.03) 200px)`
            }}
          />
        </div>

        {/* Content sobre la imagen */}
        <div className="relative z-10 container mx-auto px-4">
          <div className="max-w-5xl mx-auto text-center">
            {/* Logo/Icon animado */}
            <div className="mb-8 animate-pulse">
              <span className="text-9xl drop-shadow-2xl">🏛️</span>
            </div>

            {/* Título principal - Estilo oficial del museo */}
            <div className="mb-6">
              <h2 className="text-2xl md:text-3xl text-museo-gold font-light tracking-wider mb-4 uppercase">
                Icónico • Mágico • Único
              </h2>
              <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold text-white mb-6 tracking-tight">
                MUSEO
                <span className="block text-museo-gold mt-2">PUMAPUNGO</span>
              </h1>
            </div>

            {/* Subtítulo descriptivo */}
            <p className="text-xl md:text-2xl text-white/90 mb-12 max-w-3xl mx-auto leading-relaxed font-light">
              Descubre las culturas ancestrales del Ecuador con{' '}
              <span className="text-museo-gold font-semibold">itinerarios personalizados</span>{' '}
              generados por{' '}
              <span className="text-museo-gold font-semibold">Inteligencia Artificial</span>
            </p>

            {/* Botones CTA principales */}
            <div className="flex flex-col sm:flex-row gap-6 justify-center items-center mb-16">
              {!user ? (
                <>
                  <button
                    onClick={handleGoogleLogin}
                    className="group relative px-10 py-5 text-xl font-bold text-white bg-gradient-to-r from-museo-gold to-yellow-600 rounded-full overflow-hidden shadow-2xl hover:shadow-museo-gold/50 transition-all duration-300 transform hover:scale-105"
                  >
                    <span className="relative z-10 flex items-center gap-3">
                      🔑 Iniciar con Google
                    </span>
                    <div className="absolute inset-0 bg-gradient-to-r from-yellow-600 to-museo-gold transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
                  </button>
                  <Link
                    to="/areas"
                    className="px-10 py-5 text-xl font-bold text-white bg-white/10 backdrop-blur-sm border-2 border-white/50 rounded-full hover:bg-white/20 transition-all duration-300 flex items-center gap-3"
                  >
                    📍 Explorar Áreas
                  </Link>
                </>
              ) : (
                <>
                  <Link
                    to="/generar-itinerario"
                    className="group relative px-10 py-5 text-xl font-bold text-white bg-gradient-to-r from-museo-gold to-yellow-600 rounded-full overflow-hidden shadow-2xl hover:shadow-museo-gold/50 transition-all duration-300 transform hover:scale-105"
                  >
                    <span className="relative z-10 flex items-center gap-3">
                      🤖 Generar Mi Itinerario
                    </span>
                    <div className="absolute inset-0 bg-gradient-to-r from-yellow-600 to-museo-gold transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
                  </Link>
                  <Link
                    to="/mis-itinerarios"
                    className="px-10 py-5 text-xl font-bold text-white bg-white/10 backdrop-blur-sm border-2 border-white/50 rounded-full hover:bg-white/20 transition-all duration-300 flex items-center gap-3"
                  >
                    📋 Mis Itinerarios
                  </Link>
                </>
              )}
            </div>

            {/* Scroll indicator */}
            <div className="animate-bounce">
              <div className="flex flex-col items-center gap-2 text-white/70">
                <span className="text-sm uppercase tracking-wider">Descubre más</span>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* Decorative elements */}
        <div className="absolute bottom-0 left-0 w-full">
          <svg viewBox="0 0 1440 120" xmlns="http://www.w3.org/2000/svg" className="w-full">
            <path
              fill="#ffffff"
              d="M0,64L48,69.3C96,75,192,85,288,80C384,75,480,53,576,48C672,43,768,53,864,58.7C960,64,1056,64,1152,58.7C1248,53,1344,43,1392,37.3L1440,32L1440,120L1392,120C1344,120,1248,120,1152,120C1056,120,960,120,864,120C768,120,672,120,576,120C480,120,384,120,288,120C192,120,96,120,48,120L0,120Z"
            />
          </svg>
        </div>
      </section>

      {/* SECCIÓN DE CARACTERÍSTICAS - Con cards visuales */}
      <section className="py-24 bg-white relative">
        <div className="container mx-auto px-4">
          <div className="text-center mb-20">
            <span className="text-museo-gold font-semibold text-lg uppercase tracking-wider">Tecnología Innovadora</span>
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mt-4 mb-6">
              Experiencia Personalizada con IA
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Combinamos inteligencia artificial con tus intereses personales para crear el itinerario perfecto
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {features.map((feature, index) => (
              <div
                key={index}
                className="group relative bg-white rounded-3xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 hover:-translate-y-4 border border-gray-100 overflow-hidden"
              >
                {/* Background gradient on hover */}
                <div className="absolute inset-0 bg-gradient-to-br from-museo-gold/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                
                <div className="relative z-10">
                  <div className="text-7xl mb-6 transform group-hover:scale-110 transition-transform duration-300">
                    {feature.icon}
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-4">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    {feature.description}
                  </p>
                </div>

                {/* Decorative corner */}
                <div className="absolute -top-10 -right-10 w-32 h-32 bg-museo-gold/10 rounded-full blur-2xl group-hover:bg-museo-gold/20 transition-colors duration-300" />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECCIÓN DE ESTADÍSTICAS DEL MUSEO - Con fondo oscuro dramático */}
      <section className="relative py-24 bg-gradient-to-br from-gray-900 via-museo-brown to-gray-900 text-white overflow-hidden">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute inset-0" style={{
            backgroundImage: `radial-gradient(circle at 20% 50%, white 1px, transparent 1px), radial-gradient(circle at 80% 50%, white 1px, transparent 1px)`,
            backgroundSize: '50px 50px'
          }} />
        </div>

        <div className="container mx-auto px-4 relative z-10">
          <div className="text-center mb-20">
            <span className="text-museo-gold font-semibold text-lg uppercase tracking-wider">Patrimonio Cultural</span>
            <h2 className="text-4xl md:text-5xl font-bold mt-4 mb-6">
              Museo Pumapungo
            </h2>
            <p className="text-xl text-white/80 max-w-3xl mx-auto">
              Un espacio cultural que preserva y difunde el patrimonio arqueológico y etnográfico del Ecuador
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-5xl mx-auto">
            {[
              { number: '8', label: 'Áreas Temáticas', icon: '🏛️' },
              { number: '3000+', label: 'Piezas Arqueológicas', icon: '🏺' },
              { number: '5 Ha', label: 'Jardín Botánico', icon: '🌿' },
              { number: 'UNESCO', label: 'Patrimonio', icon: '🏆' }
            ].map((stat, index) => (
              <div
                key={index}
                className="text-center group cursor-pointer"
              >
                <div className="bg-white/10 backdrop-blur-sm rounded-3xl p-8 hover:bg-white/20 transition-all duration-300 transform hover:scale-105 border border-white/20">
                  <div className="text-5xl mb-4 transform group-hover:scale-110 transition-transform duration-300">
                    {stat.icon}
                  </div>
                  <div className="text-5xl font-bold mb-3 text-museo-gold">
                    {stat.number}
                  </div>
                  <div className="text-white/90 font-medium">
                    {stat.label}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Decorative circles */}
        <div className="absolute top-20 left-10 w-64 h-64 bg-museo-gold/10 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-museo-gold/5 rounded-full blur-3xl" />
      </section>

      {/* CÓMO FUNCIONA - Timeline visual */}
      <section className="py-24 bg-gradient-to-b from-white to-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-20">
            <span className="text-museo-gold font-semibold text-lg uppercase tracking-wider">Proceso Simple</span>
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mt-4 mb-6">
              ¿Cómo Funciona?
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Tu experiencia personalizada en 4 simples pasos
            </p>
          </div>

          <div className="max-w-6xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              {[
                { num: '01', icon: '🔐', title: 'Inicia Sesión', desc: 'Autentícate con Google' },
                { num: '02', icon: '✨', title: 'IA Analiza', desc: 'Generamos tu itinerario personalizado' },
                { num: '03', icon: '🚶', title: 'Explora', desc: 'Sigue tu recorrido único' },
                { num: '04', icon: '⭐', title: 'Comparte', desc: 'Valora tu experiencia' }
              ].map((step, index) => (
                <div key={index} className="relative">
                  {/* Connecting line */}
                  {index < 3 && (
                    <div className="hidden lg:block absolute top-16 left-1/2 w-full h-1 bg-gradient-to-r from-museo-gold to-transparent z-0" />
                  )}
                  
                  <div className="relative z-10 text-center">
                    {/* Number badge */}
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-museo-gold to-yellow-600 text-white text-2xl font-bold rounded-full shadow-xl mb-6">
                      {step.num}
                    </div>
                    
                    {/* Icon */}
                    <div className="text-6xl mb-4">{step.icon}</div>
                    
                    {/* Content */}
                    <h3 className="text-xl font-bold text-gray-900 mb-2">
                      {step.title}
                    </h3>
                    <p className="text-gray-600">
                      {step.desc}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA FINAL - Card destacado */}
      <section className="py-24 bg-gradient-to-br from-gray-50 to-white">
        <div className="container mx-auto px-4">
          <div className="max-w-5xl mx-auto">
            <div className="relative bg-gradient-to-br from-museo-brown via-museo-gold to-yellow-600 rounded-[3rem] shadow-2xl overflow-hidden">
              {/* Pattern overlay */}
              <div className="absolute inset-0 opacity-10">
                <div className="absolute inset-0" style={{
                  backgroundImage: `repeating-linear-gradient(45deg, transparent, transparent 35px, white 35px, white 70px)`
                }} />
              </div>

              <div className="relative z-10 px-8 py-16 md:px-16 md:py-20 text-center text-white">
                <div className="text-7xl mb-8">🌟</div>
                <h2 className="text-4xl md:text-5xl font-bold mb-6">
                  ¿Listo para tu Aventura Cultural?
                </h2>
                <p className="text-xl md:text-2xl mb-10 max-w-2xl mx-auto text-white/90">
                  Crea tu itinerario personalizado ahora y descubre las maravillas del Museo Pumapungo
                </p>
                
                {!user ? (
                  <button
                    onClick={handleGoogleLogin}
                    className="px-12 py-6 text-xl font-bold text-museo-brown bg-white rounded-full shadow-2xl hover:shadow-3xl transform hover:scale-105 transition-all duration-300 inline-flex items-center gap-3"
                  >
                    <span className="text-2xl">🚀</span>
                    Comenzar Ahora
                  </button>
                ) : (
                  <Link
                    to="/generar-itinerario"
                    className="inline-flex px-12 py-6 text-xl font-bold text-museo-brown bg-white rounded-full shadow-2xl hover:shadow-3xl transform hover:scale-105 transition-all duration-300 items-center gap-3"
                  >
                    <span className="text-2xl">🤖</span>
                    Generar Mi Itinerario
                  </Link>
                )}

                <div className="mt-10 flex flex-wrap justify-center items-center gap-6 text-white/90">
                  <span className="flex items-center gap-2">
                    <span className="text-2xl">✓</span>
                    Gratis y sin compromisos
                  </span>
                  <span className="flex items-center gap-2">
                    <span className="text-2xl">✓</span>
                    100% Personalizado
                  </span>
                  <span className="flex items-center gap-2">
                    <span className="text-2xl">✓</span>
                    Basado en IA
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;