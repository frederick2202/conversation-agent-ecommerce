from abc import ABC, abstractmethod
import sqlite3
from typing import List, Optional
from src.models.book import Book


class BookRepositoryInterface(ABC):
    """Interface abstrata para o repositório de livros (DIP - Dependency Inversion)."""

    @abstractmethod
    def save(self, book: Book) -> Book:
        """Persiste um novo livro e atribui um ID único."""
        pass

    @abstractmethod
    def find_by_isbn(self, isbn: str) -> Optional[Book]:
        """Busca um livro pelo ISBN normalizado."""
        pass

    @abstractmethod
    def find_by_id(self, book_id: int) -> Optional[Book]:
        """Busca um livro pelo ID."""
        pass

    @abstractmethod
    def update_copies(self, book_id: int, new_copies: int) -> Book:
        """Atualiza a quantidade de exemplares de um livro existente."""
        pass

    @abstractmethod
    def list_all(self) -> List[Book]:
        """Retorna todos os livros cadastrados."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Limpa todos os registros (útil para testes)."""
        pass


class SQLiteBookRepository(BookRepositoryInterface):
    """Implementação do repositório utilizando SQLite."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._shared_conn = None
        if self.db_path == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:")
            self._shared_conn.row_factory = sqlite3.Row
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._shared_conn is not None:
            return self._shared_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                autor TEXT NOT NULL,
                isbn TEXT NOT NULL UNIQUE,
                ano_publicacao INTEGER NOT NULL,
                genero TEXT NOT NULL,
                quantidade_exemplares INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT NOT NULL
            )
        """)
        conn.commit()
        if self._shared_conn is None:
            conn.close()

    def save(self, book: Book) -> Book:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO books (titulo, autor, isbn, ano_publicacao, genero, quantidade_exemplares, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            book.titulo,
            book.autor,
            book.isbn,
            book.ano_publicacao,
            book.genero,
            book.quantidade_exemplares,
            book.criado_em
        ))
        conn.commit()
        book.id = cursor.lastrowid
        if self._shared_conn is None:
            conn.close()
        return book

    def find_by_isbn(self, isbn: str) -> Optional[Book]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books WHERE isbn = ?", (isbn,))
        row = cursor.fetchone()
        book = Book.from_dict(dict(row)) if row else None
        if self._shared_conn is None:
            conn.close()
        return book

    def find_by_id(self, book_id: int) -> Optional[Book]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        row = cursor.fetchone()
        book = Book.from_dict(dict(row)) if row else None
        if self._shared_conn is None:
            conn.close()
        return book

    def update_copies(self, book_id: int, new_copies: int) -> Book:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE books SET quantidade_exemplares = ? WHERE id = ?",
            (new_copies, book_id)
        )
        conn.commit()
        if self._shared_conn is None:
            conn.close()
        updated = self.find_by_id(book_id)
        if not updated:
            raise ValueError(f"Livro com ID {book_id} não encontrado.")
        return updated

    def list_all(self) -> List[Book]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books ORDER BY id ASC")
        rows = cursor.fetchall()
        result = [Book.from_dict(dict(row)) for row in rows]
        if self._shared_conn is None:
            conn.close()
        return result

    def clear(self) -> None:
        conn = self._get_connection()
        conn.execute("DELETE FROM books")
        conn.commit()
        if self._shared_conn is None:
            conn.close()
