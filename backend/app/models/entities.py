"""
Modelos ORM (SQLAlchemy 2.x) que representam as tabelas do PostgreSQL.

Visão geral do modelo de dados:
    Product 1──N ProductVariant   (cada combinação de cor/armazenamento/etc. tem estoque próprio)
    Product 1──N Review           (avaliações de clientes, nota 1..5)
    Cart    1──N CartItem N──1 ProductVariant   (carrinho identificado por session_id, sem login)
    Faq                           (perguntas frequentes usadas pelo agente via RAG)
    ChatMessage                   (histórico da conversa com o agente, por session_id)

`Product.embedding` e `Faq.embedding` são vetores (pgvector) usados na busca semântica.
As tabelas são criadas automaticamente no startup (veja `app/main.py`).
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Classe base de todos os modelos; `Base.metadata` contém o schema completo."""

    pass


class Product(Base):
    """Produto do catálogo. Preço e estoque efetivos ficam nas variações (`variants`)."""

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)  # Código único, ex.: "LMN-NB-001".
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    brand: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    short_description: Mapped[str] = mapped_column(String(320), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)  # Preço base (pode ser sobrescrito pela variação).
    original_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)  # Preço "de" (antes do desconto).
    discount_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    specs_tags: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)  # Destaques exibidos como "chips".
    # Atributos que o cliente DEVE escolher antes de comprar (ex.: ["cor", "armazenamento"]).
    # São as chaves esperadas em `ProductVariant.attributes`.
    required_variation_keys: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    # Embedding (1536 dimensões) do texto do produto, usado para sugerir similares via distância de cosseno.
    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(1536), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # `lazy="selectin"` carrega os relacionamentos com uma query extra automática,
    # evitando lazy-load implícito (que não funciona em sessões assíncronas).
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", lazy="selectin"
    )
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", lazy="selectin"
    )


class ProductVariant(Base):
    """Variação comprável de um produto (ex.: cor Preta + 512GB), com estoque e preço próprios."""

    __tablename__ = "product_variants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    variant_sku: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    attributes: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)  # Ex.: {"cor": "Preto", "armazenamento": "512GB"}.
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Quando preenchido, substitui `Product.price` para esta variação.
    price_override: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    product: Mapped["Product"] = relationship(back_populates="variants")


class Review(Base):
    """Avaliação de um produto. A nota é garantida entre 1 e 5 também no nível do banco."""

    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    author_name: Mapped[str] = mapped_column(String(100), default="Cliente Lumen", nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="reviews")


class Cart(Base):
    """Carrinho de compras. Não há usuários/login: o carrinho é identificado pelo
    `session_id` gerado e persistido no navegador pelo frontend."""

    __tablename__ = "carts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan", lazy="selectin"
    )


class CartItem(Base):
    """Linha do carrinho: uma variação + quantidade. A mesma variação não se repete no
    mesmo carrinho (constraint `uq_cart_variant`); adicionar de novo soma a quantidade."""

    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "variant_id", name="uq_cart_variant"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("carts.id", ondelete="CASCADE"), nullable=False
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    cart: Mapped["Cart"] = relationship(back_populates="items")
    variant: Mapped["ProductVariant"] = relationship(lazy="selectin")


class Faq(Base):
    """Pergunta frequente / política da loja. É a base de conhecimento consultada pelo
    agente (RAG) através de busca semântica no campo `embedding`."""

    __tablename__ = "faqs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    question: Mapped[str] = mapped_column(String(300), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(1536), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ChatMessage(Base):
    """Mensagem do histórico de conversa com o agente de IA."""

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" ou "assistant".
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Ações de interface geradas pelas ferramentas do agente (ex.: SELECT_VARIANT, CART_UPDATED),
    # salvas para que o frontend possa redesenhar botões/cards ao recarregar o histórico.
    ui_actions: Mapped[Optional[list[dict]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
