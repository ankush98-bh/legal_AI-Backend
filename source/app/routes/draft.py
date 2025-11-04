from fastapi import APIRouter
#rom ..services.auth_service import authorize
from fastapi import Request

router = APIRouter()

@router.get("/draft_document")
#authorize()
async def draft_document(request: Request, current_user=None):
    try:
        return {'response':
                {
                    'Property Sale & Purchase' : ['Sale Deed', 'Agreement for Sale', 'Gift Deed', 'Partition Deed'],
                    'Lease & Rental Agreements' : ['Commercial Lease Agreement', 'Residential Rental Agreement']
                }}
    except Exception as e:
        return ({
            'error': str(e),
            'error_type': str(type(e).__name__),
            'error_file_details': f'error on line {e.__traceback__.tb_lineno} inside {__file__}'
        })