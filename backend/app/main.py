"""
Ponto de entrada da API FastAPI do e-commerce Lumen.

Responsabilidades deste módulo:
- Criar a instância `app` do FastAPI (usada pelo Uvicorn: `uvicorn app.main:app`).
- Garantir, na inicialização, que a extensão `pgvector` exista no PostgreSQL e que
  todas as tabelas declaradas em `app.models.entities` estejam criadas.
- Configurar CORS para que o frontend Next.js possa consumir a API.
- Registrar os tratadores globais de exceção e os routers (controllers) de cada domínio.

Arquitetura em camadas usada no backend:
    controllers (rotas HTTP) -> services (regras de negócio) -> repositories (acesso ao banco)
    models/entities (tabelas ORM) e schemas (DTOs Pydantic de entrada/saída)
    agent/ (agente de IA LangGraph + Gemini que usa os services como "ferramentas")
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.controllers import (
    cart_controller,
    chat_controller,
    faq_controller,
    product_controller,
    review_controller,
)
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.models.entities import Base


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Ciclo de vida da aplicação: o código antes do `yield` roda no startup.

    Não há ferramenta de migrations (ex.: Alembic); o schema é criado diretamente
    a partir dos modelos ORM. `create_all` só cria tabelas inexistentes — não altera
    colunas de tabelas que já existem.
    """
    async with engine.begin() as conn:
        # Extensão necessária para o tipo de coluna `vector` (embeddings da busca semântica).
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # `create_all` é síncrono, por isso é executado via `run_sync` na conexão assíncrona.
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Lumen E-Commerce & AI Agent API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # CORS_ORIGINS é uma string separada por vírgulas (ex.: "http://localhost:3000,https://loja.com").
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Converte DomainException (e erros inesperados) em respostas JSON padronizadas.
register_exception_handlers(app)

# Cada controller define seu próprio prefixo de rota (/api/v1/...).
app.include_router(product_controller.router)
app.include_router(review_controller.router)
app.include_router(cart_controller.router)
app.include_router(faq_controller.router)
app.include_router(chat_controller.router)


@app.get("/health")
async def health():
    """Healthcheck simples (usado para verificar se o container está no ar)."""
    return {"status": "ok", "service": "lumen-backend"}
