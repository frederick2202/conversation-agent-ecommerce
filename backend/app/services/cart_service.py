"""
Regras de negócio do carrinho de compras (adicionar, alterar quantidade, resumo e checkout).
O carrinho é identificado por `session_id` (sem login de usuário).
"""

from decimal import Decimal
import uuid

from app.core.exceptions import NotFoundException, ValidationDomainException
from app.models.entities import CartItem
from app.repositories.cart_repository import CartRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.cart import CartItemDetail, CartSummaryResponse


class CartService:
    def __init__(self, cart_repo: CartRepository, product_repo: ProductRepository):
        self.cart_repo = cart_repo
        self.product_repo = product_repo

    async def get_cart_summary(self, session_id: str) -> CartSummaryResponse:
        """Retorna os itens do carrinho com preços calculados, total de unidades e subtotal.

        Cria um carrinho vazio se a sessão ainda não tiver um.
        """
        cart = await self.cart_repo.get_or_create_by_session(session_id)
        details: list[CartItemDetail] = []
        subtotal = Decimal("0.00")
        total_items = 0

        for item in cart.items:
            variant = item.variant
            product = variant.product
            # Preço sempre calculado na hora (não é congelado no item): reflete alterações do catálogo.
            unit_price = variant.price_override or product.price
            line_total = unit_price * item.quantity
            subtotal += line_total
            total_items += item.quantity
            details.append(
                CartItemDetail(
                    item_id=item.id,
                    product_id=product.id,
                    variant_id=variant.id,
                    sku=variant.variant_sku,
                    product_name=product.name,
                    image_url=product.image_url,
                    attributes=variant.attributes,
                    unit_price=unit_price,
                    quantity=item.quantity,
                    line_total=line_total,
                )
            )
        return CartSummaryResponse(
            session_id=session_id,
            items=details,
            total_items=total_items,
            subtotal=subtotal,
        )

    async def add_variant_to_cart(
        self, session_id: str, variant_id: uuid.UUID, quantity: int = 1
    ) -> CartSummaryResponse:
        """Adiciona `quantity` unidades de uma variação ao carrinho.

        Se a variação já estiver no carrinho, soma à quantidade existente. Valida o estoque
        considerando o total desejado (existente + novo). Retorna o resumo atualizado.

        Raises:
            ValidationDomainException: quantidade < 1 ou estoque insuficiente.
            NotFoundException: variação inexistente.
        """
        if quantity < 1:
            raise ValidationDomainException("A quantidade mínima para adicionar ao carrinho é 1.")

        variant = await self.product_repo.get_variant_by_id(variant_id)
        if not variant:
            raise NotFoundException("Variação de produto não encontrada.")

        cart = await self.cart_repo.get_or_create_by_session(session_id)
        existing_item = await self.cart_repo.get_item(cart.id, variant_id)
        desired_qty = (existing_item.quantity if existing_item else 0) + quantity

        if variant.stock_quantity < desired_qty:
            raise ValidationDomainException(
                f"Estoque insuficiente para {variant.product.name} ({variant.attributes}). "
                f"Disponível: {variant.stock_quantity} unidade(s)."
            )

        if existing_item:
            existing_item.quantity = desired_qty
            await self.cart_repo.save_item(existing_item)
        else:
            await self.cart_repo.save_item(
                CartItem(cart_id=cart.id, variant_id=variant_id, quantity=quantity)
            )

        return await self.get_cart_summary(session_id)

    async def update_item_quantity(
        self, session_id: str, item_id: uuid.UUID, quantity: int
    ) -> CartSummaryResponse:
        """Define a quantidade de um item do carrinho; quantidade <= 0 remove o item.

        Observação: o `session_id` é usado apenas para montar o resumo de retorno; a busca
        do item é feita somente por `item_id`.
        """
        item = await self.cart_repo.get_item_by_id(item_id)
        if not item:
            raise NotFoundException("Item não encontrado no carrinho.")

        if quantity <= 0:
            await self.cart_repo.delete_item(item)
        else:
            if item.variant.stock_quantity < quantity:
                raise ValidationDomainException(
                    f"Estoque máximo disponível: {item.variant.stock_quantity} unidade(s)."
                )
            item.quantity = quantity
            await self.cart_repo.save_item(item)

        return await self.get_cart_summary(session_id)

    async def checkout(self, session_id: str) -> dict:
        """Finaliza a compra de forma SIMULADA: gera um código de pedido e esvazia o carrinho.

        Não há integração com pagamento, nem baixa de estoque ou persistência de pedido.
        """
        summary = await self.get_cart_summary(session_id)
        if summary.total_items == 0:
            raise ValidationDomainException("Seu carrinho está vazio.")
        cart = await self.cart_repo.get_or_create_by_session(session_id)
        order_code = f"LMN-{str(uuid.uuid4())[:8].upper()}"
        await self.cart_repo.clear_cart(cart)
        return {
            "order_code": order_code,
            "total_paid": summary.subtotal,
            "items_count": summary.total_items,
            "message": "Pedido confirmado com sucesso! Nota fiscal enviada por e-mail.",
        }
