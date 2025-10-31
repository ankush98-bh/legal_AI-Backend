from fastapi import HTTPException
import requests
from typing import Dict
from ..config import OLLAMA_BASE_URL

async def call_ollama_api(endpoint: str, method: str = "GET", json_data: Dict = None) -> Dict:
    """Make request to Ollama API using requests library"""
    url = f"{OLLAMA_BASE_URL}/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=60.0)
        elif method == "POST":
            response = requests.post(url, json=json_data, timeout=600.0)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as exc:
        raise HTTPException(status_code=503, detail=f"Error communicating with Ollama: {str(exc)}")
    except requests.exceptions.HTTPError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=f"Ollama API error: {exc.response.text}")