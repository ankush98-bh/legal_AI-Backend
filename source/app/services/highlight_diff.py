import fitz
import io
from fastapi import HTTPException, status

def highlight_differences(pdf_data: bytes, diff_text: dict):
    if not pdf_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PDF data is empty, cannot process.")
    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error processing PDF: {e}")
    
    try:
        for page in doc:
            text = page.get_text("text")
        
            # Highlight added text in **red**
            for line in diff_text.get("added", []):
                try:
                    search_term = line.strip()
                    if search_term:
                        instances = page.search_for(search_term)
                        for inst in instances:
                            highlight = page.add_highlight_annot(inst)
                            highlight.set_colors(stroke=(1, 0, 0))  # Red
                            highlight.update()
                
                except AttributeError:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"'added' line is not a string: {line}")
                    continue  # Skip to the next line
        
            # Redact removed text (completely remove)
            for line in diff_text.get("removed", []):
                try:
                    search_term = line.strip()
                    if search_term and search_term in text:
                        for inst in page.search_for(search_term):
                            page.add_redact_annot(inst, fill=(1, 0, 0))  # Redaction color set to RED
                            page.apply_redactions()  # Apply the redaction
                except AttributeError:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"'removed' line is not a string: {line}")
                    continue  # Skip to the next line
            
            # ✏️ **Highlight Modified Text (Changed Words)**
            for change in diff_text.get("changed_lines", []):
                try:
                    modified_info = change.get("modified")
                    if isinstance(modified_info, dict):
                        modified_text = modified_info.get("content", "").strip()
                    elif isinstance(modified_info, str):
                        modified_text = modified_info.strip()
                    else:
                        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"'modified' in changed_lines is not a string or dict: {modified_info}")
                        continue  # Skip to the next change

                    if modified_text:
                        instances = page.search_for(modified_text)
                        for inst in instances:
                            highlight = page.add_highlight_annot(inst)
                            highlight.set_colors(stroke=(1, 0, 0))  # Red
                            highlight.update()
                except AttributeError as e:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"'modified' in changed_lines has issues: {change} - {e}")
                    continue  # Skip to the next change 
        
        # Save the PDF to an in-memory stream instead of a file
        output_stream = io.BytesIO()
        doc.save(output_stream)
        pdf_bytes = output_stream.getvalue()
        doc.close()
        
        return pdf_bytes
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error during highlighting/redaction: {e}")