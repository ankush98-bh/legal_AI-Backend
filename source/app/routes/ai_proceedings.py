from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from ..services import extract_text_from_file_path, is_likely_case_file, parse_conversation
from ..services.auth_service import authorize
from ..config import DEFAULT_MODEL, UPLOAD_FOLDER, OLLAMA_BASE_URL
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
import os
import aiofiles
from typing import Optional
from ..services import preprocess_text

router = APIRouter()

llm = OllamaLLM(base_url=OLLAMA_BASE_URL, model=DEFAULT_MODEL)

@router.post("/ai_proceedings")
# @authorize()
async def ai_proceedings(
    request: Request,
    file: UploadFile = File(...),
    model: Optional[str] = Form(DEFAULT_MODEL),
    court: Optional[str] = Form(None),
    current_user=None
):
    """
    Endpoint to handle AI proceedings.
    """
    try:
        """Endpoint to upload a case file."""
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(1024):
                await f.write(chunk)
        
        document_text = await extract_text_from_file_path(file_path)
        case_text = preprocess_text(document_text)
        if not is_likely_case_file(case_text):
            raise HTTPException(status_code=400, detail="The uploaded file does not appear to be a court case or judgment.")


        if court == "civil":
            prompt = PromptTemplate(
    input_variables=["case_text"],
    template=f"""You are simulating a **Civil Court Proceeding in India** such as a dispute over property, contract, or defamation as a story narrated by a narrator. Keep it in a very detailed and realistic manner.

Generate a detailed and realistic proceeding as a series of lines. Each line represents a part of the proceeding and must follow this format:
speaker||designation||speech

For example:
Narrator||Narrator||Welcome to the Court of the Civil Judge, Senior Division, Mumbai...
Judge||Judge||Hon'ble court is now in session...

Include the following elements in sequence:
1. Narrator introduces the court, date, and case.
2. Judge opens the court and introduces the case.
3. Plaintiff presents opening statement.
4. Defendant presents opening statement.
5. Plaintiff calls witnesses, who testify.
6. Defendant cross-examines witnesses.
7. Plaintiff makes closing argument.
8. Defendant makes closing argument.
9. Judge delivers the judgment.
10. Narrator concludes the story.

Ensure the flow is logical and the designations are appropriate (e.g., "Narrator", "Judge", "Plaintiff Attorney", "Defendant Attorney", "Witness").

**IMPORTANT:** Do not include any additional text, explanations, JSON, markdown, or extra formatting. Only generate the lines in the specified format, one per line.

Here's the case file to generate the response from:

\"\"\"{case_text}\"\"\"
""")
    
        elif court == "criminal":
            prompt = PromptTemplate(
    input_variables=["case_text"],
    template=f"""You are simulating a **Criminal Court Proceeding in India** under the Indian Penal Code. Keep it in a very detailed and realistic manner. The trial must include witness testimonies, direct and cross-examinations, and statements under CrPC.

Generate a structured courtroom narrative as a series of lines. Each line must follow this format:
speaker||designation||speech

For example:
Narrator||Narrator||Welcome to the Court of the Civil Judge, Senior Division, Mumbai...
Judge||Judge||This court is now in session...
Adv. Sharma||Prosecution||My Lord, the prosecution submits that...

Include:
- Narrator Introduces the court, date, and case.
- Judge opens the court and introduces the case.
- Prosecution led by Public Prosecutor (e.g., Adv. Sharma)
- Accused represented by defense counsel (e.g., Adv. Khan)
- IPC charges (derive from case text; e.g., 302, 376, 420, etc.)
- Use proper legal language (e.g., "My Lord", "The learned counsel...", "Statement under Section 313 CrPC")
- Include realistic Q&A interactions with all key witnesses
- Accused Statement (Section 313 CrPC)
- Closing Arguments of both sides
- Judge's final order or judgment
- Include legal citations and references to relevant sections of IPC, CrPC, and other laws
- Narrator Closes the Session
- Maintain formal, respectful court dialogue throughout
- Ensure the flow is logical and the designations are appropriate

**IMPORTANT:** Do not include any additional text, explanations, JSON, markdown, or extra formatting. Only generate the lines in the specified format, one per line.
            CASE DESCRIPTION:
            {case_text}""")
        else:
            prompt = PromptTemplate(
    input_variables=["case_text"],
    template= f"""You are a legal AI assistant with expert knowledge of Indian law and judicial proceedings.

Given the case file below, simulate a **realistic court proceeding in India**. You must determine the appropriate type of court based on the subject matter, legal sections involved, and nature of the dispute. Keep it in a very detailed manner.

### Court Types (Choose one based on the content):
1. Supreme Court - Constitutional and appellate matters  
2. High Courts - Civil/criminal appeals, writs, state-level jurisdiction  
3. District Courts - Local civil or criminal cases  
4. Subordinate Courts - Magistrate-level or small civil claims  
5. Special Courts - For specified laws (e.g., NDPS, POCSO, Economic Offenses)  
6. Tribunals - Subject-matter courts like NCLT, CAT, IPAB, etc.  
7. Lok Adalats - Alternative Dispute Resolution cases  

---

### Simulation Instructions:
- Begin with the correct **court name, case number (if available), and date**
- Introduce **both parties** and their **legal counsels**
- Present **opening statements**
- Detail **arguments and counterarguments** with **legal citations** from applicable laws (e.g., IPC, CrPC, Constitution, CPC, IT Act, etc.)
- Include **examination and cross-examination** of at least one witness if relevant
- End with a **judgment or court order** that includes legal reasoning

---

Generate a structured courtroom narrative as a series of lines. Each line must follow this format:
speaker||designation||speech

For example:
Narrator||Narrator||Welcome to the Court of the Civil Judge, Senior Division, Mumbai...
Judge||Judge||This court is now in session...
Adv. Sharma||Prosecution||My Lord, the prosecution submits that...

Include:
- Narrator Introduces the court, date, and case.
- Judge opens the court and introduces the case.
- Prosecution led by Public Prosecutor (e.g., Adv. Sharma)
- Accused represented by defense counsel (e.g., Adv. Khan)
- IPC charges (derive from case text; e.g., 302, 376, 420, etc.) if required
- Use proper legal language (e.g., "My Lord", "The learned counsel...", "Statement under Section 313 CrPC")
- Include realistic Q&A interactions with all key witnesses
- Accused Statement (Section 313 CrPC) if applicable
- Closing Arguments of both sides
- Judge's complete final order or judgment
- Include legal citations and references to relevant sections of IPC, CrPC, and other laws
- Narrator Closes the Session
- Maintain formal, respectful court dialogue throughout
- Ensure the flow is logical and the designations are appropriate

**IMPORTANT:** Do not include any additional text, explanations, JSON, markdown, or extra formatting. Only generate the lines in the specified format, one per line. Don't use any bullet points(not even numeric bullet points like, 1,2,3...) no I don't want that while generating the response especially in judgement. In judgment the format should be like this: Judge||Judge||The court finds that the evidence presented by the prosecution is compelling and establishes the guilt of the accused beyond a reasonable doubt. The accused is hereby sentenced to 10 years of rigorous imprisonment under Section 376 IPC. The fine of Rs. 50,000 is also imposed. The case is disposed of accordingly.

            CASE DESCRIPTION:
            {case_text}
            """)

        formatted_prompt = prompt.format(case_text=case_text)
        response = llm.invoke(formatted_prompt)
        try:
            conversation = parse_conversation(response)
            if not conversation:
                raise ValueError("No valid conversation entries parsed.")
            return {
                "conversation": conversation
            }
        except Exception as e:
            return {
                "error": "Failed to parse conversation response.",
                "raw_response": response,
                "details": str(e)
            }
    except Exception as e:
        return ({
            'error': str(e),
            'error_type': str(type(e).__name__),
            'error_file_details': f'Error on line {e.__traceback__.tb_lineno} inside {__file__}'
        })