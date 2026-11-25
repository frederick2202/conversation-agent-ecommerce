from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    author_name: str = Field(default="Cliente Lumen", min_length=2, max_length=100)
    rating: int = Field(..., description="Nota inteira estritamente entre 1 e 5")
    comment: Optional[str] = Field(default=None, max_length=1000)


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    product_id: uuid.UUID
    author_name: str
    rating: int
    comment: Optional[str]
    created_at: datetime
