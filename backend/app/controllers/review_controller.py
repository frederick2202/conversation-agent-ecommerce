import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.product_repository import ProductRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewResponse
from app.services.review_service import ReviewService

router = APIRouter(prefix="/api/v1/products/{product_id}/reviews", tags=["Avaliações"])


def get_review_service(db: AsyncSession = Depends(get_db)) -> ReviewService:
    return ReviewService(ReviewRepository(db), ProductRepository(db))


@router.get("", response_model=list[ReviewResponse])
async def list_reviews(product_id: uuid.UUID, service: ReviewService = Depends(get_review_service)):
    return await service.list_reviews(product_id)


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    product_id: uuid.UUID, payload: ReviewCreate, service: ReviewService = Depends(get_review_service)
):
    return await service.create_review(product_id, payload)
