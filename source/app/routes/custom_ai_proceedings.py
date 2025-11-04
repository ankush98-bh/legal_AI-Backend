from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
#rom ..services.auth_service import authorize
from typing import Optional
from ..services import extract_text_from_file_path, is_likely_case_file, parse_conversation, preprocess_text, get_court_proceedings_conversation_chain, court_proceedings_conversation_chain, extract_conversational_lines_from_chat_history
from ..config import UPLOAD_FOLDER
import aiofiles
import os
import uuid

router = APIRouter()

async def get_sesh_id(session_id: Optional[str] = Form(None)):
    """Dependency to get or create a session ID."""
    if session_id:
        return session_id
    else:
        return str(uuid.uuid4())

@router.post("/start_custom_ai_proceedings")
async def start_custom_ai_proceedings(
    request: Request,
    file: UploadFile = File(...),
    user_role: str = Form(...),
    court: str = Form(...),
    session_id: str = Depends(get_sesh_id),
    current_user=None
):
    """
    Endpoint to handle AI proceedings.
    """
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
            case_text = preprocess_text(document_text)

        if not is_likely_case_file(case_text):
            raise HTTPException(status_code=400, detail="The uploaded file does not appear to be a court case or judgment.")
        
        # Create conversation chain with case file
        conversation_chain = court_proceedings_conversation_chain(session_id, case_text)

        # Generate initial judge statement
        initial_prompt = (
            f"You are in the {court} court. The case is about: {case_text}. "
            f"The user is playing the role of {user_role}. "
            "Begin the court proceedings with the judge's opening statement. "
            '''Generate a detailed and realistic proceeding as a series of lines. Each line represents a part of the proceeding and must follow this format:
            speaker||role||speech

            Note: Do not use this statement just generate the statement and leave it user himself knows what he has to do(Please let me know if you would like me to continue generating the proceeding!)

            For example:
            Judge||Judge||Hon'ble court is now in session....
            Ensure the flow is logical and the designations are appropriate (e.g., "Narrator", "Judge", "Plaintiff Attorney", "Defendant Attorney", "Witness").

            **IMPORTANT:** Do not include any additional text, explanations, JSON, markdown, or extra formatting.
                            Only generate the lines in the specified format, one per line.'''
            )
        result = await conversation_chain.ainvoke({"question": initial_prompt})
        parsed_conversation = parse_conversation(result['answer'].strip())
        
        return {
            "session_id": session_id,
            "result": result['answer'],
            "conversation": parsed_conversation
        }
    
    except Exception as e:
        return ({
            'error': str(e),
            'error_type': str(type(e).__name__),
            'error_file_details': f'Error on line {e.__traceback__.tb_lineno} inside {__file__}'
        })
    
@router.post("/start_custom_ai_proceedings/input_custom_ai_proceedings")
async def input_custom_ai_proceedings(
    user_role: str = Form(...),
    message: str = Form(...),
    session_id: str = Form(...)
):
    conversation = get_court_proceedings_conversation_chain(session_id)

    if not conversation:
        raise HTTPException(status_code=400, detail="Session ID not found or expired. Please start a new session.")
    try:
        # Construct prompt for realistic courtroom response
        prompt = (
            f"User's latest input: {message}\n"
            "Continue the courtroom proceedings in a realistic manner based on Indian law. "
            "Multiple participants (judge, lawyers, witnesses) may respond after the user's input. "
            f"Generate the next sequence of statements until it's {user_role}'s turn to speak again. "
            f"It is possible that it is not provided in the document think on your own and generate the statement for further proceedings. Think as if you are the one who on behalf of everyone is speaking except the {user_role}. "
            "Each statement must be formatted as 'Speaker||Designation||Speech', one per line. "
            "For example:\n"
            "Judge||Judge||The court acknowledges the prosecution's submission.\n"
            "Defense Attorney||Defense Attorney||My Lord, we request clarification on the evidence.\n"
            # "Ensure the flow is logical and designations are appropriate (e.g., 'Judge', 'Public Prosecutor', 'Defense Attorney', 'Witness'). "
            # "**Strictly follow this format. Do not include any additional text, explanations, or commentary outside the specified format.**"
        )
        result = await conversation.ainvoke({"question": prompt})
        parsed_conversation = extract_conversational_lines_from_chat_history(result['chat_history'])

        return {"result": result,
                "parsed_conversation": parsed_conversation
                }
    
    except Exception as e:
        return ({
            'error': str(e),
            'error_type': str(type(e).__name__),
            'error_file_details': f'Error on line {e.__traceback__.tb_lineno} inside {__file__}'
        })
    
@router.post("/conclude_custom_ai_proceedings")
async def conclude_custom_ai_proceedings(session_id: str = Form(...)):
    conversation = get_court_proceedings_conversation_chain(session_id)

    if not conversation:
        raise HTTPException(status_code=400, detail="Session ID not found or expired. Please start a new session.")
    try:
        # Construct prompt for realistic courtroom response
        prompt = (
            "Conclude the courtroom proceedings in a realistic manner based on Indian law. "
            "Generate the final statements and conclusions of the court. "
            "Each statement must be formatted as 'Speaker||Designation||Speech', one per line. "
            "For example:\n"
            "Judge||Judge||The court will now adjourn until further notice.\n"
            "Defense Attorney||Defense Attorney||Thank you, Your Honor.\n"
            # "**Strictly follow this format. Do not include any additional text, explanations, or commentary outside the specified format.**"
        )
        result = await conversation.ainvoke({"question": prompt})
        parsed_conversation = extract_conversational_lines_from_chat_history(result['chat_history'])

        return {"result": result,
                "parsed_conversation": parsed_conversation
                }
    
    except Exception as e:
        return ({
            'error': str(e),
            'error_type': str(type(e).__name__),
            'error_file_details': f'Error on line {e.__traceback__.tb_lineno} inside {__file__}'
        })