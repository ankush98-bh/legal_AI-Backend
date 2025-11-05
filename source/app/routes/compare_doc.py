from fastapi import APIRouter, UploadFile, File, Form, Response, Request
#from ..services.auth_service import authorize
from typing import Optional
from ..services import call_ollama_api, extract_text_from_file, format_response
from ..config import DEFAULT_MODEL

router = APIRouter()

@router.post("/compare_documents")
#@authorize()
async def compare_documents(
    request: Request,
    file1: UploadFile = File(...),
    model: Optional[str] = Form(DEFAULT_MODEL),
    file2: UploadFile = File(...),
    current_user=None
):
    """Compares two real estate legal documents and returns a structured comparison."""
    try:
        content1 = extract_text_from_file(file1)
        content2 = extract_text_from_file(file2)

        prompt = f""" You are a legal expert specializing in real estate laws across India. Your task is to analyze and compare two uploaded legal documents, considering key legal, financial, and regulatory aspects. The documents may include sale deeds, lease agreements, gift deeds, mortgage deeds, rental agreements, power of attorney, partition deeds, or other real estate-related contracts.

Comparison Parameters:

Document Type & Purpose: Identify the category of each document and explain its primary function (e.g., sale deed for ownership transfer vs. lease agreement for temporary possession).
Parties Involved: Compare the roles and obligations of the parties (e.g., buyer vs. seller, lessor vs. lessee).
Rights Transferred: Analyze what rights are conveyed (e.g., full ownership in a sale deed vs. limited possession in a lease).
Financial Considerations: Examine payment structures (e.g., lump sum in sales vs. recurring rent in leases).
Duration & Validity: Determine the timeframe each document is valid for (e.g., permanent in a sale deed vs. fixed term in a lease).
Legal Requirements & Compliance: Check compliance with Indian laws such as the Registration Act, 1908, RERA, and stamp duty variations across states.
State-Specific Variations: Highlight jurisdictional differences (e.g., stamp duty in Maharashtra vs. Tamil Nadu, land ceiling laws, registration requirements).
Tax Implications: Identify relevant taxes like capital gains tax, property tax, and rental income tax.
Dispute Resolution & Termination Clauses: Compare the legal recourse available (e.g., arbitration vs. court proceedings, termination conditions).
Task:

Extract key terms, obligations, and legal clauses from both documents.
Compare and highlight similarities and differences using the above parameters.
Provide a structured comparison, ensuring clarity for legal professionals and stakeholders.
Summarize major risks, missing clauses, or potential legal issues.
Output Format:

Document 1 (Type: X) vs. Document 2 (Type: Y)
Key Similarities & Differences
Legal & Compliance Issues Noted
State-Specific Considerations
Summary of Risks & Recommendations
Provide a detailed analysis of the comparison, highlighting any significant differences, gaps, or risks. Ensure your analysis is thorough and considers the complexities of the Indian legal landscape.
        Document 1: {content1}
        Document 2: {content2}"""

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    
        response = await call_ollama_api("api/generate", method="POST", json_data=payload)
        raw_response = response.get("response", "")
        formatted_response = format_response(raw_response)

        return Response(content=formatted_response, media_type="text/html")
    
    except Exception as e:
        return ({
            'error': str(e),
            'error_type': str(type(e).__name__),
            'error_file_details': f'error on line {e.__traceback__.tb_lineno} inside {__file__}'
        })