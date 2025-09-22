# scripts/init_db.py
from app.core.db import Base, engine
from app.models.job import Job  # noqa: F401 (важно импортировать)
from app.models.books import Document  # noqa: F401 (важно импортировать)
Base.metadata.create_all(bind=engine)
