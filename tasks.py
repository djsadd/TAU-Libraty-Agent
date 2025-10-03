import dramatiq
from app.api.routes.kabis_integrate import kabis_upload

@dramatiq.actor
def run_kabis_upload_task():
    import asyncio
    asyncio.run(kabis_upload())
