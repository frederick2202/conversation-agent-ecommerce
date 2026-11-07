import unittest
from src.repositories.book_repository import SQLiteBookRepository
from src.services.book_service import BookService
from src.controllers.book_controller import BookController
from src.agent.conversation_agent import ConversationAgent, AgentState


class TestUserStoryBDD(unittest.TestCase):
    """
    Testes automatizados cobrindo os critérios de aceite BDD da User Story US-01:
    Cadastro de Novos Livros no Acervo via Agente Conversacional.
    """

    def setUp(self):
        self.repo = SQLiteBookRepository(":memory:")
        self.service = BookService(repository=self.repo)
        self.controller = BookController(service=self.service)
        self.agent = ConversationAgent(controller=self.controller)

    def test_cenario_1_cadastro_completo_com_sucesso(self):
        """
        Cenário 1: Cadastro completo com sucesso (passo a passo e confirmação)
        """
        # Dado que o bibliotecário inicia o cadastro de um livro
        resp = self.agent.process_message("Quero cadastrar um novo livro")
        self.assertEqual(self.agent.state, AgentState.AWAITING_TITLE)
        self.assertIn("Título", resp)

        # Quando fornecer todas as informações válidas
        resp = self.agent.process_message("O Pequeno Príncipe")
        self.assertEqual(self.agent.state, AgentState.AWAITING_AUTHOR)
        self.assertIn("Autor", resp)

        resp = self.agent.process_message("Antoine de Saint-Exupéry")
        self.assertEqual(self.agent.state, AgentState.AWAITING_ISBN)
        self.assertIn("ISBN", resp)

        resp = self.agent.process_message("9788522005230")
        self.assertEqual(self.agent.state, AgentState.AWAITING_YEAR)
        self.assertIn("Ano de publicação", resp)

        resp = self.agent.process_message("1943")
        self.assertEqual(self.agent.state, AgentState.AWAITING_GENRE)
        self.assertIn("Gênero", resp)

        resp = self.agent.process_message("Fábula")
        self.assertEqual(self.agent.state, AgentState.AWAITING_COPIES)
        self.assertIn("Quantidade de exemplares", resp)

        resp = self.agent.process_message("4")
        # E o agente apresentar o resumo dos dados para confirmação
        self.assertEqual(self.agent.state, AgentState.AWAITING_CONFIRMATION)
        self.assertIn("Resumo do Livro a ser Cadastrado", resp)
        self.assertIn("O Pequeno Príncipe", resp)

        # E o bibliotecário responder "sim"
        resp = self.agent.process_message("sim")
        # Então o livro deve ser persistido e o agente confirma o sucesso
        self.assertEqual(self.agent.state, AgentState.IDLE)
        self.assertIn("Livro cadastrado com sucesso", resp)

        # Verificação no repositório
        saved_book = self.repo.find_by_isbn("9788522005230")
        self.assertIsNotNone(saved_book)
        self.assertEqual(saved_book.titulo, "O Pequeno Príncipe")
        self.assertEqual(saved_book.quantidade_exemplares, 4)

    def test_cenario_1_cadastro_one_shot(self):
        """
        Variação do Cenário 1: Cadastro em uma única frase completa
        """
        msg = (
            "Cadastrar livro Capitães da Areia, autor Jorge Amado, "
            "ISBN 9788535914061, ano 1937, genero Romance, 3 exemplares"
        )
        resp = self.agent.process_message(msg)
        # O agente já deve extrair tudo e pedir confirmação imediatamente
        self.assertEqual(self.agent.state, AgentState.AWAITING_CONFIRMATION)
        self.assertIn("Capitães da Areia", resp)
        self.assertIn("Jorge Amado", resp)

        confirm_resp = self.agent.process_message("sim")
        self.assertEqual(self.agent.state, AgentState.IDLE)
        self.assertIn("cadastrado com sucesso", confirm_resp)

        saved = self.repo.find_by_isbn("9788535914061")
        self.assertIsNotNone(saved)
        self.assertEqual(saved.quantidade_exemplares, 3)

    def test_cenario_2_coleta_incremental_de_dados_pendentes(self):
        """
        Cenário 2: Coleta de informações pendentes (slot filling)
        """
        # Usuário informa apenas o livro
        resp = self.agent.process_message("Cadastrar livro Ensaio sobre a Cegueira")
        self.assertEqual(self.agent.state, AgentState.AWAITING_AUTHOR)
        self.assertEqual(self.agent.book_data["titulo"], "Ensaio sobre a Cegueira")
        self.assertIn("Autor", resp)

    def test_cenario_3_validacao_de_entradas_invalidas_e_recuperacao(self):
        """
        Cenário 3: Validação de ISBN e campos numéricos inválidos com recuperação
        """
        self.agent.process_message("Cadastrar livro")
        self.agent.process_message("Livro Teste")
        self.agent.process_message("Autor Teste")

        # Estado atual é AWAITING_ISBN; usuário digita ISBN com letras/tamanho inválido
        resp = self.agent.process_message("isbn_errado_123")
        self.assertEqual(self.agent.state, AgentState.AWAITING_ISBN)
        self.assertIn("é inválido", resp)

        # Usuário corrige o ISBN
        resp = self.agent.process_message("9788535902778")
        self.assertEqual(self.agent.state, AgentState.AWAITING_YEAR)

        # Usuário digita ano futuro inválido
        resp = self.agent.process_message("2999")
        self.assertEqual(self.agent.state, AgentState.AWAITING_YEAR)
        self.assertIn("Ano inválido", resp)

        # Corrige o ano
        self.agent.process_message("2021")
        self.assertEqual(self.agent.state, AgentState.AWAITING_GENRE)

    def test_cenario_4_identificacao_isbn_duplicado_e_incremento(self):
        """
        Cenário 4: Identificação de ISBN duplicado e incremento de exemplares
        """
        # Pré-cadastra o livro com 2 exemplares
        self.service.register_book(
            titulo="Dom Casmurro",
            autor="Machado de Assis",
            isbn="9788535902778",
            ano_publicacao=1899,
            genero="Romance",
            quantidade_exemplares=2
        )

        # Bibliotecário tenta cadastrar novamente o mesmo ISBN com 3 novos exemplares
        msg = (
            "Cadastrar livro Dom Casmurro Ed. Luxo, autor Machado de Assis, "
            "ISBN 9788535902778, ano 1899, genero Romance, 3 exemplares"
        )
        self.agent.process_message(msg)
        resp = self.agent.process_message("sim")

        # Agente identifica duplicidade e pergunta se quer acrescentar exemplares
        self.assertEqual(self.agent.state, AgentState.AWAITING_DUPLICATE_DECISION)
        self.assertIn("Já existe um livro cadastrado com o ISBN", resp)
        self.assertIn("+3 exemplar(es)", resp)

        # Bibliotecário aceita acrescentar
        resp2 = self.agent.process_message("sim")
        self.assertEqual(self.agent.state, AgentState.IDLE)
        self.assertIn("Estoque atualizado com sucesso", resp2)
        self.assertIn("5", resp2)

        # Verifica no repositório se o total agora é 2 + 3 = 5
        updated = self.repo.find_by_isbn("9788535902778")
        self.assertEqual(updated.quantidade_exemplares, 5)

    def test_cenario_5_cancelamento_da_operacao(self):
        """
        Cenário 5: Cancelamento do fluxo a qualquer momento
        """
        self.agent.process_message("Cadastrar livro")
        self.agent.process_message("Livro Cancelável")
        self.assertEqual(self.agent.state, AgentState.AWAITING_AUTHOR)

        resp = self.agent.process_message("cancelar")
        self.assertEqual(self.agent.state, AgentState.IDLE)
        self.assertIn("cancelada com sucesso", resp)
        self.assertEqual(len(self.repo.list_all()), 0)


if __name__ == "__main__":
    unittest.main()
