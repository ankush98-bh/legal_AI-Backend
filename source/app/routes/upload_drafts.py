# import os
# from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
# from ..services.auth_service import authorize
# from fastapi.responses import JSONResponse, FileResponse
# import shutil # Import shutil for file operations
# from ..models.request_models import DraftRequest
# # from ..services.file_converter import convert_file_to_docx
# import uuid

# router = APIRouter()

# # Define the base directory for storing drafts
# BASE_DIR = "drafts"

# @router.post("/upload_drafts/")
# #authorize()
# async def upload_draft(
#     request: Request,
#     file: UploadFile = File(...),
#     domain: str = Form(...),
#     file_name: str = Form(...),  # Now required
#     current_user=None
# ):
#     '''Comment out if you have to convert the user uploaded file to docx format'''
#     # file = await convert_file_to_docx(file)

#     """
#     Uploads a draft file under 'drafts/<domain>/<file_name>'.
#     - Uses 'file_name' from the form as the saved filename.
#     - Raises an error if the file already exists under the domain folder.
#     - Extracts the extension from the uploaded file, not from 'file_name'.
#     """
#     #try:
#     # Ensure the base and domain-specific directories exist
#     os.makedirs(BASE_DIR, exist_ok=True)
#     user_id = current_user.user_id
#     user_base_dir = os.path.join(BASE_DIR, str(user_id))
#     domain_path = os.path.join(user_base_dir,domain)
#     os.makedirs(domain_path, exist_ok=True)

#     # Validate uploaded filename
#     original_filename = file.filename
#     if not original_filename:
#         raise HTTPException(status_code=400, detail="No filename provided in the upload.")

#     # Extract file extension from the uploaded file
#     _, file_extension = os.path.splitext(original_filename)
#     # print(f"Extracted file extension: {file_extension}")

#     # Add extension to the file_name if not already included
#     if not file_name.endswith(file_extension):
#         file_name += file_extension

#     # Construct full path using user-specified file_name
#     file_path = os.path.join(domain_path, file_name)

#     # Check if file already exists
#     if os.path.exists(file_path):
#         raise HTTPException(status_code=409, detail=f"A file named '{file_name}' already exists in domain '{domain}'.")

#     # Save the file
#     with open(file_path, "wb") as f:
#         file.file.seek(0)
#         shutil.copyfileobj(file.file, f)

#     return JSONResponse(content={
#     "message": f"File '{file_name}' successfully saved under domain '{domain}'.",
#     "path": file_path,
#     "action_taken": "create",
#     "saved_filename": file_name,
#     "file_extension": file_extension
#     })

    

# @router.get("/list_drafts/")
# #@authorize()
# async def list_drafts(request: Request, current_user=None):
#     """
#     Lists all folders under the 'drafts' directory and the files contained within each folder.
#     Returns a dictionary where keys are folder names (domains) and values are lists of filenames.
#     """
#     try:
#         user_id = current_user.user_id
#         user_base_dir = os.path.join(BASE_DIR, str(user_id))
#         if not os.path.exists(user_base_dir):
#             return JSONResponse(content={"response": {}}, status_code=200)

#         response_data = {}

#         # Iterate over each subdirectory (domain)
#         for domain_folder in os.listdir(user_base_dir):
#             domain_path = os.path.join(user_base_dir, domain_folder)
#             # Only process directories
#             if os.path.isdir(domain_path):
#                 # Get list of files in the domain folder
#                 files = [
#                     f for f in os.listdir(domain_path)
#                     if os.path.isfile(os.path.join(domain_path, f))
#                 ]
#                 response_data[domain_folder] = files

#         return JSONResponse(content={"response": response_data}, status_code=200)

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to list drafts: {str(e)}")

# def get_mime_type(file_name: str) -> str:
#     extension = os.path.splitext(file_name)[1].lower()
#     mime_types = {
#         '.pdf': 'application/pdf',
#         '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
#         '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
#         '.txt': 'text/plain',
#         '.html': 'text/html',
#     }
#     return mime_types.get(extension, 'application/octet-stream')

# @router.post("/get_draft/")
# #authorize()
# async def get_draft(request: Request,payload: DraftRequest,
#                     current_user= None):
#     try:
#         user_id = current_user.user_id
#         user_base_dir = os.path.join(BASE_DIR, str(user_id))
#         file_path = os.path.join(user_base_dir, payload.domain, payload.file_name)
#         if not os.path.isfile(file_path):
#             raise HTTPException(status_code=404, detail="File not found.")
#         return FileResponse(
#             path=file_path,
#             filename=payload.file_name,
#             media_type=get_mime_type(payload.file_name)
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         # print(f"Error retrieving file: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to retrieve file: {str(e)}")

# @router.post("/delete_draft/")
# async def delete_draft(payload: DraftRequest):
#     """
#     Deletes a draft file under 'drafts/<domain>/<file_name>'.
#     - Returns success message if deletion is successful.
#     - Raises 404 if file not found.
#     """
#     try:
#         file_path = os.path.join(BASE_DIR, payload.domain, payload.file_name)
        
#         # Check if the file exists
#         if not os.path.isfile(file_path):
#             raise HTTPException(status_code=404, detail="File not found.")

#         # Delete the file
#         os.remove(file_path)

#         return JSONResponse(content={
#             "message": f"File '{payload.file_name}' under domain '{payload.domain}' deleted successfully.",
#             "deleted": True
#         }, status_code=200)

#     except HTTPException:
#         raise
#     except Exception as e:
#         # print(f"Error deleting file: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from ..models.request_models import DraftRequest

router = APIRouter()

# Base directory for storing drafts
BASE_DIR = "drafts"


@router.post("/upload_drafts/")
# @authorize()  # Optional — only use if you add authentication later
async def upload_draft(
    request: Request,
    file: UploadFile = File(...),
    domain: str = Form(...),
    file_name: str = Form(...),  # Required
    current_user=None
):
    """
    Uploads a draft file under 'drafts/<user_id or guest>/<domain>/<file_name>'.
    Works without authentication by assigning a unique guest ID.
    """
    try:
        # ✅ Generate guest user_id if not authenticated
        user_id = getattr(current_user, "user_id", None) or f"guest_{uuid.uuid4().hex[:8]}"

        # ✅ Create necessary directories
        os.makedirs(BASE_DIR, exist_ok=True)
        user_base_dir = os.path.join(BASE_DIR, str(user_id))
        domain_path = os.path.join(user_base_dir, domain)
        os.makedirs(domain_path, exist_ok=True)

        # ✅ Validate uploaded file name
        original_filename = file.filename
        if not original_filename:
            raise HTTPException(status_code=400, detail="No filename provided in the upload.")

        # ✅ Extract extension from uploaded file
        _, file_extension = os.path.splitext(original_filename)

        # ✅ Add extension if missing
        if not file_name.endswith(file_extension):
            file_name += file_extension

        # ✅ Construct final path
        file_path = os.path.join(domain_path, file_name)

        # ✅ Prevent overwriting
        if os.path.exists(file_path):
            raise HTTPException(
                status_code=409,
                detail=f"A file named '{file_name}' already exists in domain '{domain}'."
            )

        # ✅ Save the file
        with open(file_path, "wb") as f:
            file.file.seek(0)
            shutil.copyfileobj(file.file, f)

        return JSONResponse(content={
            "message": f"File '{file_name}' successfully saved under domain '{domain}'.",
            "path": file_path,
            "user_id": user_id,
            "action_taken": "create",
            "saved_filename": file_name,
            "file_extension": file_extension
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving draft: {e}")


@router.get("/list_drafts/")
# @authorize()
async def list_drafts(request: Request, current_user=None):
    """
    Lists all domain folders and files for a given user (or guest).
    Returns a dictionary: { "domain": ["file1", "file2", ...] }
    """
    try:
        user_id = getattr(current_user, "user_id", None) or "guest_default"
        user_base_dir = os.path.join(BASE_DIR, str(user_id))

        if not os.path.exists(user_base_dir):
            return JSONResponse(content={"response": {}}, status_code=200)

        response_data = {}

        # Iterate over domain folders
        for domain_folder in os.listdir(user_base_dir):
            domain_path = os.path.join(user_base_dir, domain_folder)
            if os.path.isdir(domain_path):
                files = [
                    f for f in os.listdir(domain_path)
                    if os.path.isfile(os.path.join(domain_path, f))
                ]
                response_data[domain_folder] = files

        return JSONResponse(content={"response": response_data}, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list drafts: {str(e)}")


def get_mime_type(file_name: str) -> str:
    extension = os.path.splitext(file_name)[1].lower()
    mime_types = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.txt': 'text/plain',
        '.html': 'text/html',
    }
    return mime_types.get(extension, 'application/octet-stream')


@router.post("/get_draft/")
# @authorize()
async def get_draft(
    request: Request,
    payload: DraftRequest,
    current_user=None
):
    """
    Fetches and returns a specific draft file.
    Works even without authentication (uses guest_default if no user).
    """
    try:
        user_id = getattr(current_user, "user_id", None) or "guest_default"
        user_base_dir = os.path.join(BASE_DIR, str(user_id))
        file_path = os.path.join(user_base_dir, payload.domain, payload.file_name)

        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail="File not found.")

        return FileResponse(
            path=file_path,
            filename=payload.file_name,
            media_type=get_mime_type(payload.file_name)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve file: {str(e)}")


@router.post("/delete_draft/")
async def delete_draft(payload: DraftRequest):
    """
    Deletes a draft file under 'drafts/<domain>/<file_name>'.
    Works without authentication.
    """
    try:
        # Support guest deletion (no user folder)
        domain_path = os.path.join(BASE_DIR, payload.domain)
        file_path = os.path.join(domain_path, payload.file_name)

        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail="File not found.")

        os.remove(file_path)

        return JSONResponse(content={
            "message": f"File '{payload.file_name}' under domain '{payload.domain}' deleted successfully.",
            "deleted": True
        }, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
