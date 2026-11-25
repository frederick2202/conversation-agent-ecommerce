from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.controllers import (
    cart_controller,
    chat_controller,
    faq_controller,
    product_controller,
    review_controller,
)
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.models.entities import Base


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Lumen E-Commerce & AI Agent API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(product_controller.router)
app.include_router(review_controller.router)
app.include_router(cart_controller.router)
app.include_router(faq_controller.router)
app.include_router(chat_controller.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "lumen-backend"}
