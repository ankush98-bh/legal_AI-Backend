from pydantic import BaseModel
from typing import Dict, Any, List

class QueryResponse(BaseModel):
    model: str
    response: Any

class ModelInfo(BaseModel):
    name: str
    modified_at: str
    size: int
    digest: str
    details: Dict[str, Any]

class ModelsResponse(BaseModel):
    models: List[ModelInfo]