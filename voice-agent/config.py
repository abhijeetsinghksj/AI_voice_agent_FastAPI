from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "voice-agent"
    host: str = "0.0.0.0"
    port: int = 8080

    deepgram_api_key: str = ""
    groq_api_key: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "Rachel"

    redis_url: str = "redis://localhost:6379/0"
    faiss_index_path: str = "knowledge_base/faiss.index"
    faiss_meta_path: str = "knowledge_base/faiss_meta.json"
    docs_path: str = "knowledge_base/sample_docs"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
