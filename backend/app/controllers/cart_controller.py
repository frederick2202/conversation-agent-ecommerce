import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.cart_repository import CartRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.cart import AddCartItemRequest, CartSummaryResponse, UpdateCartItemRequest
from app.services.cart_service import CartService

router = APIRouter(prefix="/api/v1/cart", tags=["Carrinho"])


def get_cart_service(db: AsyncSession = Depends(get_db)) -> CartService:
    return CartService(CartRepository(db), ProductRepository(db))


@router.get("/{session_id}", response_model=CartSummaryResponse)
async def get_cart(session_id: str, service: CartService = Depends(get_cart_service)):
    return await service.get_cart_summary(session_id)


@router.post("/{session_id}/items", response_model=CartSummaryResponse)
async def add_item(
    session_id: str, payload: AddCartItemRequest, service: CartService = Depends(get_cart_service)
):
    return await service.add_variant_to_cart(session_id, payload.variant_id, payload.quantity)


@router.patch("/{session_id}/items/{item_id}", response_model=CartSummaryResponse)
async def update_item(
    session_id: str,
    item_id: uuid.UUID,
    payload: UpdateCartItemRequest,
    service: CartService = Depends(get_cart_service),
):
    return await service.update_item_quantity(session_id, item_id, payload.quantity)


@router.post("/{session_id}/checkout")
async def checkout(session_id: str, service: CartService = Depends(get_cart_service)):
    return await service.checkout(session_id)
