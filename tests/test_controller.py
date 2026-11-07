import unittest
from src.repositories.book_repository import SQLiteBookRepository
from src.services.book_service import BookService
from src.controllers.book_controller import BookController


class TestBookController(unittest.TestCase):
    def setUp(self):
        self.repo = SQLiteBookRepository(":memory:")
        self.service = BookService(repository=self.repo)
        self.controller = BookController(service=self.service)

    def test_create_book_success_response(self):
        payload = {
            "titulo": "O Hobbit",
            "autor": "J.R.R. Tolkien",
            "isbn": "9788595084759",
            "ano_publicacao": 1937,
            "genero": "Fantasia",
            "quantidade_exemplares": 5
        }
        response = self.controller.create_book(payload)
        self.assertEqual(response["status"], "success")
        self.assertIn("data", response)
        self.assertEqual(response["data"]["titulo"], "O Hobbit")

    def test_create_book_duplicate_response(self):
        payload = {
            "titulo": "O Hobbit",
            "autor": "J.R.R. Tolkien",
            "isbn": "9788595084759",
            "ano_publicacao": 1937,
            "genero": "Fantasia",
            "quantidade_exemplares": 2
        }
        self.controller.create_book(payload)
        response2 = self.controller.create_book(payload)

        self.assertEqual(response2["status"], "duplicate")
        self.assertIn("existing_book", response2)

    def test_create_book_validation_error_response(self):
        payload = {
            "titulo": "Título",
            "autor": "Autor",
            "isbn": "123",  # ISBN inválido
            "ano_publicacao": 2020,
            "genero": "Gênero",
            "quantidade_exemplares": 1
        }
        response = self.controller.create_book(payload)
        self.assertEqual(response["status"], "error")
        self.assertIn("ISBN '123' inválido", response["message"])

    def test_add_copies_success(self):
        self.controller.create_book({
            "titulo": "Livro Base",
            "autor": "Autor",
            "isbn": "9780000000000",
            "ano_publicacao": 2020,
            "genero": "Gênero",
            "quantidade_exemplares": 2
        })
        response = self.controller.add_copies({
            "isbn": "9780000000000",
            "quantidade_exemplares": 3
        })
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["quantidade_exemplares"], 5)


if __name__ == "__main__":
    unittest.main()
