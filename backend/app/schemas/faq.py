"""
DTOs (Pydantic) das FAQs.
"""

from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict


class FaqCreate(BaseModel):
    """Corpo de POST /faqs."""

    category: str
    question: str
    answer: str


class FaqUpdate(BaseModel):
    """Corpo de PATCH /faqs/{id}: todos os campos são opcionais (atualização parcial)."""

    category: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None


class FaqResponse(BaseModel):
    """FAQ retornada pela API (o embedding não é exposto)."""

    # Permite criar o DTO diretamente a partir do objeto ORM (`model_validate(entidade)`).
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    category: str
    question: str
    answer: str
    updated_at: datetime
