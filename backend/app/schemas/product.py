from decimal import Decimal
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class VariantCreate(BaseModel):
    variant_sku: str
    attributes: dict[str, str]
    stock_quantity: int = Field(ge=0)
    price_override: Optional[Decimal] = None


class VariantResponse(VariantCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class ProductCreate(BaseModel):
    sku: str
    name: str
    brand: str
    category: str
    short_description: str
    description: str
    price: Decimal = Field(gt=0)
    original_price: Optional[Decimal] = None
    discount_percent: int = Field(default=0, ge=0, le=95)
    image_url: str
    specs_tags: list[str] = Field(default_factory=list)
    required_variation_keys: list[str] = Field(default_factory=list)
    variants: list[VariantCreate] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, gt=0)
    original_price: Optional[Decimal] = None
    discount_percent: Optional[int] = Field(default=None, ge=0, le=95)
    image_url: Optional[str] = None
    specs_tags: Optional[list[str]] = None
    required_variation_keys: Optional[list[str]] = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sku: str
    name: str
    brand: str
    category: str
    short_description: str
    description: str
    price: Decimal
    original_price: Optional[Decimal]
    discount_percent: int
    image_url: str
    specs_tags: list[str]
    required_variation_keys: list[str]
    variants: list[VariantResponse]
    total_stock: int = 0
    average_rating: float = 0.0
    review_count: int = 0
