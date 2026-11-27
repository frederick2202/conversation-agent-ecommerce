"""
Regras de negócio do catálogo de produtos: listagem, busca (exata e semântica) e CRUD.
Também converte entidades ORM em `ProductResponse`, calculando campos derivados.
"""

from typing import Optional
import uuid

from app.core.exceptions import NotFoundException, ValidationDomainException
from app.models.entities import Product, ProductVariant
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate, VariantResponse
from app.services.embedding_service import EmbeddingService


class ProductService:
    def __init__(self, repo: ProductRepository, embedding_service: EmbeddingService):
        self.repo = repo
        self.embedding_service = embedding_service

    def _build_embedding_text(self, product: Product) -> str:
        """Texto que descreve o produto para gerar o embedding usado na busca semântica."""
        tags = ", ".join(product.specs_tags or [])
        return (
            f"SKU: {product.sku}. Nome: {product.name}. Marca: {product.brand}. "
            f"Categoria: {product.category}. Resumo: {product.short_description}. "
            f"Especificações: {tags}. Detalhes: {product.description}"
        )

    def _to_response(self, product: Product) -> ProductResponse:
        """Converte a entidade em DTO, calculando estoque total e média/quantidade de avaliações."""
        total_stock = sum(v.stock_quantity for v in product.variants)
        review_count = len(product.reviews)
        avg_rating = (
            round(sum(r.rating for r in product.reviews) / review_count, 1)
            if review_count > 0
            else 0.0
        )
        return ProductResponse(
            id=product.id,
            sku=product.sku,
            name=product.name,
            brand=product.brand,
            category=product.category,
            short_description=product.short_description,
            description=product.description,
            price=product.price,
            original_price=product.original_price,
            discount_percent=product.discount_percent,
            image_url=product.image_url,
            specs_tags=product.specs_tags,
            required_variation_keys=product.required_variation_keys,
            variants=[VariantResponse.model_validate(v) for v in product.variants],
            total_stock=total_stock,
            average_rating=avg_rating,
            review_count=review_count,
        )

    async def list_products(self, category: Optional[str] = None, search: Optional[str] = None) -> list[ProductResponse]:
        """Lista produtos, opcionalmente filtrando por categoria e/ou texto livre."""
        products = await self.repo.list_all(category=category, search=search)
        return [self._to_response(p) for p in products]

    async def get_product(self, product_id: uuid.UUID) -> ProductResponse:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise NotFoundException("Produto não encontrado.")
        return self._to_response(product)

    async def find_product_for_chat(self, query: str) -> Optional[ProductResponse]:
        """Busca um único produto por SKU exato ou trecho do nome (usado pelas ferramentas do agente)."""
        product = await self.repo.find_by_name_or_sku(query)
        return self._to_response(product) if product else None

    async def suggest_similar_products(self, query: str, limit: int = 3) -> list[ProductResponse]:
        """Busca semântica: retorna os produtos cujo embedding é mais próximo do texto informado."""
        vector = await self.embedding_service.generate_embedding(query)
        products = await self.repo.semantic_search(vector, limit=limit)
        return [self._to_response(p) for p in products]

    async def create_product(self, payload: ProductCreate) -> ProductResponse:
        """Cria um produto com suas variações e gera o embedding. SKUs são salvos em maiúsculas."""
        # `find_by_name_or_sku` também casa por nome, por isso confirmamos que o SKU é de fato igual.
        existing = await self.repo.find_by_name_or_sku(payload.sku)
        if existing and existing.sku.lower() == payload.sku.lower():
            raise ValidationDomainException(f"Já existe um produto com o SKU {payload.sku}.")

        product = Product(
            sku=payload.sku.upper(),
            name=payload.name,
            brand=payload.brand,
            category=payload.category,
            short_description=payload.short_description,
            description=payload.description,
            price=payload.price,
            original_price=payload.original_price,
            discount_percent=payload.discount_percent,
            image_url=payload.image_url,
            specs_tags=payload.specs_tags,
            required_variation_keys=payload.required_variation_keys,
            variants=[
                ProductVariant(
                    variant_sku=v.variant_sku.upper(),
                    attributes=v.attributes,
                    stock_quantity=v.stock_quantity,
                    price_override=v.price_override,
                )
                for v in payload.variants
            ],
        )
        # RF04: Reindexação automática no pgvector
        product.embedding = await self.embedding_service.generate_embedding(self._build_embedding_text(product))
        saved = await self.repo.save(product)
        return self._to_response(saved)

    async def update_product(self, product_id: uuid.UUID, payload: ProductUpdate) -> ProductResponse:
        """Atualização parcial (PATCH) dos dados do produto. Variações não são alteradas aqui."""
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise NotFoundException("Produto não encontrado.")

        # Aplica somente os campos efetivamente enviados na requisição.
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(product, field, value)

        # RF04: Atualiza embedding imediatamente após edição
        product.embedding = await self.embedding_service.generate_embedding(self._build_embedding_text(product))
        saved = await self.repo.save(product)
        return self._to_response(saved)

    async def delete_product(self, product_id: uuid.UUID) -> None:
        """Remove o produto (variações e avaliações são removidas em cascata)."""
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise NotFoundException("Produto não encontrado.")
        await self.repo.delete(product)
