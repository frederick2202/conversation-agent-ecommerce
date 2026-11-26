import hashlib
import math
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        has_valid_key = bool(settings.gemini_api_key) and not settings.gemini_api_key.startswith("cole-sua-chave")
        self._client = (
            GoogleGenerativeAIEmbeddings(
                google_api_key=settings.gemini_api_key,
                model=settings.gemini_embedding_model,
                output_dimensionality=1536,
            )
            if has_valid_key
            else None
        )

    async def generate_embedding(self, text: str) -> list[float]:
        if self._client:
            try:
                return await self._client.aembed_query(text)
            except Exception as exc:
                print(f"[EMBEDDING FALLBACK] Erro na Gemini API ({exc}). Usando vetor local.")
        # Fallback determinístico local
        dim = 1536
        digest = hashlib.sha256(text.lower().encode("utf-8")).digest()
        raw = [((digest[i % len(digest)] / 255.0) * 2.0 - 1.0) for i in range(dim)]
        norm = math.sqrt(sum(x * x for x in raw)) or 1.0
        return [x / norm for x in raw]