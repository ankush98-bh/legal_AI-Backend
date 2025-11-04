from .draft import router as draft_router
from .query import router as query_router
from .summary import router as summary_router
from .custom_doc import router as custom_doc_router
from .compare_doc import router as compare_doc_router
from .redline_analysis import router as redline_analysis_router
from .legal_bot import router as legal_bot_router
from .ai_proceedings import router as ai_proceedings_router
from .legal_bot import router as clear_history_router
from .legal_bot import router as get_session_id_router
from .legal_bot import router as faq_router
from .custom_ai_proceedings import router as custom_ai_proceedings_router
from .custom_ai_proceedings import router as input_custom_ai_proceedings_router
from .custom_ai_proceedings import router as conclude_custom_ai_proceedings_router
from .cross_exam import router as cross_exam_router
from .auth import router as sign_up_router
from .auth import router as login_router
from .auth import router as logout_router

__all__ = ['draft_router',
           'query_router',
           'summary_router',
           'custom_doc_router',
           'compare_doc_router', 'redline_analysis_router',
           'legal_bot_router', 'clear_history_router', 'get_session_id_router', 'faq_router',
           'ai_proceedings_router',
           'custom_ai_proceedings_router', 'input_custom_ai_proceedings_router', 'conclude_custom_ai_proceedings_router',
           'cross_exam_router',
           'sign_up_router', 'login_router', 'logout_router']