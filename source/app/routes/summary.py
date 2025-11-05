from fastapi import APIRouter, Response, UploadFile, File, Form, Query, Request
#from ..services.auth_service import authorize
from fastapi.responses import JSONResponse
import json
from typing import Optional, Any
from ..services.call_ollama import call_ollama_api
from ..services.format_res import format_response
from ..services.extract_text import extract_text_from_file
from ..config import DEFAULT_MODEL

router = APIRouter()

@router.post("/summarize_file")
#@authorize()
async def summarize_file(
    request: Request,
    file: UploadFile = File(...),
    model: Optional[str] = Form(DEFAULT_MODEL),
    options: Optional[str] = Form(None),
    analysis_type: str = Form(enum=["summary", "intent", "legal_analysis"]),
    current_user=None
):
    try:
        content = extract_text_from_file(file)
        # Convert options string to dict if provided
        options_dict = json.loads(options) if options else {}
        
        if analysis_type == "summary":
            prompt = f"""You are a legal document specialist. I'm sending you a document for analysis.
            Please provide a comprehensive summary of the document, including:
            1. Document type and purpose
            2. Key parties involved
            3. Main terms and conditions
            4. Important dates or deadlines
            5. Any notable clauses or provisions
            6. Any potential legal issues or concerns
            Here's the document content:
            {content}
            """
        elif analysis_type == "intent":
            prompt = f"""Analyze the provided legal document to determine its type based on content and intent.

Document Text:

[Text of the uploaded document. (Is it feasible?)]

Analysis Instructions:

Focus on keywords such as "sale," "partition," "lease," or other terms that indicate the document's purpose.

Consider the structure and clauses typical of each document type, e.g., sale deeds often include transfer of ownership details.

Output Format:

Provide the document type in a JSON format as shown.

Example Response:

{{
  "document_type": "Sale deed"
}}

Example Use Case:

For a document detailing the transfer of property ownership, the output would be "Sale deed." For a document dividing property among heirs, it would be "Partition deed."

Note:

If the full text is too lengthy, include a concise summary that preserves key terms and context to aid accurate classification. The file content is: 
            {content}
            """
        elif analysis_type == "legal_analysis":
            prompt = f"""You are an expert legal analyst specializing in Indian law, providing detailed legal analysis for lawyers. Analyze the given legal document using a structured reasoning approach (IRAC/FIRAC) based on its nature. Your response should include:
 
Key Legal Element Extraction : Identify and explicitly outline the core legal elements in the document.
Legal Reasoning : Apply expert-level legal reasoning, citing relevant case precedents, statutory provisions, and applicable legal principles.
Conclusion & Implications : Provide a well-reasoned conclusion along with a separate section detailing the potential legal implications.
Issue Flagging : Detect and flag any missing, inconsistent, or ambiguous information that may affect legal interpretation.
Strategic Legal Insights : Offer possible legal strategies, arguments, or risk assessments based on the document’s content.

Ensure clarity, precision, and strict adherence to Indian legal principles while maintaining a professional and structured format suitable for legal practitioners. 
 
Find below the text of the uploaded document:
            {content}
            """
        
        # Send to model and process response
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        if options_dict:
            payload["options"] = options_dict
            
        response = await call_ollama_api("api/generate", method="POST", json_data=payload)
        raw_response = response.get("response", "")
        formatted_response = format_response(raw_response)
        
        return Response(content=formatted_response, media_type="text/html")
        
    except json.JSONDecodeError:
        return JSONResponse(
            content={"error": "Invalid options format. Please provide a valid JSON."},
            status_code=400
        )
    except Exception as e:
        return ({
            'error': str(e),
            'error_type': str(type(e).__name__),
            'error_file_details': f'error on line {e.__traceback__.tb_lineno} inside {__file__}'
        })