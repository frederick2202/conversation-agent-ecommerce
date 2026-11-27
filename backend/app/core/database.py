"""
Configuração da conexão assíncrona com o PostgreSQL (SQLAlchemy 2.x + asyncpg).
"""

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

# Engine compartilhado por toda a aplicação. `pool_pre_ping` testa a conexão antes de usá-la,
# evitando erros com conexões que o banco já fechou.
engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
# Fábrica de sessões. `expire_on_commit=False` mantém os atributos dos objetos acessíveis
# após o commit (importante em código assíncrono, onde lazy-load implícito não é permitido).
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependência do FastAPI: abre uma sessão por requisição e a fecha ao final."""
    async with AsyncSessionLocal() as session:
        yield session
