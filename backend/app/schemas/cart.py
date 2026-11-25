from decimal import Decimal
import uuid
from pydantic import BaseModel, Field


class AddCartItemRequest(BaseModel):
    variant_id: uuid.UUID
    quantity: int = Field(default=1, ge=1, le=20)


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(ge=0, le=20)


class CartItemDetail(BaseModel):
    item_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID
    sku: str
    product_name: str
    image_url: str
    attributes: dict[str, str]
    unit_price: Decimal
    quantity: int
    line_total: Decimal


class CartSummaryResponse(BaseModel):
    session_id: str
    items: list[CartItemDetail]
    total_items: int
    subtotal: Decimal
