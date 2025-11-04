from fastapi import UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
import PyPDF2
import io

def extract_text_from_file(file: UploadFile) -> str:
    
    file_content = file.file.read()
    content = ""
    if file.filename.endswith('.pdf'):
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            content += page.extract_text() + "\n"
    elif file.filename.endswith(('.txt', '.md', '.html')):
        try:
            content = file_content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not decode the text file. Please check encoding.")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file format. Please upload a PDF, TXT, MD, or HTML file.")
    return content

async def extract_text_from_file_path(file_path: str) -> str:
    """Extracts text from a file given its path."""
    content = ""
    try:
        with open(file_path, 'rb') as f:
            if file_path.endswith('.pdf'):
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    content += page.extract_text() + "\n"
            elif file_path.endswith(('.txt', '.md', '.html')):
                content = f.read().decode("utf-8", errors='ignore') # Handle potential decoding issues
            else:
                print(f"Unsupported file format: {file_path}")
        return content
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File not found: {file_path}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error extracting text from {file_path}: {e}")