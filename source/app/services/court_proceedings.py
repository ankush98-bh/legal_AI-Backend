from fastapi import HTTPException
from typing import Optional
from langchain_huggingface import HuggingFaceEmbeddings
from ..config import EMBEDDING_MODEL, DEVICE, OLLAMA_BASE_URL, DEFAULT_MODEL, FAISS_INDEX_PATH
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaLLM
from langchain.memory import VectorStoreRetrieverMemory, ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain.schema import messages_from_dict, messages_to_dict
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import FAISS
import re
import os
import json

# Initialize global components using configurations from config.py
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={'device': DEVICE})
llm = OllamaLLM(base_url=OLLAMA_BASE_URL, model=DEFAULT_MODEL)
vectorstore: FAISS = None
conversation_chain: ConversationalRetrievalChain = None

SIMULATION_DATA_DIR = "simulation_data"
os.makedirs(SIMULATION_DATA_DIR, exist_ok=True)

def _get_simulation_file_path(session_id: str) -> str:
    """Returns the file path for a given session ID."""
    return os.path.join(SIMULATION_DATA_DIR, f"{session_id}.json")

def _save_simulation_data(session_id: str, data: dict):
    """Saves session data to a JSON file."""
    file_path = _get_simulation_file_path(session_id)
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f)
    except IOError as e:
        return {
            'error': str(e),
            'error_type': str(type(e).__name__),
            'error_file_details': f'Error on line {e.__traceback__.tb_lineno} inside {__file__}',
            'session_id': session_id
        }
    except Exception as e:
        return {
            'error': str(e),
            'error_type': str(type(e).__name__),
            'error_file_details': f'Error on line {e.__traceback__.tb_lineno} inside {__file__}',
            'session_id': session_id
        }

def _load_simulation_data(session_id: str) -> Optional[dict]:
    """Loads session data from a JSON file if it exists."""
    file_path = _get_simulation_file_path(session_id)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
                return data
            except json.JSONDecodeError as e:
                return {
                    'error': str(e),
                    'error_type': str(type(e).__name__),
                    'error_file_details': f'Error on line {e.__traceback__.tb_lineno} inside {__file__}',
                    'session_id': session_id
                }
    return None

def create_vector_store_from_case(document_text: str, session_id: str) -> FAISS:
    """Creates a FAISS index from the provided text content."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_text(document_text)
    vectorstore = FAISS.from_texts(texts, embedding=embeddings)
    simulation_faiss_path = os.path.join(FAISS_INDEX_PATH, session_id)
    os.makedirs(simulation_faiss_path, exist_ok=True)
    vectorstore.save_local(simulation_faiss_path)
    # vectorstore.save_local(FAISS_INDEX_PATH)
    return vectorstore

def load_vector_store_of_case(session_id: str) -> Optional[FAISS]:
    """Loads an existing FAISS index for a specific session."""
    simulation_faiss_path = os.path.join(FAISS_INDEX_PATH, session_id)
    try:
        vectorstore = FAISS.load_local(simulation_faiss_path, embeddings, allow_dangerous_deserialization=True)
        if vectorstore is None:
            raise ValueError("FAISS.load_local returned None unexpectedly.")
        return vectorstore
    except Exception as e:
        return {
            'error': str(e),
            'error_type': str(type(e).__name__),
            'error_file_details': f'Error on line {e.__traceback__.tb_lineno} inside {__file__}',
            'session_id': session_id
        }

def court_proceedings_conversation_chain(session_id: str, document_text: Optional[str] = None) -> ConversationalRetrievalChain:
    """Gets or creates the conversational retrieval chain for a specific session, handling file uploads."""
    session_data = _load_simulation_data(session_id) or {}
    if document_text:
        vectorstore = create_vector_store_from_case(document_text, session_id)
        session_data['vectorstore_path'] = os.path.join(FAISS_INDEX_PATH, session_id)
        session_data['has_document'] = True
        # Create and save the conversation chain immediately after vector store creation
        try:
            chat_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, human_prefix="Human", ai_prefix="AI")
            vector_memory = VectorStoreRetrieverMemory(retriever=vectorstore.as_retriever(), memory_key="chat_history")
            # retriever = vectorstore.as_retriever()
            conversation_chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=vector_memory.retriever, memory=chat_memory)
            session_data['chat_memory'] = {
                "messages": [m.__dict__ for m in chat_memory.chat_memory.messages],
                "memory_key": chat_memory.memory_key,
                "human_prefix": chat_memory.human_prefix,
                "ai_prefix": chat_memory.ai_prefix
            }
            session_data['conversation_chain'] = True
            _save_simulation_data(session_id, session_data)
            return conversation_chain
        except Exception as e:
            return {
                'error': str(e),
                'error_type': str(type(e).__name__),
                'error_file_details': f'Error on line {e.__traceback__.tb_lineno} inside {__file__}',
                'session_id': session_id
            }
    elif session_data.get('has_document'):
        # Load existing conversation chain
        vectorstore = load_vector_store_of_case(session_id)
        if not vectorstore:
                raise HTTPException(status_code=500, detail="Could not load vector store for this session.")
        # Rehydrate memory
        chat_memory_data = session_data.get('chat_memory', {})
        message_dicts = chat_memory_data.get("messages", [])
        restored_messages = messages_from_dict(message_dicts)

        restored_history = ChatMessageHistory()
        restored_history.messages = restored_messages

        chat_memory = ConversationBufferMemory(
            memory_key=chat_memory_data.get("memory_key", "chat_history"),
            return_messages=True,
            human_prefix=chat_memory_data.get("human_prefix", "Human"),
            ai_prefix=chat_memory_data.get("ai_prefix", "AI"),
            chat_memory=restored_history
        )
        vector_memory = VectorStoreRetrieverMemory(retriever=vectorstore.as_retriever(), memory_key="chat_history")
        conversation_chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=vector_memory.retriever, memory=chat_memory)
        return conversation_chain
    elif not document_text and not session_data.get('has_document'):
        raise HTTPException(status_code=400, detail="Please upload a PDF file first to ask questions about it.")
    else:
        raise HTTPException(status_code=500, detail="An unexpected error occurred during session initialization.")

def get_court_proceedings_conversation_chain(session_id: str) -> Optional[ConversationalRetrievalChain]:
    """Retrieves the conversation chain for a specific session if it exists."""
    session_data = _load_simulation_data(session_id)
    if session_data is None:
        raise HTTPException(status_code=400, detail="Session Data not found. Please start a new session.")
    if session_data and session_data.get('conversation_chain'):
        memory_data = session_data.get('chat_memory', {})
        chat_messages = memory_data.get('messages', []) # Assuming 'messages' key
        restored_history = ChatMessageHistory()
        for message in messages_from_dict(chat_messages):
            restored_history.add_message(message)

        chat_memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            chat_memory=restored_history,
            human_prefix=memory_data.get("human_prefix", "Human"),
            ai_prefix=memory_data.get("ai_prefix", "AI")
        )
        vectorstore = load_vector_store_of_case(session_id)
        if vectorstore:
            vector_memory = VectorStoreRetrieverMemory(retriever=vectorstore.as_retriever(), memory_key="chat_history")
            conversation_chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=vector_memory.retriever,
                memory=chat_memory
            )
            return conversation_chain
        else:
            raise HTTPException(status_code=500, detail="Error: Could not load vector store for this session.")
    else:
        print("No valid conversation chain found for session:", session_id)
    return None

# def update_simulation_chat_history(session_id: str, memory: ConversationBufferMemory):
#     """Updates the general chat history in the session data."""
#     try:
#         simulation_data = _load_simulation_data(session_id) or {}
#         simplified_messages = messages_to_dict(memory.chat_memory.messages)

#         simulation_data['chat_memory'] = {
#             "messages": simplified_messages,
#             "memory_key": memory.memory_key,
#             "human_prefix": memory.human_prefix,
#             "ai_prefix": memory.ai_prefix
#         }
#         _save_simulation_data(session_id, simulation_data)
#     except Exception as e:
#         return {
#             'error': str(e),
#             'error_type': str(type(e).__name__),
#             'error_file_details': f'Error on line {e.__traceback__.tb_lineno} inside {__file__}',
#             'session_id': session_id
#         }

def parse_conversation(response: str) -> list:
    """
    Parse the line-based conversation into a list of dicts.
    Any line matching 'speaker||designation||speech' starts a new entry;
    all other lines (including bullet points) are appended to the current entry's speech.
    """
    response = response.replace('\\n', '\n')
    conversation = []
    current = None

    # Pattern for lines that define a new speaker entry
    entry_re = re.compile(r'^\s*([^|]+)\|\|([^|]+)\|\|(.+)$')

    for raw_line in response.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        m = entry_re.match(line)
        if m:
            # Save previous entry
            if current:
                conversation.append(current)
            # Start a new entry
            speaker, designation, speech = m.groups()
            current = {
                "speaker": speaker.strip(),
                "designation": designation.strip(),
                "speech": speech.strip()
            }
        else:
            # Continuation of the previous speech (preserve bullets/newlines)
            if current:
                current["speech"] += "\n" + line
            else:
                # Fallback: treat unformatted text as a single AI response
                conversation.append({
                    "speaker": "AI",
                    "designation": "Assistant",
                    "speech": line
                })
    # Append the last one
    if current:
        conversation.append(current)

    return conversation

def extract_conversational_lines_from_chat_history(chat_memory: dict) -> list:
    """
    Look into the chat_history to find the latest AI message that contains courtroom-style formatted lines.
    Returns the content as a string if found, else returns an empty string.
    """
    if isinstance(chat_memory, dict):
        chat_history = chat_memory.get("chat_history", [])
    elif isinstance(chat_memory, list):
        # If it's already a list, use it directly
        chat_history = chat_memory

    for message in reversed(chat_history):
            # if message.get("type") == "ai":
            #     content = message.get("data", {}).get("content", "")
            #     if content and "||" in content:  # Quick check to skip unrelated AI messages
            #         parsed_lines = parse_conversation(content)
            #         print("[DEBUG] Parsed lines from AI message:\n", parsed_lines)
            #         if parsed_lines:  # Only return if parsing found valid structured lines
            #             return parsed_lines
            #         else:
            #             print("[WARNING] No valid courtroom dialogue lines found in AI message.")
            #             return []
            if isinstance(message, AIMessage):
                content = message.content  # Extract content from AIMessage object
                if content and "||" in content:  # Quick check to skip unrelated AI messages
                    parsed_lines = parse_conversation(content)
                    print("[DEBUG] Parsed lines from AI message:\n", parsed_lines)
                    if parsed_lines:  # Only return if parsing found valid structured lines
                        return parsed_lines
                    else:
                        print("[WARNING] No valid courtroom dialogue lines found in AI message.")
                        return []

# def parse_conversation(response: str) -> list:
#     """Parse the line-based conversation into a list of dictionaries."""
#     lines = re.split(r'\n+|(?<=\n)[\*\-•\d]+\s+', response.strip())
#     conversation = []
#     for line in lines:
#         parts = line.split('||', 2)
#         if len(parts) == 3:
#             speaker, designation, speech = parts
#             conversation.append({
#                 "speaker": speaker.strip(),
#                 "designation": designation.strip(),
#                 "speech": speech.strip()
#             })
#     return conversation

def is_likely_case_file(text: str) -> bool:
    """
    Heuristically check if the text looks like a court judgment or case file.
    """
    legal_indicators = [
        "IN THE SUPREME COURT", "IN THE HIGH COURT", "WRIT PETITION", 
        "CIVIL APPEAL", "RESPONDENT", "APPELLANT", "HON'BLE", 
        "CONSTITUTION BENCH", "JUDGMENT DELIVERED", "ORDER", 
        "BENCH", "DECREE", "ISSUE FOR CONSIDERATION", "ARGUED BY", 
        "PRONOUNCED", "DATE OF JUDGMENT", "PETITIONER VERSUS RESPONDENT",
        "VERSUS", "CIVIL PROCEDURE CODE", "INDIAN PENAL CODE",
        "EVIDENCE ACT", "JUDICIAL PRONOUNCEMENTS", "CITATION","SESSIONS JUDGE"
    ]
    
    lower_text = text.lower()
    return sum(1 for keyword in legal_indicators if keyword.lower() in lower_text) >= 3