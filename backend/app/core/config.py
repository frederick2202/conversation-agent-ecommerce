"""
Configurações da aplicação carregadas de variáveis de ambiente.

O Pydantic Settings lê cada campo da variável de ambiente de mesmo nome
(sem diferenciar maiúsculas/minúsculas, ex.: `GEMINI_API_KEY` -> `gemini_api_key`)
ou do arquivo `.env` na pasta de execução (veja `backend/.env.example`).
Os valores abaixo são apenas padrões para desenvolvimento local.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # `extra="ignore"`: variáveis desconhecidas no .env não geram erro.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://lumen:lumen_secret@localhost:5432/lumen_db"
    gemini_api_key: str = ""  # Sem chave válida o chat responde com aviso e embeddings usam fallback local.
    gemini_chat_model: str = "gemini-3.5-flash-lite"  # Modelo LLM usado pelo agente (app/agent/graph.py).
    gemini_embedding_model: str = "gemini-embedding-001"  # Modelo de embeddings (app/services/embedding_service.py).
    cors_origins: str = "http://localhost:3000"  # Origens permitidas, separadas por vírgula.


# Instância única (singleton) importada pelo resto do código.
settings = Settings()
