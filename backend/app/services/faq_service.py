"""
Regras de negócio das FAQs (base de conhecimento do agente).
Toda criação/edição recalcula o embedding para que a busca semântica (RAG) fique atualizada.
"""

import uuid
from app.core.exceptions import NotFoundException
from app.models.entities import Faq
from app.repositories.faq_repository import FaqRepository
from app.schemas.faq import FaqCreate, FaqResponse, FaqUpdate
from app.services.embedding_service import EmbeddingService


class FaqService:
    def __init__(self, repo: FaqRepository, embedding_service: EmbeddingService):
        self.repo = repo
        self.embedding_service = embedding_service

    def _build_embedding_text(self, category: str, question: str, answer: str) -> str:
        """Texto que representa a FAQ para gerar o embedding (combina categoria, pergunta e resposta)."""
        return f"Categoria: {category}. Pergunta: {question}. Resposta: {answer}"

    async def list_faqs(self) -> list[FaqResponse]:
        return [FaqResponse.model_validate(f) for f in await self.repo.list_all()]

    async def create_faq(self, payload: FaqCreate) -> FaqResponse:
        embedding = await self.embedding_service.generate_embedding(
            self._build_embedding_text(payload.category, payload.question, payload.answer)
        )
        faq = Faq(
            category=payload.category,
            question=payload.question,
            answer=payload.answer,
            embedding=embedding,
        )
        return FaqResponse.model_validate(await self.repo.save(faq))

    async def update_faq(self, faq_id: uuid.UUID, payload: FaqUpdate) -> FaqResponse:
        faq = await self.repo.get_by_id(faq_id)
        if not faq:
            raise NotFoundException("FAQ não encontrada.")

        # Atualização parcial (PATCH): aplica só os campos enviados na requisição.
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(faq, field, value)

        # RF04: Reindexação imediata no pgvector
        faq.embedding = await self.embedding_service.generate_embedding(
            self._build_embedding_text(faq.category, faq.question, faq.answer)
        )
        return FaqResponse.model_validate(await self.repo.save(faq))

    async def delete_faq(self, faq_id: uuid.UUID) -> None:
        faq = await self.repo.get_by_id(faq_id)
        if not faq:
            raise NotFoundException("FAQ não encontrada.")
        await self.repo.delete(faq)

    async def search_faqs(self, query: str, limit: int = 3) -> list[FaqResponse]:
        """Busca semântica: retorna as `limit` FAQs mais próximas da pergunta (usada pelo agente)."""
        vector = await self.embedding_service.generate_embedding(query)
        faqs = await self.repo.semantic_search(vector, limit=limit)
        return [FaqResponse.model_validate(f) for f in faqs]
