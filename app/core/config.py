from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "📂 File API"
    UPLOAD_DIR: Path = Path("uploads")

    GROQ_API_KEY: str
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "book_tau_e5"

    E5_MODEL_NAME: str = "intfloat/multilingual-e5-large-instruct"
    E5_DEVICE: str = "cpu"

    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    TOP_K: int = 5

    KABIS_USERNAME: str
    KABIS_PASSWORD: str

    # Настройки для pydantic-settings v2
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
