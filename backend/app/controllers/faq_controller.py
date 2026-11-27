"""
Rotas HTTP de administração das FAQs: /api/v1/faqs
Criar/editar uma FAQ reindexa automaticamente seu embedding para a busca do agente.
"""

import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.faq_repository import FaqRepository
from app.schemas.faq import FaqCreate, FaqResponse, FaqUpdate
from app.services.embedding_service import EmbeddingService
from app.services.faq_service import FaqService

router = APIRouter(prefix="/api/v1/faqs", tags=["FAQs"])


def get_faq_service(db: AsyncSession = Depends(get_db)) -> FaqService:
    """Injeção de dependência do FaqService por requisição."""
    return FaqService(FaqRepository(db), EmbeddingService())


@router.get("", response_model=list[FaqResponse])
async def list_faqs(service: FaqService = Depends(get_faq_service)):
    return await service.list_faqs()


@router.post("", response_model=FaqResponse, status_code=status.HTTP_201_CREATED)
async def create_faq(payload: FaqCreate, service: FaqService = Depends(get_faq_service)):
    return await service.create_faq(payload)


@router.patch("/{faq_id}", response_model=FaqResponse)
async def update_faq(
    faq_id: uuid.UUID, payload: FaqUpdate, service: FaqService = Depends(get_faq_service)
):
    return await service.update_faq(faq_id, payload)


@router.delete("/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faq(faq_id: uuid.UUID, service: FaqService = Depends(get_faq_service)):
    await service.delete_faq(faq_id)
