from fastapi import APIRouter
import requests
from config import get_settings

router = APIRouter()

settings = get_settings()

OLLAMA_URL = f"{settings.OLLAMA_BASE_URL}/api/generate"
MODEL = settings.OLLAMA_MODEL

@router.post("/chat")
def chat(prompt: str):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
    except Exception as e:
        return {"error": f"Error al conectar con Ollama: {e}"}

    if response.status_code != 200:
        return {
            "error": "Error comunicándose con Ollama",
            "detalle": response.text
        }

    return {"respuesta": response.json().get("response")}
