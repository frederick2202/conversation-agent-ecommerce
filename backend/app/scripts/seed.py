import asyncio
from decimal import Decimal
from sqlalchemy import text

from app.core.database import AsyncSessionLocal, engine
from app.models.entities import Base
from app.repositories.faq_repository import FaqRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.faq import FaqCreate
from app.schemas.product import ProductCreate, VariantCreate
from app.services.embedding_service import EmbeddingService
from app.services.faq_service import FaqService
from app.services.product_service import ProductService

INITIAL_PRODUCTS = [
    ProductCreate(
        sku="LMN-NB-001",
        name="Notebook Gamer Lumen Pulse 16 RTX 4070",
        brand="Lumen Gear",
        category="Notebooks & PCs",
        short_description="Intel Core i7 14ª Gen, RTX 4070 8GB, tela 165Hz QHD e 16GB DDR5.",
        description="Notebook de alta performance com chassi em alumínio, sistema de refrigeração dual-fan e carregamento rápido USB-C.",
        price=Decimal("7499.00"),
        original_price=Decimal("8999.00"),
        discount_percent=17,
        image_url="https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=800",
        specs_tags=["RTX 4070", "165Hz", "Bivolt"],
        required_variation_keys=["cor", "armazenamento"],
        variants=[
            VariantCreate(variant_sku="LMN-NB-001-PR-512", attributes={"cor": "Preto Ônix", "armazenamento": "512GB SSD"}, stock_quantity=8),
            VariantCreate(variant_sku="LMN-NB-001-PR-1TB", attributes={"cor": "Preto Ônix", "armazenamento": "1TB SSD"}, stock_quantity=4, price_override=Decimal("7899.00")),
            VariantCreate(variant_sku="LMN-NB-001-PRATA-1TB", attributes={"cor": "Prata Titânio", "armazenamento": "1TB SSD"}, stock_quantity=0, price_override=Decimal("7899.00")),
        ],
    ),
    ProductCreate(
        sku="LMN-AU-002",
        name="Headset Wireless Sony WH-1000XM5 ANC",
        brand="Sony",
        category="Áudio & Fones",
        short_description="Cancelamento de ruído líder de mercado, 30h de bateria e áudio Hi-Res.",
        description="Oito microfones integrados, conexão multiponto Bluetooth 5.2 e estojo rígido de transporte.",
        price=Decimal("1899.00"),
        original_price=Decimal("2499.00"),
        discount_percent=24,
        image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800",
        specs_tags=["ANC Pro", "30h Bateria", "Bluetooth 5.2"],
        required_variation_keys=["cor"],
        variants=[
            VariantCreate(variant_sku="LMN-AU-002-PR", attributes={"cor": "Preto"}, stock_quantity=15),
            VariantCreate(variant_sku="LMN-AU-002-BG", attributes={"cor": "Prata Platina"}, stock_quantity=6),
        ],
    ),
    ProductCreate(
        sku="LMN-MN-003",
        name='Monitor Gamer Curvo Odyssey 27" 165Hz QHD',
        brand="Samsung",
        category="Monitores",
        short_description="Painel VA curvo 1000R, 1ms MPRT, HDR10 e AMD FreeSync Premium.",
        description="Imersão total para jogos competitivos e edição de vídeo com ajuste ergonômico de inclinação.",
        price=Decimal("1349.00"),
        original_price=Decimal("1999.00"),
        discount_percent=33,
        image_url="https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=800",
        specs_tags=["165Hz", "QHD 1440p", "FreeSync"],
        required_variation_keys=["voltagem"],
        variants=[
            VariantCreate(variant_sku="LMN-MN-003-BV", attributes={"voltagem": "Bivolt"}, stock_quantity=12),
        ],
    ),
    ProductCreate(
        sku="LMN-PR-004",
        name="Teclado Mecânico Keychron K2 Pro QMK/VIA",
        brand="Keychron",
        category="Periféricos",
        short_description="Layout 75%, Bluetooth/USB-C, hot-swappable e keycaps PBT double-shot.",
        description="Compatível com Windows e macOS, com espuma acústica interna e retroiluminação RGB programável.",
        price=Decimal("649.00"),
        original_price=Decimal("849.00"),
        discount_percent=24,
        image_url="https://images.unsplash.com/photo-1595225476474-87563907a212?w=800",
        specs_tags=["75%", "Hot-Swap", "RGB"],
        required_variation_keys=["cor", "switch"],
        variants=[
            VariantCreate(variant_sku="LMN-PR-004-PR-BR", attributes={"cor": "Preto", "switch": "Brown Tátil"}, stock_quantity=10),
            VariantCreate(variant_sku="LMN-PR-004-PR-RD", attributes={"cor": "Preto", "switch": "Red Linear"}, stock_quantity=7),
        ],
    ),
    ProductCreate(
        sku="LMN-SM-005",
        name="Smartphone Galaxy S25 Ultra 5G",
        brand="Samsung",
        category="Smartphones",
        short_description='Tela AMOLED 6.8" 120Hz, câmera 200MP, S-Pen integrada e bateria 5000mAh.',
        description="Construção em titânio com proteção IP68 e recursos nativos de IA embarcada.",
        price=Decimal("6299.00"),
        original_price=Decimal("7999.00"),
        discount_percent=21,
        image_url="https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=800",
        specs_tags=["5G", "200MP", "IP68"],
        required_variation_keys=["cor", "armazenamento"],
        variants=[
            VariantCreate(variant_sku="LMN-SM-005-TT-256", attributes={"cor": "Titânio Cinza", "armazenamento": "256GB"}, stock_quantity=9),
            VariantCreate(variant_sku="LMN-SM-005-PR-512", attributes={"cor": "Titânio Preto", "armazenamento": "512GB"}, stock_quantity=3, price_override=Decimal("6899.00")),
        ],
    ),
    ProductCreate(
        sku="LMN-PR-006",
        name="Mouse Gamer Logitech G Pro X Superlight 2",
        brand="Logitech",
        category="Periféricos",
        short_description="Sensor HERO 2 de 32.000 DPI, switches híbridos LIGHTFORCE e apenas 60g.",
        description="Desenvolvido com atletas de esports, autonomia de 95 horas e recarga USB-C.",
        price=Decimal("799.00"),
        original_price=Decimal("999.00"),
        discount_percent=20,
        image_url="https://images.unsplash.com/photo-1527814050087-3793815479db?w=800",
        specs_tags=["60g", "32K DPI", "Wireless"],
        required_variation_keys=["cor"],
        variants=[
            VariantCreate(variant_sku="LMN-PR-006-PR", attributes={"cor": "Preto"}, stock_quantity=14),
            VariantCreate(variant_sku="LMN-PR-006-BR", attributes={"cor": "Branco"}, stock_quantity=5),
        ],
    ),
]

INITIAL_FAQS = [
    FaqCreate(
        category="Trocas e Devoluções",
        question="Qual é a política de troca e devolução da Lumen?",
        answer="Você tem até 7 dias corridos após o recebimento para devolução por arrependimento (CDC) com frete reverso gratuito, e até 30 dias para troca em caso de defeito de fabricação direto com a Lumen.",
    ),
    FaqCreate(
        category="Frete e Entrega",
        question="Quais são os prazos e condições de frete grátis?",
        answer="Oferecemos frete grátis para todo o Brasil em compras acima de R$ 499,00. O envio expresso para capitais e Sudeste leva de 1 a 3 dias úteis após a confirmação do pagamento.",
    ),
    FaqCreate(
        category="Garantia e Pagamento",
        question="Os eletrônicos possuem nota fiscal e garantia? Como posso pagar?",
        answer="Todos os produtos acompanham Nota Fiscal eletrônica (NF-e) e garantia mínima de 12 meses. Aceitamos Pix com 5% de desconto imediato e cartão de crédito em até 10x sem juros.",
    ),
]


async def run_seed() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    embedding_service = EmbeddingService()
    async with AsyncSessionLocal() as session:
        product_service = ProductService(ProductRepository(session), embedding_service)
        faq_service = FaqService(FaqRepository(session), embedding_service)

        existing_products = await product_service.list_products()
        if not existing_products:
            for item in INITIAL_PRODUCTS:
                await product_service.create_product(item)
            print(f"[SEED] {len(INITIAL_PRODUCTS)} produtos indexados com pgvector.")

        existing_faqs = await faq_service.list_faqs()
        if not existing_faqs:
            for faq in INITIAL_FAQS:
                await faq_service.create_faq(faq)
            print(f"[SEED] {len(INITIAL_FAQS)} FAQs indexadas com pgvector.")


if __name__ == "__main__":
    asyncio.run(run_seed())
