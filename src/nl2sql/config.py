from __future__ import annotations

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_admin_url: str = "postgresql://nl2sql:nl2sql_dev_password@localhost:5432/nl2sql"
    db_reader_url: str = "postgresql://nl2sql_reader:reader_dev_password@localhost:5432/nl2sql"
    db_reader_password: str = "reader_dev_password"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek/deepseek-flash"
    qwen_api_key: str = ""
    qwen_embed_model: str = "qwen3.7-text-embedding"
    qwen_embed_dim: int = 1024
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    retrieval_candidate_limit: int = 30
    retrieval_context_chars: int = 16000
    enable_rag_rerank: bool = False

    @property
    def embedding_key(self) -> str:
        return self.qwen_api_key or os.getenv("DASHSCOPE_API_KEY", "")


def get_settings() -> Settings:
    return Settings()
