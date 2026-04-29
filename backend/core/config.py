from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_temperature: float = 0.2
    openai_api_key: str = ""
    embeddings_api_key: str = ""
    embeddings_base_url: str = "https://api.openai.com/v1"
    embeddings_model: str = "text-embedding-3-small"
    embeddings_timeout_seconds: int = 20
    rag_store_path: str = "./.rag_store/listing_chunks.json"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def resolved_groq_model(self) -> str:
        deprecated = {
            "llama-3.1-70b-versatile",
            "llama-3.1-70b-specdec",
        }
        if self.groq_model in deprecated:
            return "llama-3.3-70b-versatile"
        return self.groq_model

    @property
    def resolved_embeddings_api_key(self) -> str:
        return self.embeddings_api_key or self.openai_api_key


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
