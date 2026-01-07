const Footer = () => {
  return (
    <footer className="bg-gray-900 text-white mt-auto">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Info del museo */}
          <div>
            <h3 className="text-lg font-bold mb-4">Museo Pumapungo</h3>
            <p className="text-gray-400 text-sm">
              Sistema de Registro y Perfilado de Visitantes con Generación Automática 
              de Itinerarios Personalizados mediante IA Generativa
            </p>
          </div>

          {/* Universidad */}
          <div>
            <h3 className="text-lg font-bold mb-4">Universidad</h3>
            <p className="text-gray-400 text-sm">
              Universidad Politécnica Salesiana<br />
              Cuenca - Ecuador<br />
              Trabajo de Titulación 2025
            </p>
          </div>

          {/* Desarrolladores */}
          <div>
            <h3 className="text-lg font-bold mb-4">Desarrollado por</h3>
            <p className="text-gray-400 text-sm">
              Tania Lojano<br />
              Noé Leandro Ayavaca Guarango<br />
              Tutor: PhD. Gustavo Omar Bravo Quezada
            </p>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-6 text-center text-gray-400 text-sm">
          <p>&copy; 2025 Sistema Museo Pumapungo. Todos los derechos reservados.</p>
          <p className="mt-2">Potenciado por IA Generativa (DeepSeek-R1:7b)</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;