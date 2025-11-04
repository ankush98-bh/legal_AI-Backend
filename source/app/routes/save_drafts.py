from fastapi import APIRouter, Body, UploadFile, File, Form, HTTPException, Request
#rom ..services.auth_service import authorize
from pydantic import BaseModel
import os
import shutil
import json
from ..models.request_models import SaveDraftRequest 

router = APIRouter()

BASE_DIR = "drafts"  


@router.post("/save_draft")
#authorize()
async def save_draft_form(
    request: Request,
    draft_content: UploadFile = File(...),
    domain_name: str = Form(...),
    is_new_domain: bool = Form(...),
    current_user=None
):
    try:
        os.makedirs(BASE_DIR, exist_ok=True)

        domain_path = os.path.join(BASE_DIR, domain_name)

        # Create new domain directory if needed
        if is_new_domain:
            os.makedirs(domain_path, exist_ok=True)
        elif not os.path.exists(domain_path):
            raise HTTPException(status_code=400, detail=f"Domain '{domain_name}' does not exist.")

        # Generate unique filename
        draft_files = os.listdir(domain_path)
        draft_number = len(draft_files) + 1
        draft_filename = f"draft_{draft_number}.html"
        draft_path = os.path.join(domain_path, draft_filename)

        # Save the draft content
        with open(draft_path, "wb") as f:
            file_content = await draft_content.read()
            f.write(file_content)

        return {
            "message": "Draft saved successfully",
            "path": draft_path,
            "domain": domain_name,
            "filename": draft_filename
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))