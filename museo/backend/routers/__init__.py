# routers/__init__.py
# Exportar todos los routers

from . import visitantes, perfiles, areas, itinerarios, itinerario_detalles, historial, ia, auth_google

__all__ = ["visitantes", "perfiles", "areas", "itinerarios", "itinerario_detalles", "historial", "ia", "auth_google"]