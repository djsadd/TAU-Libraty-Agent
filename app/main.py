import logging
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .core.config import settings
from .core.cors import setup_cors

from .api.routes.upload import router as upload_router
from .api.routes.chat import router as chat_router
from .api.routes.jobs import router as jobs_router
from .api.routes.kabis_integrate import router as kabis_router
from app.api.routes.libtau_integrate import router as lib_router
from app.tasks import run_kabis_upload_task  # наш актор

# Логгер
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title=settings.APP_NAME,
    description="""
Минимальный API для загрузки файлов (PDF, TXT, DOCX, EPUB) и RAG-чата.
""",
    version="1.0.0",
    contact={"name": "Erasil B.", "email": "e.bahytzhanuly@tau-edu.kz"},
    license_info={"name": "MIT License", "url": "https://opensource.org/licenses/MIT"},
)

# Routers
setup_cors(app)
app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(jobs_router)
app.include_router(kabis_router)
app.include_router(lib_router)

# APScheduler
scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def startup_event():
    # Планируем задачу: запуск каждый день в 02:00
    def enqueue_task():
        logger.info("⏰ Планировщик: ставим задачу run_kabis_upload_task в очередь")
        run_kabis_upload_task.send()

    scheduler.add_job(
        enqueue_task,
        trigger="interval",
        seconds=360,
        id="kabis_test_upload",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("✅ APScheduler запущен, задача на 02:00 зарегистрирована")


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    logger.info("🛑 APScheduler остановлен")
