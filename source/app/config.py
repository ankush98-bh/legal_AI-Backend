import os
from dotenv import load_dotenv
import torch

load_dotenv()


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")

if not OLLAMA_BASE_URL:
    raise ValueError("OLLAMA_BASE_URL is not set. Please set it in the environment variables or .env file.")

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
LLM_MODEL = os.getenv("LLM_MODEL")
DEFAULT_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DEVICE = os.getenv("DEFAULT_DEVICE")
MAX_LENGTH = int(os.getenv("MAX_LENGTH"))
TEMPERATURE = float(os.getenv("TEMPERATURE"))
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# Ensure directories exist (this logic remains in config.py as it's part of setup)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FAISS_INDEX_PATH, exist_ok=True)