from fastapi import APIRouter, Response, Request
#from ..services.auth_service import authorize
from ..services.format_res import format_response
from ..services.call_ollama import call_ollama_api
from ..services.prompt_gen import generate_prompt
from ..models.request_models import QueryRequest
from ..config import DEFAULT_MODEL

router = APIRouter()

@router.post("/query")
#@authorize()
async def query(request: Request, query: QueryRequest, current_user=None):
    try:
        
        prompt = generate_prompt(query.domain, query.sub_domain, query.options)

        payload = {
            "model": DEFAULT_MODEL,
            "prompt": prompt,
            "stream": False
        }
        
        if query.options:
            payload["options"] = query.options
            
        response = await call_ollama_api("api/generate", method="POST", json_data=payload)
        raw_response = response.get("response", "")
        
        # Format the response if requested
        if query.format_output:
            formatted_response = format_response(raw_response)
        else:
            formatted_response = raw_response
        
        return Response(content=formatted_response, media_type="text/html")
        
    except Exception as e:
        return ({
            'error': str(e),
            'error_type': str(type(e).__name__),
            'error_file_details': f'error on line {e.__traceback__.tb_lineno} inside {__file__}'
        })
