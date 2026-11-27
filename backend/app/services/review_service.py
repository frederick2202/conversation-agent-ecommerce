"""
Regras de negócio das avaliações (reviews) de produtos.
"""

import uuid
from app.core.exceptions import NotFoundException, ValidationDomainException
from app.models.entities import Review
from app.repositories.product_repository import ProductRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewResponse


class ReviewService:
    def __init__(self, review_repo: ReviewRepository, product_repo: ProductRepository):
        self.review_repo = review_repo
        self.product_repo = product_repo

    async def list_reviews(self, product_id: uuid.UUID) -> list[ReviewResponse]:
        """Lista as avaliações de um produto (mais recentes primeiro)."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundException("Produto não encontrado.")
        reviews = await self.review_repo.list_by_product(product_id)
        return [ReviewResponse.model_validate(r) for r in reviews]

    async def create_review(self, product_id: uuid.UUID, payload: ReviewCreate) -> ReviewResponse:
        # RF03: Validar existência do produto e nota estritamente inteira entre 1 e 5
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundException("Não é possível avaliar um produto inexistente.")

        # `bool` é subclasse de `int` em Python, por isso True/False são rejeitados explicitamente.
        if not isinstance(payload.rating, int) or isinstance(payload.rating, bool) or not (1 <= payload.rating <= 5):
            raise ValidationDomainException("A nota da avaliação deve ser um número inteiro entre 1 e 5.")

        # Comentário vazio ou só com espaços é salvo como NULL.
        comment_clean = payload.comment.strip() if payload.comment and payload.comment.strip() else None
        review = Review(
            product_id=product_id,
            author_name=payload.author_name.strip(),
            rating=payload.rating,
            comment=comment_clean,
        )
        saved = await self.review_repo.save(review)
        return ReviewResponse.model_validate(saved)
