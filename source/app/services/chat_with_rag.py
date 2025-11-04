import re
from typing import List, Optional
from fastapi import HTTPException
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM
from langchain.memory import VectorStoreRetrieverMemory, ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain, ConversationChain
import os
import json
import shutil
from langchain.text_splitter import RecursiveCharacterTextSplitter
from ..config import (
    FAISS_INDEX_PATH,
    EMBEDDING_MODEL,
    DEFAULT_MODEL,
    DEVICE,
    OLLAMA_BASE_URL
)

# Directory to store session data
SESSION_DATA_DIR = "sessions"
os.makedirs(SESSION_DATA_DIR, exist_ok=True)

def _get_session_file_path(session_id: str) -> str:
    """Returns the file path for a given session ID."""
    return os.path.join(SESSION_DATA_DIR, f"{session_id}.json")

def _save_session_data(session_id: str, data: dict):
    """Saves session data to a JSON file."""
    file_path = _get_session_file_path(session_id)
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

def _load_session_data(session_id: str) -> Optional[dict]:
    """Loads session data from a JSON file if it exists."""
    file_path = _get_session_file_path(session_id)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                return {
                    'error': str(e),
                    'error_type': str(type(e).__name__),
                    'error_file_details': f'Error on line {e.__traceback__.tb_lineno} inside {__file__}',
                    'session_id': session_id
                }
    return None

# Initialize global components using configurations from config.py
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={'device': DEVICE})
# tokenizer = AutoTokenizer.from_pretrained(DEFAULT_MODEL)
# model = AutoModelForCausalLM.from_pretrained(DEFAULT_MODEL)
# llm_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer, max_length=MAX_LENGTH, temperature=TEMPERATURE, device=DEVICE)
llm = OllamaLLM(base_url=OLLAMA_BASE_URL, model=DEFAULT_MODEL)
vectorstore: FAISS = None
conversation_chain: ConversationalRetrievalChain = None

def create_vector_store_from_text(document_text: str, session_id: str) -> FAISS:
    """Creates a FAISS index from the provided text content."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_text(document_text)
    vectorstore = FAISS.from_texts(texts, embedding=embeddings)
    session_faiss_path = os.path.join(FAISS_INDEX_PATH, session_id)
    os.makedirs(session_faiss_path, exist_ok=True)
    vectorstore.save_local(session_faiss_path)
    # vectorstore.save_local(FAISS_INDEX_PATH)
    return vectorstore

def load_vector_store(session_id: str) -> Optional[FAISS]:
    """Loads an existing FAISS index for a specific session."""
    session_faiss_path = os.path.join(FAISS_INDEX_PATH, session_id)
    try:
        vectorstore = FAISS.load_local(session_faiss_path, embeddings)
        return vectorstore
    except Exception:
        return None

def preprocess_text(text: str) -> str:
    """
    Normalize text by removing extra spaces and standardizing
    
    Args:
        text (str): Input text to normalize
    
    Returns:
        str: Normalized text
    """
    return re.sub(r'\s+', ' ', text.strip().lower())

def get_general_conversation_chain(session_id: str) -> ConversationChain:
    """Gets or creates a general conversational chain for a specific session."""
    session_data = _load_session_data(session_id) or {}

    if 'general_conversation_chain_obj' not in session_data:
        # Create a basic chat memory for general questions
        general_chat_memory = ConversationBufferMemory(
            memory_key="history",
            return_messages=True
        )
        system_prompt = """
            You are a highly knowledgeable Indian legal assistant.
            - You must answer general questions based on Indian Law
            - If no document context is provided, answer using your own legal knowledge
            - Do not apologize or say you don't understand unless absolutely necessary
            - Provide short, accurate explanations with real legal meaning
            """

        prompt = PromptTemplate(
            input_variables=["history", "input"],
            template=system_prompt + """
            Conversation History:
            {history}

            User Question:
            {input}

            Assistant Response:
            """
        )

        conversation_chain = ConversationChain(
            llm=llm,
            memory=general_chat_memory,
            prompt=prompt,
            verbose=True
        )
        #print("\n✅ General ConversationChain created successfully\n")
        # conversation_chain = ConversationChain(
        #     llm=llm,
        #     memory=general_chat_memory
        # )
        session_data['general_conversation_chain_memory'] = general_chat_memory.model_dump() # Save memory state
        session_data['general_conversation_chain_obj'] = True # Indicate chain exists
        _save_session_data(session_id, session_data)
        #print(conversation_chain)
        return conversation_chain
    else:
        memory_data = session_data.get('general_conversation_chain_memory', {})
        chat_messages = memory_data.get('chat_memory', {}).get('messages', [])
        history = ChatMessageHistory()
        for msg in chat_messages:
            if msg.get('type') == 'human':
                history.add_user_message(msg.get('content'))
            elif msg.get('type') == 'ai':
                history.add_ai_message(msg.get('content'))

        general_chat_memory = ConversationBufferMemory(
            memory_key="history",
            return_messages=True,
            chat_memory=history  # Initialize with the ChatMessageHistory
        )
        conversation_chain = ConversationChain(
            llm=llm,
            memory=general_chat_memory
        )
        return conversation_chain

def update_general_chat_history(session_id: str, memory: ConversationBufferMemory):
    """Updates the general chat history in the session data."""
    session_data = _load_session_data(session_id) or {}
    if session_data and 'general_conversation_chain_memory' in session_data:
        session_data['general_conversation_chain_memory'] = memory.model_dump()
        _save_session_data(session_id, session_data)

def clear_session_history(session_id: str, with_file: bool = False):
    """Clears the chat history for a specific session, optionally for general or document-related chats."""
    session_data = _load_session_data(session_id)
    if session_data:
        if with_file == False and 'general_conversation_chain_memory' in session_data:
            session_data['general_conversation_chain_memory']['chat_memory']['messages'] = []
        if with_file == True and 'vectorstore_path' in session_data:
            vectorstore_path = session_data['vectorstore_path']
            try:
                if os.path.exists(vectorstore_path):
                    shutil.rmtree(vectorstore_path)
            except Exception as e:
                return {
                    'error': str(e),
                    'error_type': str(type(e).__name__),
                    'error_file_details': f'Error on line {e.__traceback__.tb_lineno} inside {__file__}',
                    'session_id': session_id
                }
        _save_session_data(session_id, session_data)

def get_or_create_conversation_chain(session_id: str, document_text: Optional[str] = None) -> ConversationalRetrievalChain:
    """Gets or creates the conversational retrieval chain for a specific session, handling file uploads."""
    session_data = _load_session_data(session_id) or {}
    if document_text:
        text = preprocess_text(document_text)
        vectorstore = create_vector_store_from_text(text, session_id)
        session_data['vectorstore_path'] = os.path.join(FAISS_INDEX_PATH, session_id)
        session_data['has_document'] = True
        # Create and save the conversation chain immediately after vector store creation
        try:
            chat_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
            # vector_memory = VectorStoreRetrieverMemory(retriever=vectorstore.as_retriever(), memory_key="chat_history")
            retriever = vectorstore.as_retriever()
            conversation_chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever, memory=chat_memory)
            session_data['chat_memory'] = chat_memory.model_dump()
            session_data['conversation_chain'] = True
            _save_session_data(session_id, session_data)
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
        vectorstore = load_vector_store(session_id)
        if vectorstore and session_data.get('conversation_chain'):
            chat_memory = ConversationBufferMemory.from_dict(session_data.get('chat_memory', {}))
            retriever = vectorstore.as_retriever()
            conversation_chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever, memory=chat_memory)
            return conversation_chain
        elif vectorstore:
            # Re-create the conversation chain if vectorstore exists but chain doesn't
            chat_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
            retriever = vectorstore.as_retriever()
            conversation_chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever, memory=chat_memory)
            session_data['chat_memory'] = chat_memory.model_dump()
            session_data['conversation_chain'] = True
            _save_session_data(session_id, session_data)
            return conversation_chain
        else:
            raise HTTPException(status_code=500, detail="Error: Could not load vector store for this session.")
    elif not document_text and not session_data.get('has_document'):
        raise HTTPException(status_code=400, detail="Please upload a PDF file first to ask questions about it.")
    else:
        raise HTTPException(status_code=500, detail="An unexpected error occurred during session initialization.")

def get_session_conversation_chain(session_id: str) -> Optional[ConversationalRetrievalChain]:
    """Retrieves the conversation chain for a specific session if it exists."""
    session_data = _load_session_data(session_id)
    if session_data and session_data.get('conversation_chain'):
        memory_data = session_data.get('chat_memory', {})
        chat_messages = memory_data.get('messages', []) # Assuming 'messages' key
        history = ChatMessageHistory()
        for msg in chat_messages:
            if msg.get('type') == 'human':
                history.add_user_message(msg.get('content'))
            elif msg.get('type') == 'ai':
                history.add_ai_message(msg.get('content'))

        chat_memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            chat_memory=history
        )
        vectorstore = load_vector_store(session_id)
        if vectorstore:
            retriever = vectorstore.as_retriever()
            conversation_chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=retriever,
                memory=chat_memory
            )
            return conversation_chain
    return None


 