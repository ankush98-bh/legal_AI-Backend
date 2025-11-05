from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response, Request
from ..services.auth_service import authorize
from typing import Optional
import json
from ..services.format_res import format_response
from ..services.call_ollama import call_ollama_api
from ..services.custom_prompt import customised_prompt
from ..config import DEFAULT_MODEL

router = APIRouter()

@router.post("/generate_custom_draft")
#@authorize()
async def generate_document_format(
    request: Request,
    sample_file: Optional[UploadFile] = File(None),
    document_type: Optional[str] = Form(None),
    input_text: Optional[str] = Form(None),
    options: Optional[str] = Form(None),
    model: Optional[str] = Form(DEFAULT_MODEL),
    current_user = None
):
    """
    Generates a formatted draft for a given document type. Optionally uses a sample document,
    structured key-value pairs (options), and free-text user instructions.
    """
    try:
        sample_text = ""
        if sample_file:
            sample_text = customised_prompt(sample_file)
        options_dict = json.loads(options) if options else {}
        prompt = ''
        # Base prompt structure
        if document_type:
            prompt = f"Generate a professional {document_type} document.\n"

        if sample_text:
            prompt += f"\nUse the following document as a structural reference:\n{sample_text}\n"

        if options_dict:
            prompt += "\nEnsure the following key-value details are included in the document:\n"
            for key, value in options_dict.items():
                prompt += f"- {key}: {value}\n"

        if input_text:
            prompt += f"\nAdditional User Instructions:\n{input_text}\n"

        # Payload for model generation
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

        response = await call_ollama_api("api/generate", method="POST", json_data=payload)
        raw_response = response.get("response", "")
        formatted_response = format_response(raw_response)

        return Response(content=formatted_response, media_type="text/html")

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid options format. Please provide a valid JSON.")
    except Exception as e:
        return ({
            'error': str(e),
            'error_type': str(type(e).__name__),
            'error_file_details': f'error on line {e.__traceback__.tb_lineno} inside {__file__}'
        })