from fastapi import FastAPI
from source.app.routes.draft import router as draft_router
from source.app.routes.query import router as query_router
from source.app.routes.summary import router as summary_router
from source.app.routes.custom_doc import router as custom_doc_router
from source.app.routes.compare_doc import router as compare_doc_router
from source.app.routes.redline_analysis import router as redline_analysis_router
from source.app.routes.legal_bot import router as legal_bot_router
from source.app.routes.legal_bot import router as clear_history_router
from source.app.routes.legal_bot import router as get_session_id_router
from source.app.routes.legal_bot import router as faq_router
from source.app.routes.ai_proceedings import router as ai_proceedings_router
from source.app.routes.custom_ai_proceedings import router as custom_ai_proceedings_router
from source.app.routes.custom_ai_proceedings import router as input_custom_ai_proceedings_router
from source.app.routes.custom_ai_proceedings import router as conclude_custom_ai_proceedings_router
from source.app.routes.upload_drafts import router as upload_draft_documents
from source.app.routes.save_drafts import router as save_drafts_domain
from source.app.routes.cross_exam import router as cross_exam_router
from source.app.routes.auth import router as sign_up_router
from source.app.routes.auth import router as login_router
from source.app.routes.auth import router as logout_router
from fastapi.middleware.cors import CORSMiddleware
from source.app.database import Base, engine
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler to create database tables on startup."""
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")
    yield  # Application runs after this point

# Create FastAPI app
app = FastAPI(
    title="Ollama API Integration",
    description="A FastAPI service to interact with Ollama models",
    version="1.1.0",
    lifespan=lifespan
)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],  # Allows all methods
#     allow_headers=["*"],  # Allows all headers
# )
origins = [
    "http://74.225.226.138",
    "http://74.225.226.138:3000",
    "http://74.225.226.138:5173",
    "http://localhost:3000",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # ✅ Must specify exact domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],)

# API Routes
@app.get("/")
async def root():
    """Root endpoint that provides basic API information"""
    return {"message": "Ollama API Integration", "docs": "/docs"}

app.include_router(draft_router, prefix="/api/legal-draft")
app.include_router(query_router, prefix="/api/query-process")
app.include_router(summary_router, prefix="/api/summary")
app.include_router(custom_doc_router, prefix="/api/custom-doc")
app.include_router(compare_doc_router, prefix="/api/compare-doc")
app.include_router(redline_analysis_router, prefix="/api/redline-analysis")
app.include_router(legal_bot_router, prefix="/api/legal-bot")
app.include_router(clear_history_router, prefix="/api/clear-history")
app.include_router(get_session_id_router, prefix="/api/get-session-id")
app.include_router(faq_router, prefix="/api/faq")
app.include_router(ai_proceedings_router, prefix="/api/ai-proceedings")
app.include_router(custom_ai_proceedings_router, prefix="/api/custom-ai-proceedings")
app.include_router(input_custom_ai_proceedings_router, prefix="/api/user-input-custom-ai")
app.include_router(conclude_custom_ai_proceedings_router, prefix="/api/conclude-custom-ai-proceedings")
app.include_router(upload_draft_documents,prefix="/api/upload-drafts")
app.include_router(save_drafts_domain,prefix="/api/save-drafts" )
app.include_router(cross_exam_router, prefix="/api/cross-exam")
app.include_router(sign_up_router, prefix="/api/auth")
app.include_router(login_router, prefix="/api/auth")
app.include_router(logout_router, prefix="/api/auth")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)