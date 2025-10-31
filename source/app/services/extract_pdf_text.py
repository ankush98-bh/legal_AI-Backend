from fastapi import UploadFile, HTTPException
import pdfplumber
import io

def extract_text_from_pdf(file: UploadFile) -> str:
    try:
        content = ""
        pdf_stream = io.BytesIO(file.file.read())
        with pdfplumber.open(pdf_stream) as pdf:
            content = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        return content,pdf_stream
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")