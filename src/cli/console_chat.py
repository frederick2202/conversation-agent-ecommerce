import sys
from typing import Optional
from src.agent.conversation_agent import ConversationAgent

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ConsoleChat:
    """Interface de Terminal interativa para conversar com o Agente da Biblioteca."""

    def __init__(self, agent: ConversationAgent):
        self.agent = agent
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None

    def display_bot(self, message: str) -> None:
        if RICH_AVAILABLE:
            self.console.print(Panel(Markdown(message), title="🤖 Assistente da Biblioteca", border_style="cyan"))
        else:
            print("\n" + "=" * 50)
            print(f"[Assistente da Biblioteca]:\n{message}")
            print("=" * 50 + "\n")

    def run(self) -> None:
        welcome_banner = (
            "# 🏛️ Sistema de Gestão de Acervo da Biblioteca\n\n"
            "Bem-vindo ao **Agente Conversacional da Biblioteca**.\n"
            "Aqui você pode cadastrar livros de forma guiada ou direta!\n\n"
            "*Exemplos de comandos:*\n"
            "- `Cadastrar livro`\n"
            "- `Listar livros`\n"
            "- `Ajuda`\n"
            "- `Sair`"
        )
        self.display_bot(welcome_banner)

        while True:
            try:
                if RICH_AVAILABLE:
                    user_input = self.console.input("[bold green]👤 Você > [/bold green]").strip()
                else:
                    user_input = input("👤 Você > ").strip()

                if not user_input:
                    continue

                response = self.agent.process_message(user_input)
                self.display_bot(response)

                if self.agent.state.name == "IDLE" and user_input.lower() in ("sair", "exit", "quit"):
                    break

            except (KeyboardInterrupt, EOFError):
                print("\nEncerrando sessão. Até mais!")
                break
