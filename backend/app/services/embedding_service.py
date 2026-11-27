"""
Geração de embeddings (vetores numéricos que representam o significado de um texto).

Os embeddings de produtos e FAQs são gravados no PostgreSQL (pgvector) e comparados por
distância de cosseno para a busca semântica (sugestão de similares e RAG de FAQs).
"""

import hashlib
import math
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        # Só cria o cliente do Gemini se houver uma chave aparentemente válida (não placeholder).
        has_valid_key = bool(settings.gemini_api_key) and not settings.gemini_api_key.startswith("cole-sua-chave")
        self._client = (
            GoogleGenerativeAIEmbeddings(
                google_api_key=settings.gemini_api_key,
                model=settings.gemini_embedding_model,
                # Deve coincidir com a dimensão das colunas Vector(1536) em app/models/entities.py.
                output_dimensionality=1536,
            )
            if has_valid_key
            else None
        )

    async def generate_embedding(self, text: str) -> list[float]:
        """Gera o embedding de `text` (1536 dimensões).

        Usa o Gemini quando disponível. Sem chave ou em caso de erro na API, retorna um vetor
        determinístico derivado do hash SHA-256 do texto — mantém a aplicação funcionando,
        mas SEM significado semântico (textos parecidos não geram vetores próximos).
        """
        if self._client:
            try:
                return await self._client.aembed_query(text)
            except Exception as exc:
                print(f"[EMBEDDING FALLBACK] Erro na Gemini API ({exc}). Usando vetor local.")
        # Fallback determinístico local
        dim = 1536
        digest = hashlib.sha256(text.lower().encode("utf-8")).digest()
        # Repete os 32 bytes do hash até preencher o vetor, mapeando cada byte para [-1, 1].
        raw = [((digest[i % len(digest)] / 255.0) * 2.0 - 1.0) for i in range(dim)]
        # Normaliza para norma 1 (vetor unitário), adequado para distância de cosseno.
        norm = math.sqrt(sum(x * x for x in raw)) or 1.0
        return [x / norm for x in raw]