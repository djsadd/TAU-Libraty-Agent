import dramatiq
import logging
import asyncio
import json
from app.api.routes.kabis_integrate import kabis_upload

logger = logging.getLogger(__name__)

@dramatiq.actor
def run_kabis_upload_task():
    logger.info("🚀 Старт задачи run_kabis_upload_task")
    try:
        result = asyncio.run(kabis_upload())

        # Если это JSONResponse → берём body
        if hasattr(result, "body"):
            preview = result.body.decode("utf-8")
        else:
            preview = str(result)

        # Чтобы не залить логи, ограничим длину
        logger.info(f"📚 Результат kabis_upload: {preview[:500]}")
        logger.info("✅ Задача run_kabis_upload_task выполнена успешно")
    except Exception as e:
        logger.error(f"❌ Ошибка в run_kabis_upload_task: {e}", exc_info=True)
