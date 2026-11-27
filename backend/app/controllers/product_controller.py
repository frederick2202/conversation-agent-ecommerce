"""
Rotas HTTP do catálogo de produtos: /api/v1/products
Inclui leitura pública (vitrine) e CRUD usado pelo painel administrativo.
"""

from typing import Optional
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.embedding_service import EmbeddingService
from app.services.product_service import ProductService

router = APIRouter(prefix="/api/v1/products", tags=["Produtos"])


def get_product_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    """Injeção de dependência do ProductService por requisição."""
    return ProductService(ProductRepository(db), EmbeddingService())


@router.get("", response_model=list[ProductResponse])
async def list_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    service: ProductService = Depends(get_product_service),
):
    """Lista produtos. Query params opcionais: `category` ("Tudo" = todas) e `search` (texto livre)."""
    return await service.list_products(category=category, search=search)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: uuid.UUID, service: ProductService = Depends(get_product_service)):
    return await service.get_product(product_id)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, service: ProductService = Depends(get_product_service)):
    return await service.create_product(payload)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    service: ProductService = Depends(get_product_service),
):
    return await service.update_product(product_id, payload)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: uuid.UUID, service: ProductService = Depends(get_product_service)):
    await service.delete_product(product_id)
