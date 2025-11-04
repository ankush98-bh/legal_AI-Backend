from fastapi import HTTPException, UploadFile, Form
from ..services.call_ollama import call_ollama_api
from ..services.extract_text import extract_text_from_file
from ..config import DEFAULT_MODEL
from typing import Optional

async def customised_prompt(file: UploadFile, model: Optional[str] = Form(DEFAULT_MODEL)) -> str:
    """Generate Prompts from custom documents uploaded."""
    try:
        content = ""
        content = extract_text_from_file(file)
        prompt = f"""Please refer the following recommended prompt technique to generate a a prompt first, this newly generated prompt is then to be used to generate the legal document.
 
The Recommended Prompting Technique: The Enhanced KOF Framework with Role Assignment and Few-Shot Guidance
This technique builds upon the KOF (Context - Objective - Format) framework and integrates the power of Role Assignment and Few-Shot Prompting. For more intricate documents or clauses, incorporating elements of Chain-of-Thought Prompting can further enhance the output.   
Here's how to apply this enhanced framework:
1.	Context (Setting the Scene):   
          Clearly define the legal domain: Specify the area of law relevant to the document (e.g., property law, contract law, etc.).
          State the jurisdiction: Explicitly mention the governing jurisdiction (e.g., Maharashtra, India) as legal requirements vary significantly.   
          Identify the parties involved: Specify the roles and names (or types) of the parties (e.g., Buyer, Seller, Landlord, Tenant).
          Provide relevant background information: Include any crucial details about the transaction, dispute, or regulatory context. For example, for a Sale Deed, mention the type of property, its location, and the purpose of the document.   
2.	Objective (Defining the Task):   
          Clearly state the desired action: Use explicit verbs like "Draft," "Generate," "Outline," "Review," or "Create".   
          Specify the exact type of document: Be precise about the document name (e.g., "Sale Deed," "Commercial Lease Agreement," "RERA Registration Document").   
          Highlight the key purpose of the document: Briefly mention the legal goal the document aims to achieve (e.g., "for the legal transfer of ownership," "to define the terms of a rental agreement").
3.	Format (Specifying the Output Structure):   
          Define the desired structure: Specify the format you need (e.g., "using standard legal clauses," "in a numbered list," "with clear headings and subheadings," "including signature blocks"). You can even reference standard legal document structures like those found in law office memorandums.   
          Mention specific clauses or sections: If you need particular clauses (like "indemnity clause," "dispute resolution clause," "payment terms"), explicitly list them.   
          Specify any length constraints: If there's a desired word count or page limit, include that in your prompt.   
4.	Role Assignment (Adding Expertise):   
          Instruct the LLM to act as a specific legal professional: Assign a role relevant to the document (e.g., "Act as a seasoned property lawyer in Maharashtra," "You are an expert in drafting commercial lease agreements," "Assume the role of a legal consultant specializing in RERA regulations"). This helps the AI adopt the appropriate tone, terminology, and level of expertise.    
Your output should be in a formal legal language, using precise legal terminology and adhering to a structured, clause-by-clause format. Ensure clarity, thoroughness, and adherence to best legal practices.'''
 
Here is the content of the document for your analysis before creating a prompt: {content}"""
    
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

        response = await call_ollama_api("api/generate", method="POST", json_data=payload)
        raw_response = response.get("response", "")
        return raw_response

    except HTTPException as http_exc:
        raise http_exc #re raise the HTTPException
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")