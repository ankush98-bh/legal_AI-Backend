import os
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Request
#rom ..services.auth_service import authorize
from fastapi.responses import JSONResponse
from ..services import extract_text_from_file_path, call_ollama_api
from ..config import DEFAULT_MODEL, UPLOAD_FOLDER

router = APIRouter()

@router.post("/cross_exam")
#authorize()
async def cross_exam(
    request: Request,
    file: UploadFile = File(...),
    interviewer: str = Form(...),
    interviewee: str = Form(...),
    current_user=None
):
    """Endpoint to get FAQs for the uploaded file."""
    try:
        file_path = None
        document_text = None

        # If a file is uploaded, extract its text
        if file:
            if not file.filename.endswith(".pdf"):
                raise HTTPException(status_code=400, detail="Only PDF files are supported")
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            async with aiofiles.open(file_path, "wb") as f:
                while chunk := await file.read(1024):
                    await f.write(chunk)
            document_text = await extract_text_from_file_path(file_path)
            if not document_text:
                raise HTTPException(status_code=400, detail="Failed to extract text from the uploaded file.")
            prompt = f"""You are a legal expert specialized in Indian law. Based on the provided document, imagine a cross-examination scenario where the interviewer is "{interviewer}" and the interviewee is "{interviewee}". Generate a list of potential cross-examination questions that "{interviewer}" could ask "{interviewee}" based on the content of the document. The questions should be relevant, specific to the document, and suitable for a legal cross-examination context.
            Note: Do not answer the questions just formulate the questions pertaining to the document. Just list the questions without any additional text or formatting.
            The document content is: {document_text}"""
        
        # Send to model and process response
        payload = {
            "model": DEFAULT_MODEL,
            "prompt": prompt,
            "stream": False
        }
        
        response = await call_ollama_api("api/generate", method="POST", json_data=payload)
        raw_response = response.get("response", "")
        cross_questions = [q.strip("- ").strip() for q in raw_response.split("\n") if q.strip()]
        if cross_questions and cross_questions[0].lower().startswith("here are"):
            cross_questions = cross_questions[1:]
        return JSONResponse(content={"questions": cross_questions})
    
    except Exception as e:
        return ({
            'error': str(e),
            'error_type': str(type(e).__name__),
            'error_file_details': f'Error on line {e.__traceback__.tb_lineno} inside {__file__}'
        })