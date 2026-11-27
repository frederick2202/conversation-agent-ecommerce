"""
Exceções de domínio e seus tratadores HTTP.

Os services lançam estas exceções quando uma regra de negócio é violada; os
handlers registrados em `register_exception_handlers` as convertem em respostas
JSON no formato: {"error": {"code": "...", "message": "..."}}.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DomainException(Exception):
    """Erro de negócio genérico (HTTP 400 por padrão). Base das demais exceções."""

    def __init__(self, message: str, status_code: int = 400, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class NotFoundException(DomainException):
    """Recurso inexistente (HTTP 404)."""

    def __init__(self, message: str):
        super().__init__(message=message, status_code=404, code="NOT_FOUND")


class ValidationDomainException(DomainException):
    """Violação de regra de negócio, ex.: estoque insuficiente ou nota inválida (HTTP 422)."""

    def __init__(self, message: str):
        super().__init__(message=message, status_code=422, code="BUSINESS_VALIDATION_ERROR")


def register_exception_handlers(app: FastAPI) -> None:
    """Registra os tratadores globais de exceção na aplicação FastAPI."""

    @app.exception_handler(DomainException)
    async def domain_exception_handler(_: Request, exc: DomainException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    # Qualquer erro não previsto vira 500 com mensagem genérica (não expõe detalhes internos ao cliente).
    @app.exception_handler(Exception)
    async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "Erro interno no servidor."}},
        )
