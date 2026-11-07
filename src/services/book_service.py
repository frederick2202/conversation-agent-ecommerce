from typing import List, Optional, Dict, Any
from src.models.book import Book, BookValidationError, normalize_isbn
from src.repositories.book_repository import BookRepositoryInterface


class BookServiceError(Exception):
    """Exceção base para erros na camada de serviço."""
    pass


class DuplicateBookError(BookServiceError):
    """Exceção levantada quando um livro com o mesmo ISBN já existe."""
    def __init__(self, message: str, existing_book: Book):
        super().__init__(message)
        self.existing_book = existing_book


class BookNotFoundError(BookServiceError):
    """Exceção levantada quando um livro procurado não é encontrado."""
    pass


class BookService:
    """
    Camada de Serviço responsável pelas Regras de Negócio do Acervo de Livros.
    Isola a lógica de negócio do Controller e a persistência do Repository.
    """

    def __init__(self, repository: BookRepositoryInterface):
        self.repository = repository

    def register_book(
        self,
        titulo: str,
        autor: str,
        isbn: str,
        ano_publicacao: int,
        genero: str,
        quantidade_exemplares: int = 1
    ) -> Book:
        """
        Regra de Negócio:
        1. Normaliza o ISBN.
        2. Verifica se o ISBN já existe no acervo.
           - Se existir, levanta DuplicateBookError para tratamento.
        3. Instancia e valida a entidade Book.
        4. Persiste o livro no repositório.
        """
        normalized_isbn = normalize_isbn(isbn)
        existing_book = self.repository.find_by_isbn(normalized_isbn)
        if existing_book:
            raise DuplicateBookError(
                f"O livro com ISBN '{normalized_isbn}' já está cadastrado no acervo: "
                f"'{existing_book.titulo}' por {existing_book.autor} "
                f"(Exemplares atuais: {existing_book.quantidade_exemplares}).",
                existing_book=existing_book
            )

        # A validação dos dados ocorre na inicialização da entidade de domínio Book
        try:
            new_book = Book(
                titulo=titulo,
                autor=autor,
                isbn=normalized_isbn,
                ano_publicacao=ano_publicacao,
                genero=genero,
                quantidade_exemplares=quantidade_exemplares
            )
        except BookValidationError as e:
            raise BookServiceError(str(e)) from e

        return self.repository.save(new_book)

    def increment_book_copies(self, isbn: str, additional_copies: int) -> Book:
        """
        Regra de Negócio (Cenário 4 da US-01):
        Permite somar exemplares a um livro já cadastrado no acervo.
        """
        if additional_copies < 1:
            raise BookServiceError("A quantidade a ser adicionada deve ser de pelo menos 1 exemplar.")

        normalized_isbn = normalize_isbn(isbn)
        existing_book = self.repository.find_by_isbn(normalized_isbn)
        if not existing_book:
            raise BookNotFoundError(f"Livro com ISBN '{normalized_isbn}' não encontrado para atualização.")

        new_total = existing_book.quantidade_exemplares + int(additional_copies)
        return self.repository.update_copies(existing_book.id, new_total)

    def get_book_by_isbn(self, isbn: str) -> Optional[Book]:
        """Consulta um livro pelo ISBN."""
        normalized_isbn = normalize_isbn(isbn)
        return self.repository.find_by_isbn(normalized_isbn)

    def get_book_by_id(self, book_id: int) -> Optional[Book]:
        """Consulta um livro pelo identificador numérico."""
        return self.repository.find_by_id(book_id)

    def list_catalog(self) -> List[Book]:
        """Retorna todos os livros cadastrados no catálogo."""
        return self.repository.list_all()
