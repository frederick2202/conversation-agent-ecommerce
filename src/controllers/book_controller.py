from typing import Dict, Any
from src.services.book_service import (
    BookService,
    DuplicateBookError,
    BookNotFoundError,
    BookServiceError,
)


class BookController:
    """
    Camada de Controller:
    Responsável apenas por receber as requisições (do agente conversacional, API ou CLI),
    repassar as chamadas para a camada de serviço (BookService) e formatar a resposta.

    IMPORTANTE:
    Conforme as diretrizes arquiteturais, esta classe NÃO CONTÉM REGRAS DE NEGÓCIO.
    Todas as regras e validações pertencem à camada de Service/Model.
    """

    def __init__(self, service: BookService):
        self.service = service

    def create_book(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recebe o payload com os dados do livro e delega o cadastro ao BookService.
        """
        try:
            book = self.service.register_book(
                titulo=payload.get("titulo", ""),
                autor=payload.get("autor", ""),
                isbn=payload.get("isbn", ""),
                ano_publicacao=payload.get("ano_publicacao"),
                genero=payload.get("genero", ""),
                quantidade_exemplares=payload.get("quantidade_exemplares", 1)
            )
            return {
                "status": "success",
                "message": "Livro cadastrado com sucesso no acervo!",
                "data": book.to_dict()
            }
        except DuplicateBookError as e:
            return {
                "status": "duplicate",
                "message": str(e),
                "existing_book": e.existing_book.to_dict()
            }
        except (BookServiceError, ValueError) as e:
            return {
                "status": "error",
                "message": str(e)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro interno inesperado: {str(e)}"
            }

    def add_copies(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recebe a solicitação para adicionar exemplares a um livro existente e delega ao BookService.
        """
        try:
            isbn = payload.get("isbn", "")
            copies = payload.get("quantidade_exemplares", 1)
            book = self.service.increment_book_copies(isbn, copies)
            return {
                "status": "success",
                "message": f"Exemplares adicionados com sucesso! Total atual: {book.quantidade_exemplares}.",
                "data": book.to_dict()
            }
        except BookNotFoundError as e:
            return {
                "status": "not_found",
                "message": str(e)
            }
        except (BookServiceError, ValueError) as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def get_by_isbn(self, isbn: str) -> Dict[str, Any]:
        """
        Delega a consulta de livro por ISBN ao BookService.
        """
        book = self.service.get_book_by_isbn(isbn)
        if not book:
            return {
                "status": "not_found",
                "message": f"Livro com ISBN '{isbn}' não encontrado no acervo."
            }
        return {
            "status": "success",
            "data": book.to_dict()
        }

    def list_all(self) -> Dict[str, Any]:
        """
        Delega a listagem de todos os livros ao BookService.
        """
        books = self.service.list_catalog()
        return {
            "status": "success",
            "count": len(books),
            "data": [b.to_dict() for b in books]
        }
