import unittest
from src.repositories.book_repository import SQLiteBookRepository
from src.services.book_service import BookService, DuplicateBookError, BookServiceError, BookNotFoundError


class TestBookService(unittest.TestCase):
    def setUp(self):
        self.repo = SQLiteBookRepository(":memory:")
        self.service = BookService(repository=self.repo)

    def test_register_book_success(self):
        book = self.service.register_book(
            titulo="Clean Code",
            autor="Robert C. Martin",
            isbn="9780132350884",
            ano_publicacao=2008,
            genero="Tecnologia",
            quantidade_exemplares=4
        )
        self.assertIsNotNone(book.id)
        self.assertEqual(book.titulo, "Clean Code")
        self.assertEqual(book.quantidade_exemplares, 4)

    def test_duplicate_isbn_raises_error(self):
        self.service.register_book(
            titulo="Clean Code",
            autor="Robert C. Martin",
            isbn="9780132350884",
            ano_publicacao=2008,
            genero="Tecnologia",
            quantidade_exemplares=2
        )
        with self.assertRaises(DuplicateBookError) as ctx:
            self.service.register_book(
                titulo="Clean Code - Edição Especial",
                autor="Uncle Bob",
                isbn="9780132350884",
                ano_publicacao=2009,
                genero="Tecnologia",
                quantidade_exemplares=1
            )
        self.assertIn("já está cadastrado", str(ctx.exception))
        self.assertEqual(ctx.exception.existing_book.titulo, "Clean Code")

    def test_increment_copies_for_existing_book(self):
        self.service.register_book(
            titulo="Clean Code",
            autor="Robert C. Martin",
            isbn="9780132350884",
            ano_publicacao=2008,
            genero="Tecnologia",
            quantidade_exemplares=3
        )
        updated = self.service.increment_book_copies("9780132350884", 2)
        self.assertEqual(updated.quantidade_exemplares, 5)

    def test_increment_copies_non_existing_raises_not_found(self):
        with self.assertRaises(BookNotFoundError):
            self.service.increment_book_copies("9789999999999", 1)

    def test_invalid_fields_raise_service_error(self):
        with self.assertRaises(BookServiceError):
            self.service.register_book(
                titulo="",
                autor="Autor",
                isbn="9780132350884",
                ano_publicacao=2020,
                genero="Gênero",
                quantidade_exemplares=1
            )


if __name__ == "__main__":
    unittest.main()
