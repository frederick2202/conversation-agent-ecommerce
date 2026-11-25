import hashlib
import math
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        has_valid_key = bool(settings.openai_api_key) and not settings.openai_api_key.startswith("sk-proj-substitua")
        self._client = (
            OpenAIEmbeddings(
                api_key=settings.openai_api_key,
                model=settings.openai_embedding_model,
            )
            if has_valid_key
            else None
        )

    async def generate_embedding(self, text: str) -> list[float]:
        if self._client:
            return await self._client.aembed_query(text)
        # Fallback determinístico local para testes/execução sem chave externa
        dim = 1536
        digest = hashlib.sha256(text.lower().encode("utf-8")).digest()
        raw = [((digest[i % len(digest)] / 255.0) * 2.0 - 1.0) for i in range(dim)]
        norm = math.sqrt(sum(x * x for x in raw)) or 1.0
        return [x / norm for x in raw]
