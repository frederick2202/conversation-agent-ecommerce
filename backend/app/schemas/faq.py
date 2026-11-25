from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict


class FaqCreate(BaseModel):
    category: str
    question: str
    answer: str


class FaqUpdate(BaseModel):
    category: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None


class FaqResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    category: str
    question: str
    answer: str
    updated_at: datetime
