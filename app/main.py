from fastapi import FastAPI
from .core.config import settings
from .core.cors import setup_cors
from .api.routes.upload import router as upload_router
from .api.routes.chat import router as chat_router
from .api.routes.jobs import router as jobs_router


app = FastAPI(
    title=settings.APP_NAME,
    description="""
Минимальный API для загрузки файлов (PDF, TXT, DOCX, EPUB) и RAG-чата.
""",
    version="1.0.0",
    contact={"name": "Erasil B.", "email": "e.bahytzhanuly@tau-edu.kz"},
    license_info={"name": "MIT License", "url": "https://opensource.org/licenses/MIT"},
)

setup_cors(app)
app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(jobs_router)
