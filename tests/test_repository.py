import unittest
from src.models.book import Book
from src.repositories.book_repository import SQLiteBookRepository


class TestBookRepository(unittest.TestCase):
    def setUp(self):
        # Repositório em memória para isolamento total dos testes
        self.repo = SQLiteBookRepository(":memory:")

    def test_save_and_find_by_isbn(self):
        book = Book(
            titulo="Dom Casmurro",
            autor="Machado de Assis",
            isbn="9788535902778",
            ano_publicacao=1899,
            genero="Romance",
            quantidade_exemplares=3
        )
        saved = self.repo.save(book)
        self.assertIsNotNone(saved.id)

        found = self.repo.find_by_isbn("9788535902778")
        self.assertIsNotNone(found)
        self.assertEqual(found.titulo, "Dom Casmurro")
        self.assertEqual(found.quantidade_exemplares, 3)

    def test_update_copies(self):
        book = Book(
            titulo="1984",
            autor="George Orwell",
            isbn="9780451524935",
            ano_publicacao=1949,
            genero="Ficção Científica",
            quantidade_exemplares=2
        )
        saved = self.repo.save(book)
        updated = self.repo.update_copies(saved.id, 5)

        self.assertEqual(updated.quantidade_exemplares, 5)
        refetched = self.repo.find_by_id(saved.id)
        self.assertEqual(refetched.quantidade_exemplares, 5)

    def test_list_all(self):
        self.assertEqual(len(self.repo.list_all()), 0)
        self.repo.save(Book(
            titulo="Livro 1", autor="Autor 1", isbn="9780000000001",
            ano_publicacao=2020, genero="Ficção", quantidade_exemplares=1
        ))
        self.repo.save(Book(
            titulo="Livro 2", autor="Autor 2", isbn="9780000000002",
            ano_publicacao=2021, genero="Tecnologia", quantidade_exemplares=2
        ))
        all_books = self.repo.list_all()
        self.assertEqual(len(all_books), 2)


if __name__ == "__main__":
    unittest.main()
