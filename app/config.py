"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central config — one place for all env vars so we never scatter magic strings.
    Pydantic validates types at startup (fail fast before serving traffic).
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    metadata_database_url: str = Field(
        default="postgresql+asyncpg://querypilot:querypilot@localhost:5435/querypilot_meta",
        alias="METADATA_DATABASE_URL",
    )
    kek_secret: str = Field(default="", alias="KEK_SECRET")

    router_model: str = Field(default="llama-3.1-8b-instant", alias="ROUTER_MODEL")
    sql_model: str = Field(default="llama-3.3-70b-versatile", alias="SQL_MODEL")

    default_row_limit: int = Field(default=1000, alias="DEFAULT_ROW_LIMIT")
    query_timeout_seconds: int = Field(default=5, alias="QUERY_TIMEOUT_SECONDS")
    max_sql_retries: int = Field(default=2, alias="MAX_SQL_RETRIES")
    max_joins: int = Field(default=6, alias="MAX_JOINS")
    max_subqueries: int = Field(default=3, alias="MAX_SUBQUERIES")

    trace_blob_dir: str = Field(default="./data/traces", alias="TRACE_BLOB_DIR")
    faiss_index_dir: str = Field(default="./data/faiss", alias="FAISS_INDEX_DIR")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cors_origins: str = Field(default="http://localhost:8501", alias="CORS_ORIGINS")
    query_cache_ttl_seconds: int = Field(default=3600, alias="QUERY_CACHE_TTL_SECONDS")
    query_cache_enabled: bool = Field(default=True, alias="QUERY_CACHE_ENABLED")

    simple_schema_table_limit: int = Field(default=20, alias="SIMPLE_SCHEMA_TABLE_LIMIT")
    retrieval_top_k: int = Field(default=12, alias="RETRIEVAL_TOP_K")
    retrieval_max_tables: int = Field(default=15, alias="RETRIEVAL_MAX_TABLES")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL",
    )
    docs_dir: str = Field(default="./data/docs", alias="DOCS_DIR")
    docs_search_enabled: bool = Field(default=True, alias="DOCS_SEARCH_ENABLED")
    docs_top_k: int = Field(default=3, alias="DOCS_TOP_K")

    groq_base_url: str = "https://api.groq.com/openai/v1"

    @property
    def docs_dir_path(self) -> Path:
        return Path(self.docs_dir)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
