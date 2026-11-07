from enum import Enum, auto
from typing import Dict, Any, Optional
from datetime import datetime
from src.controllers.book_controller import BookController
from src.agent.intent import IntentClassifier, Intent
from src.models.book import normalize_isbn


class AgentState(Enum):
    IDLE = auto()
    AWAITING_TITLE = auto()
    AWAITING_AUTHOR = auto()
    AWAITING_ISBN = auto()
    AWAITING_YEAR = auto()
    AWAITING_GENRE = auto()
    AWAITING_COPIES = auto()
    AWAITING_CONFIRMATION = auto()
    AWAITING_DUPLICATE_DECISION = auto()


class ConversationAgent:
    """
    Agente Conversacional para Gestão da Biblioteca.
    Orquestra o diálogo com o bibliotecário, gerencia o estado da conversa,
    conduz a coleta de slots (slot-filling) e consome o BookController.
    """

    REQUIRED_FIELDS = [
        ("titulo", "Título da obra", AgentState.AWAITING_TITLE),
        ("autor", "Autor(a)", AgentState.AWAITING_AUTHOR),
        ("isbn", "ISBN (10 ou 13 dígitos)", AgentState.AWAITING_ISBN),
        ("ano_publicacao", "Ano de publicação", AgentState.AWAITING_YEAR),
        ("genero", "Gênero/Categoria literária", AgentState.AWAITING_GENRE),
        ("quantidade_exemplares", "Quantidade de exemplares", AgentState.AWAITING_COPIES),
    ]

    def __init__(self, controller: BookController):
        self.controller = controller
        self.state: AgentState = AgentState.IDLE
        self.book_data: Dict[str, Any] = {}
        self.duplicate_info: Optional[Dict[str, Any]] = None

    def reset(self) -> None:
        """Reinicia o estado da conversa para IDLE."""
        self.state = AgentState.IDLE
        self.book_data = {}
        self.duplicate_info = None

    def process_message(self, user_message: str) -> str:
        """
        Processa a mensagem do usuário com base no estado atual da máquina de estados.
        """
        msg = user_message.strip()
        if not msg:
            return "Olá! Sou o assistente da biblioteca. Digite 'ajuda' para ver os comandos."

        intent = IntentClassifier.classify(msg)

        # Comando universal de cancelamento
        if intent == Intent.CANCEL and self.state != AgentState.IDLE:
            self.reset()
            return "❌ Operação cancelada com sucesso. O que gostaria de fazer agora?"

        # Comando universal de saída
        if intent == Intent.EXIT:
            self.reset()
            return "Até logo! O acervo da biblioteca agradece sua dedicação."

        # Despacho baseado no estado da conversa
        if self.state == AgentState.IDLE:
            return self._handle_idle_state(msg, intent)
        elif self.state == AgentState.AWAITING_TITLE:
            return self._handle_title_input(msg)
        elif self.state == AgentState.AWAITING_AUTHOR:
            return self._handle_author_input(msg)
        elif self.state == AgentState.AWAITING_ISBN:
            return self._handle_isbn_input(msg)
        elif self.state == AgentState.AWAITING_YEAR:
            return self._handle_year_input(msg)
        elif self.state == AgentState.AWAITING_GENRE:
            return self._handle_genre_input(msg)
        elif self.state == AgentState.AWAITING_COPIES:
            return self._handle_copies_input(msg)
        elif self.state == AgentState.AWAITING_CONFIRMATION:
            return self._handle_confirmation_state(msg, intent)
        elif self.state == AgentState.AWAITING_DUPLICATE_DECISION:
            return self._handle_duplicate_decision(msg, intent)

        return "Desculpe, não compreendi. Digite 'ajuda' para ver as opções disponíveis."

    def _handle_idle_state(self, msg: str, intent: Intent) -> str:
        if intent == Intent.HELP:
            return (
                "📚 **Comandos disponíveis do Assistente do Acervo:**\n"
                "• 'Cadastrar livro' - Inicia o processo de cadastro de uma nova obra no acervo\n"
                "• 'Listar livros' - Exibe todas as obras atualmente cadastradas no acervo\n"
                "• 'Ajuda' - Mostra este menu de auxílio\n"
                "• 'Sair' - Encerra a conversa\n\n"
                "💡 *Dica:* Você também pode cadastrar diretamente informando tudo em uma única frase!\n"
                "Exemplo: 'Cadastrar livro 1984, autor George Orwell, ISBN 9780451524935, ano 1949, Ficção, 3 exemplares'"
            )

        if intent == Intent.LIST_BOOKS:
            res = self.controller.list_all()
            books = res.get("data", [])
            if not books:
                return "📖 O acervo da biblioteca está vazio no momento. Que tal cadastrar o primeiro livro?"

            lines = ["📚 **Livros Atualmente no Acervo:**\n"]
            for b in books:
                lines.append(
                    f"• [ID #{b['id']}] **{b['titulo']}** por *{b['autor']}* | "
                    f"ISBN: `{b['isbn']}` | Ano: {b['ano_publicacao']} | "
                    f"Gênero: {b['genero']} | Exemplares: **{b['quantidade_exemplares']}**"
                )
            return "\n".join(lines)

        if intent == Intent.START_REGISTRATION:
            self.reset()
            extracted = IntentClassifier.extract_one_shot_fields(msg)
            self.book_data.update(extracted)
            return self._ask_next_missing_field("Excelente! Vamos iniciar o cadastro de um novo livro no acervo.")

        return (
            "Olá! Sou seu assistente de gestão do acervo da biblioteca.\n"
            "Deseja **cadastrar um novo livro** ou **listar livros** do acervo? (Digite 'ajuda' para mais opções)"
        )

    def _ask_next_missing_field(self, prefix_msg: str = "") -> str:
        """Identifica o próximo campo pendente e transiciona o estado."""
        for key, label, next_state in self.REQUIRED_FIELDS:
            if key not in self.book_data or self.book_data[key] in (None, ""):
                self.state = next_state
                lead = f"{prefix_msg}\n\n" if prefix_msg else ""
                return f"{lead}Por favor, informe o **{label}**:"

        # Se todos os campos já foram preenchidos:
        self.state = AgentState.AWAITING_CONFIRMATION
        return self._format_summary_and_prompt()

    def _format_summary_and_prompt(self) -> str:
        b = self.book_data
        summary = (
            "📋 **Resumo do Livro a ser Cadastrado:**\n"
            f"• **Título:** {b.get('titulo')}\n"
            f"• **Autor:** {b.get('autor')}\n"
            f"• **ISBN:** {b.get('isbn')}\n"
            f"• **Ano de Publicação:** {b.get('ano_publicacao')}\n"
            f"• **Gênero:** {b.get('genero')}\n"
            f"• **Quantidade de Exemplares:** {b.get('quantidade_exemplares', 1)}\n\n"
            "Deseja confirmar o cadastro no sistema? (**Sim** / **Não**)"
        )
        return summary

    def _handle_title_input(self, msg: str) -> str:
        if not msg:
            return "⚠️ O título não pode ser vazio. Por favor, digite o título da obra:"
        self.book_data["titulo"] = msg
        return self._ask_next_missing_field("Título registrado com sucesso.")

    def _handle_author_input(self, msg: str) -> str:
        if not msg:
            return "⚠️ O autor não pode ser vazio. Por favor, informe o autor ou autora:"
        self.book_data["autor"] = msg
        return self._ask_next_missing_field("Autor registrado com sucesso.")

    def _handle_isbn_input(self, msg: str) -> str:
        norm = normalize_isbn(msg)
        if len(norm) not in (10, 13):
            return (
                f"⚠️ O ISBN '{msg}' é inválido.\n"
                "Um ISBN deve conter 10 ou 13 dígitos numéricos (hífens são aceitos).\n"
                "Por favor, digite um ISBN válido:"
            )
        self.book_data["isbn"] = norm
        return self._ask_next_missing_field("ISBN validado e registrado.")

    def _handle_year_input(self, msg: str) -> str:
        try:
            year = int(msg)
            current_year = datetime.now().year
            if year < 1 or year > current_year + 1:
                return f"⚠️ Ano inválido. Por favor, informe um ano entre 1 e {current_year + 1}:"
            self.book_data["ano_publicacao"] = year
            return self._ask_next_missing_field("Ano registrado.")
        except ValueError:
            return "⚠️ Por favor, informe um ano válido em formato numérico (ex: 2023):"

    def _handle_genre_input(self, msg: str) -> str:
        if not msg:
            return "⚠️ O gênero não pode ser vazio. Ex: Ficção, Romance, Tecnologia, História:"
        self.book_data["genero"] = msg
        return self._ask_next_missing_field("Gênero registrado.")

    def _handle_copies_input(self, msg: str) -> str:
        try:
            copies = int(msg)
            if copies < 1:
                return "⚠️ A quantidade deve ser de no mínimo 1 exemplar. Quantos exemplares deseja cadastrar?"
            self.book_data["quantidade_exemplares"] = copies
            return self._ask_next_missing_field("Quantidade registrada.")
        except ValueError:
            return "⚠️ Por favor, digite um número inteiro válido para a quantidade de exemplares:"

    def _handle_confirmation_state(self, msg: str, intent: Intent) -> str:
        if intent == Intent.CONFIRM:
            # O Controller é acionado sem regras de negócio
            res = self.controller.create_book(self.book_data)

            if res.get("status") == "success":
                data = res["data"]
                self.reset()
                return (
                    f"✅ **Livro cadastrado com sucesso no acervo!**\n"
                    f"• **ID no Catálogo:** #{data['id']}\n"
                    f"• **Título:** {data['titulo']}\n"
                    f"• **Autor:** {data['autor']}\n"
                    f"• **ISBN:** `{data['isbn']}`\n"
                    f"• **Exemplares disponíveis:** {data['quantidade_exemplares']}\n\n"
                    "O livro já está disponível para consulta e empréstimos!"
                )
            elif res.get("status") == "duplicate":
                self.duplicate_info = res
                self.state = AgentState.AWAITING_DUPLICATE_DECISION
                existing = res.get("existing_book", {})
                new_copies = self.book_data.get("quantidade_exemplares", 1)
                return (
                    f"⚠️ **Atenção:** Já existe um livro cadastrado com o ISBN `{self.book_data.get('isbn')}`!\n"
                    f"• **Obra existente:** '{existing.get('titulo')}' por {existing.get('autor')}\n"
                    f"• **Exemplares atuais:** {existing.get('quantidade_exemplares')}\n\n"
                    f"Deseja apenas **acrescentar +{new_copies} exemplar(es)** ao estoque existente? (**Sim** / **Não**)"
                )
            else:
                err_msg = res.get("message", "Erro desconhecido")
                self.reset()
                return f"❌ Falha ao cadastrar livro: {err_msg}. Operação cancelada."

        elif intent in (Intent.DENY, Intent.CANCEL):
            self.reset()
            return "❌ Cadastro cancelado pelo usuário. Nenhum dado foi salvo no acervo."

        return "Por favor, responda com **Sim** para confirmar o cadastro ou **Não** para cancelar."

    def _handle_duplicate_decision(self, msg: str, intent: Intent) -> str:
        if intent == Intent.CONFIRM:
            isbn = self.book_data.get("isbn")
            copies = self.book_data.get("quantidade_exemplares", 1)
            res = self.controller.add_copies({
                "isbn": isbn,
                "quantidade_exemplares": copies
            })
            self.reset()
            if res.get("status") == "success":
                book = res["data"]
                return (
                    f"✅ **Estoque atualizado com sucesso!**\n"
                    f"Foram adicionados novos exemplares ao livro '{book['titulo']}'.\n"
                    f"Total de exemplares no acervo: **{book['quantidade_exemplares']}**."
                )
            else:
                return f"❌ Erro ao atualizar estoque: {res.get('message')}."

        elif intent in (Intent.DENY, Intent.CANCEL):
            self.reset()
            return "Operação cancelada. O registro existente permanece inalterado."

        return "Por favor, responda com **Sim** para somar os exemplares ou **Não** para cancelar."
