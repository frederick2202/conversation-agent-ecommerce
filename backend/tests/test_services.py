from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
import uuid
import pytest

from app.core.exceptions import NotFoundException, ValidationDomainException
from app.schemas.faq import FaqCreate
from app.schemas.review import ReviewCreate
from app.services.cart_service import CartService
from app.services.faq_service import FaqService
from app.services.product_service import ProductService
from app.services.review_service import ReviewService


@pytest.mark.asyncio
async def test_review_rejeita_nota_fora_do_intervalo():
    product_id = uuid.uuid4()
    product_repo = AsyncMock()
    product_repo.get_by_id.return_value = SimpleNamespace(id=product_id)
    review_repo = AsyncMock()

    service = ReviewService(review_repo, product_repo)

    with pytest.raises(ValidationDomainException):
        await service.create_review(product_id, ReviewCreate(author_name="Ana", rating=6, comment="Excelente"))

    with pytest.raises(ValidationDomainException):
        await service.create_review(product_id, ReviewCreate(author_name="Ana", rating=0))


@pytest.mark.asyncio
async def test_review_rejeita_produto_inexistente():
    product_repo = AsyncMock()
    product_repo.get_by_id.return_value = None
    review_repo = AsyncMock()

    service = ReviewService(review_repo, product_repo)
    with pytest.raises(NotFoundException):
        await service.create_review(uuid.uuid4(), ReviewCreate(author_name="Lucas", rating=5))


@pytest.mark.asyncio
async def test_review_aceita_comentario_opcional():
    product_id = uuid.uuid4()
    product_repo = AsyncMock()
    product_repo.get_by_id.return_value = SimpleNamespace(id=product_id)
    review_repo = AsyncMock()
    review_repo.save.side_effect = lambda r: SimpleNamespace(
        id=uuid.uuid4(),
        product_id=r.product_id,
        author_name=r.author_name,
        rating=r.rating,
        comment=r.comment,
        created_at=datetime.now(timezone.utc),
    )

    service = ReviewService(review_repo, product_repo)
    result = await service.create_review(product_id, ReviewCreate(author_name="Carlos", rating=4, comment=None))
    assert result.rating == 4
    assert result.comment is None


@pytest.mark.asyncio
async def test_carrinho_bloqueia_quando_estoque_insuficiente():
    variant_id = uuid.uuid4()
    product_repo = AsyncMock()
    product_repo.get_variant_by_id.return_value = SimpleNamespace(
        id=variant_id,
        stock_quantity=2,
        attributes={"cor": "Preto"},
        product=SimpleNamespace(name="Headset Sony", price=Decimal("1899.00")),
    )
    cart_repo = AsyncMock()
    cart_repo.get_or_create_by_session.return_value = SimpleNamespace(id=uuid.uuid4(), items=[])
    cart_repo.get_item.return_value = None

    service = CartService(cart_repo, product_repo)
    with pytest.raises(ValidationDomainException, match="Estoque insuficiente"):
        await service.add_variant_to_cart("sess-123", variant_id, quantity=5)


@pytest.mark.asyncio
async def test_busca_semantica_retorna_similares_quando_solicitado():
    product_repo = AsyncMock()
    product_repo.semantic_search.return_value = [
        SimpleNamespace(
            id=uuid.uuid4(),
            sku="LMN-AU-002",
            name="Headset Sony WH-1000XM5",
            brand="Sony",
            category="Áudio & Fones",
            short_description="ANC Pro",
            description="Detalhes",
            price=Decimal("1899.00"),
            original_price=None,
            discount_percent=20,
            image_url="https://example.com/img.jpg",
            specs_tags=["ANC"],
            required_variation_keys=["cor"],
            variants=[],
            reviews=[],
        )
    ]
    emb_service = AsyncMock()
    emb_service.generate_embedding.return_value = [0.05] * 1536

    service = ProductService(product_repo, emb_service)
    similares = await service.suggest_similar_products("fone bluetooth cancelamento ruído")
    assert len(similares) == 1
    assert similares[0].sku == "LMN-AU-002"
    emb_service.generate_embedding.assert_awaited_once()


@pytest.mark.asyncio
async def test_faq_reindexa_embedding_automaticamente_ao_criar():
    faq_repo = AsyncMock()
    faq_repo.save.side_effect = lambda f: SimpleNamespace(
        id=uuid.uuid4(),
        category=f.category,
        question=f.question,
        answer=f.answer,
        updated_at=datetime.now(timezone.utc),
    )
    emb_service = AsyncMock()
    emb_service.generate_embedding.return_value = [0.1] * 1536

    service = FaqService(faq_repo, emb_service)
    await service.create_faq(FaqCreate(category="Frete", question="Prazo?", answer="2 dias úteis."))

    emb_service.generate_embedding.assert_awaited_once()
    saved_entity = faq_repo.save.call_args[0][0]
    assert len(saved_entity.embedding) == 1536
