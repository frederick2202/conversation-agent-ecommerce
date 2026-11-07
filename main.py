import os
import sys

# Garante que a raiz do projeto esteja no sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.repositories.book_repository import SQLiteBookRepository
from src.services.book_service import BookService
from src.controllers.book_controller import BookController
from src.agent.conversation_agent import ConversationAgent
from src.cli.console_chat import ConsoleChat


def bootstrap() -> ConsoleChat:
    """Configura e conecta todas as camadas seguindo a arquitetura Controller -> Service -> Repository."""
    # Garante que o diretório data/ exista para persistência
    os.makedirs("data", exist_ok=True)
    db_path = os.path.join("data", "library.db")

    # Camada de Persistência (Repository)
    repository = SQLiteBookRepository(db_path=db_path)

    # Camada de Negócio (Service)
    service = BookService(repository=repository)

    # Camada de Interface/Orquestração (Controller - Sem regra de negócio)
    controller = BookController(service=service)

    # Agente Conversacional (consome o Controller)
    agent = ConversationAgent(controller=controller)

    # Interface de Chat CLI
    return ConsoleChat(agent=agent)


def main():
    chat = bootstrap()
    chat.run()


if __name__ == "__main__":
    main()
