from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DomainException(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class NotFoundException(DomainException):
    def __init__(self, message: str):
        super().__init__(message=message, status_code=404, code="NOT_FOUND")


class ValidationDomainException(DomainException):
    def __init__(self, message: str):
        super().__init__(message=message, status_code=422, code="BUSINESS_VALIDATION_ERROR")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainException)
    async def domain_exception_handler(_: Request, exc: DomainException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "Erro interno no servidor."}},
        )
