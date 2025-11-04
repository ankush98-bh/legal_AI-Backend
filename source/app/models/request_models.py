from pydantic import BaseModel
from typing import Optional, Dict, Any
from ..config import DEFAULT_MODEL

class QueryRequest(BaseModel):
    domain: str
    sub_domain: str
    model: Optional[str] = DEFAULT_MODEL
    prompt: str
    options: Optional[Dict[str, Any]] = None
    format_output: Optional[bool] = True #added format output

class FormattedContent(BaseModel):
    text: str
    html: Optional[str] = None

class DraftRequest(BaseModel):
    file_name: str
    domain: str

class SaveDraftRequest(BaseModel):
    draft_content: str
    domain_name: str
    is_new_domain: bool
