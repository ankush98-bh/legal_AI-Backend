from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
#from ..services.auth_service import authorize
from fastapi.responses import JSONResponse
from typing import Optional, List, Union
import aiofiles
from ..services import extract_text_from_file_path, get_or_create_conversation_chain, clear_session_history, get_session_conversation_chain, get_general_conversation_chain, update_general_chat_history, call_ollama_api
from ..config import DEFAULT_MODEL, UPLOAD_FOLDER
from ..constants.prompts import PROMPTS
import os
import uuid

router = APIRouter()

async def get_sesh_id(session_id: Optional[str] = Form(None)):
    """Dependency to get or create a session ID."""
    if session_id:
        return session_id
    else:
        return str(uuid.uuid4())

async def compress_text_via_prompt(text: str) -> str:
    # Modify this function to use your actual LLM client
    prompt = f"""
    Minimize the following combined legal documents without changing their meaning or removing critical context.
    Note: Don't add anything extra like I don't want to know what you did just the output only, and I do appreciate what you did but that's not what I want as an output, I just want the compressed text only. Don't write "Here is the minimized combined legal document".
    Documents:
    {text}
    """
    # Send to model and process response
    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt,
        "stream": False
    }
        
    response = await call_ollama_api("api/generate", method="POST", json_data=payload)
    # print(f"Response: {response['response']}")
    return response['response']


async def process_uploaded_files(files: List[UploadFile]) -> str:
    texts = []

    # Save and extract text from each file
    for file in files:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(1024):
                await f.write(chunk)

        text = await extract_text_from_file_path(file_path)
        texts.append((file.filename, text))

    # If more than 1 file, compress in pairs
    if len(texts) > 1:
        compressed_chunks = []
        i = 0
        while i < len(texts):
            chunk = texts[i:i+2]  # Handle 1 or 2 files at a time
            combined_text = "\n\n".join(f"--- {file.filename} ---\n{text}" for file.filename, text in chunk)
            compressed = await compress_text_via_prompt(combined_text)
            compressed_chunks.append(compressed)
            i += 2
        return "\n\n".join(compressed_chunks)

    else:
        # Single file — no compression
        return texts[0][1]

@router.post("/legal_bot")
#@authorize()
async def legal_bot(
    request: Request,
    question: str = Form(...),
    preset_prompt: Optional[str] = Form(None),
    interviewee: Optional[str] = Form(None),
    interviewer: Optional[str] = Form(None),
    file: Optional[Union[UploadFile, List[UploadFile]]] = File(None),
    with_file: Optional[bool] = Form(None),
    session_id: str = Depends(get_sesh_id),
    current_user=None
):
    try:
        combined_text = None

        # If a file is uploaded, extract its text
        if file:
            files = [file] if isinstance(file, UploadFile) else file
            combined_text = await process_uploaded_files(files)
        
        if preset_prompt:
            selected_prompt = PROMPTS.get("Analysis_Prompts", {}).get(preset_prompt)

            if not selected_prompt:
                raise HTTPException(status_code=400, detail=f"Invalid preset prompt: {preset_prompt}")

            # For cross-exam prompt (requires interviewer and interviewee)
            if preset_prompt == "cross_exam_prompts":
                if not interviewer or not interviewee:
                    raise HTTPException(status_code=400, detail="Interviewer and interviewee are required for cross-examination prompt.")
                question = selected_prompt.format(
                    interviewer=interviewer,
                    interviewee=interviewee,
                    content=combined_text)
            else:
                # For all other prompts
                if '{content}' in selected_prompt and not combined_text:
                    raise HTTPException(status_code=400, detail="Document content required for preset prompt.")
                question = selected_prompt.format(content=combined_text)
        if with_file:
            if combined_text:
                conversation = get_or_create_conversation_chain(session_id, combined_text)
                if conversation:
                    print("\n====== Sending Query to LLM (Document Mode) ======")
                    print("User Question:", question)

                    response = await conversation.ainvoke({'question': question})

                    print("\n====== RAW MODEL RESPONSE (Document Mode) ======")
                    print(response)

                    return {"answer": response['answer'], "session_id": session_id}
                else:
                    raise HTTPException(status_code=500, detail="Failed to initialize conversation chain.")
            else:
                existing_conversation = get_session_conversation_chain(session_id)
                if existing_conversation:
                    print("\n====== Sending Query to LLM (Existing Doc Session) ======")
                    print("User Question:", question)

                    response = await existing_conversation.ainvoke({'question': question})

                    print("\n====== RAW MODEL RESPONSE (Existing Doc Session) ======")
                    print(response)

                    return {"answer": response['answer'], "session_id": session_id}
                else:
                    raise HTTPException(status_code=400, detail="Please upload a PDF file first to ask questions about it.")
        else:
            general_conversation = get_general_conversation_chain(session_id)

            # print("\n====== Sending Query to LLM (General Mode) ======")
            # print("User Question:", question)

            # print("\n✅ MODEL STREAMING STARTED...")

            # final_answer = ""

            # #🔥 STREAM RESPONSE FROM MODEL
            # stream = await general_conversation.ainvoke_stream({'question': question})

            # async for chunk in stream:
            #     token = chunk.get("content") or chunk.get("output") or ""
            #     print(token, end="", flush=True)
            #     final_answer += token

            # print("\n✅ MODEL STREAM COMPLETE ✅")
            # print("\n====== FINAL CLEAN RESPONSE ======")
            # print(final_answer)

            # update_general_chat_history(session_id, general_conversation.memory)

            # return {"answer": final_answer, "session_id": session_id}

        # if with_file:
        #     if combined_text:
        #         conversation = get_or_create_conversation_chain(session_id, combined_text)
        #         if conversation:
        #             response = await conversation.ainvoke({'question': question})
        #             return {"answer": response['answer'], "session_id": session_id}
        #         else:
        #             raise HTTPException(status_code=500, detail="Failed to initialize conversation chain.")
        #     # else:
        #     #     raise HTTPException(status_code=400, detail="Upload the pdf file first!!")
        #     else:
        #         # Check if a vector store exists for this session
        #         existing_conversation = get_session_conversation_chain(session_id)
        #         print("Session Data:", existing_conversation)
        #         if existing_conversation:
        #             response = await existing_conversation.ainvoke({'question': question})
        #             return {"answer": response['answer'], "session_id": session_id}
        #         else:
        #             raise HTTPException(status_code=400, detail="Please upload a PDF file first to ask questions about it.")
            #general_conversation = get_general_conversation_chain(session_id)
            # response = await general_conversation.ainvoke({'input':question})
            # if response:
            #     print(response)
            # else:
            #     print('Response is not generated')
            # update_general_chat_history(session_id, general_conversation.memory) # Update history
            # return {"answer": response['answer'], "session_id": session_id}
            print('response is generating...')
            response = await general_conversation.ainvoke({'input': question})
            print("\n✅ MODEL RAW RESPONSE ✅", flush=True)
            print(response)

            if not response:
                return {"answer": "Sorry, I could not generate a response.", "session_id": session_id}

            # ✅ Only take the actual text content
            final_answer = response.get("response") or response.get("answer") or response.get("output") or str(response)

            update_general_chat_history(session_id, general_conversation.memory)

            return {"answer": final_answer.strip(), "session_id": session_id}

    except Exception as e:
        print(e)
        return {
            'error': str(e),
            'error_type': str(type(e).__name__),
            'error_file_details': f'Error on line {e.__traceback__.tb_lineno} inside {__file__}',
            'session_id': session_id
        }
    
@router.delete("/legal_bot/clear_history")
async def clear_history(session_id: str = Form(...), with_file: bool = Form(False)):
    """Clears the chat history for a given session, optionally for general or document-related chats."""
    clear_session_history(session_id, with_file)
    return {"message": f"Chat history cleared for session: {session_id}, with file: {with_file}"}

@router.get("/legal_bot/get_session_id")
async def get_session_id():
    """Endpoint to get a new session ID."""
    return {"session_id": str(uuid.uuid4())}

@router.post("/legal_bot/faq")
async def faq(file: UploadFile = File(...)):
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
            prompt = f"""You are a legal expert specialized in Indian law. Based on the provided document, generate a list of frequently asked questions (FAQs) that a user might have regarding the content of the document. The FAQs should be relevant and specific to the document's subject matter.
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
        faq_list = [q.strip("- ").strip() for q in raw_response.split("\n") if q.strip()]
        if faq_list and faq_list[0].lower().startswith("here are"):
            faq_list = faq_list[1:]
        return JSONResponse(content={"faqs": faq_list})
    
    except Exception as e:
        return ({
            'error': str(e),
            'error_type': str(type(e).__name__),
            'error_file_details': f'Error on line {e.__traceback__.tb_lineno} inside {__file__}'
        })