from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql://study:study_local@localhost:55433/study"
    ollama_url: str = "http://localhost:11435"
    chat_model: str = "qwen2.5:3b"
    embedding_model: str = "embeddinggemma"
    embedding_dimensions: int = Field(default=768, ge=768, le=768)
    answer_context_chunks: int = Field(default=3, ge=1, le=5)
    max_pdf_bytes: int = 10 * 1024 * 1024
    max_pages: int = 100
