# services/interest_analyzer_service.py
# Analizador de intereses basado en datos sociales
# Sistema Museo Pumapungo

import logging

logger = logging.getLogger(__name__)

class InterestAnalyzerService:

    async def analizar_perfil_completo(
        self,
        facebook_data: dict,
        instagram_data: dict,
        nombre_visitante: str
    ) -> dict:
        """
        Analiza intereses a partir de datos sociales simulados
        """

        intereses = []

        # Extraer intereses desde "pages_liked"
        for page in facebook_data.get("pages_liked", []):
            nombre = page["name"].lower()

            if "historia" in nombre:
                intereses.append("historia")
            elif "arte" in nombre:
                intereses.append("arte")
            elif "naturaleza" in nombre:
                intereses.append("naturaleza")
            else:
                intereses.append("cultura")

        # Valores por defecto si no se detecta nada
        if not intereses:
            intereses = ["cultura", "historia"]

        logger.info(f"🤖 Intereses detectados para {nombre_visitante}: {intereses}")

        return {
            "intereses": list(set(intereses)),
            "confianza": 75,
            "nivel_detalle_sugerido": "normal",
            "tiempo_sugerido": 420,
            "explicacion": "Intereses inferidos a partir de actividad social y canales seguidos."
        }


# Instancia global
interest_analyzer = InterestAnalyzerService()
