import re
from typing import Dict, Any, Optional, Tuple
from enum import Enum, auto


class Intent(Enum):
    START_REGISTRATION = auto()
    CONFIRM = auto()
    DENY = auto()
    CANCEL = auto()
    LIST_BOOKS = auto()
    HELP = auto()
    EXIT = auto()
    UNKNOWN = auto()


class IntentClassifier:
    """Classificador de intenções simples e robusto baseado em padrões e palavras-chave."""

    CONFIRM_WORDS = {"sim", "s", "yes", "y", "confirmo", "confirmar", "ok", "correto", "pode cadastrar", "positivo"}
    DENY_WORDS = {"não", "nao", "n", "no", "rejeitar", "discordo", "negativo"}
    CANCEL_WORDS = {"cancelar", "cancela", "abortar", "cancela aí", "parar", "desistir"}
    EXIT_WORDS = {"sair", "tchau", "exit", "quit", "encerrar", "fechar"}
    LIST_WORDS = {"listar", "listar livros", "ver acervo", "mostrar livros", "catalogo", "catálogo", "livros cadastrados"}
    HELP_WORDS = {"ajuda", "help", "comandos", "menu", "como funciona", "?"}

    @classmethod
    def classify(cls, text: str) -> Intent:
        clean = text.strip().lower()

        if clean in cls.EXIT_WORDS:
            return Intent.EXIT
        if clean in cls.CANCEL_WORDS:
            return Intent.CANCEL
        if clean in cls.CONFIRM_WORDS:
            return Intent.CONFIRM
        if clean in cls.DENY_WORDS:
            return Intent.DENY
        if any(w in clean for w in cls.LIST_WORDS):
            return Intent.LIST_BOOKS
        if clean in cls.HELP_WORDS:
            return Intent.HELP

        # Gatilhos para iniciar cadastro
        if any(trigger in clean for trigger in [
            "cadastrar", "adicionar livro", "novo livro", "inserir livro",
            "registrar livro", "cadastro de livro", "incluir livro"
        ]):
            return Intent.START_REGISTRATION

        return Intent.UNKNOWN

    @classmethod
    def extract_one_shot_fields(cls, text: str) -> Dict[str, Any]:
        """
        Tenta extrair campos caso o usuário envie múltiplos dados de uma vez só.
        Ex: 'Cadastrar livro Dom Casmurro, autor Machado de Assis, ISBN 9788535902778, ano 1899, genero Romance, 3 exemplares'
        """
        extracted = {}

        # ISBN
        isbn_match = re.search(r"\bisbn[:\s]+([0-9Xx\-]{10,17})\b", text, re.IGNORECASE)
        if not isbn_match:
            # Procura qualquer sequência isolada de 10 ou 13 dígitos
            isbn_match = re.search(r"\b([0-9]{13}|[0-9]{10})\b", text)
        if isbn_match:
            extracted["isbn"] = isbn_match.group(1).replace("-", "").strip()

        # Ano
        year_match = re.search(r"\bano[:\s]+(\d{4})\b", text, re.IGNORECASE)
        if year_match:
            extracted["ano_publicacao"] = int(year_match.group(1))

        # Quantidade de exemplares
        copies_match = re.search(r"(\d+)\s*(?:exemplar|exemplares|copias|cópias)", text, re.IGNORECASE)
        if not copies_match:
            copies_match = re.search(r"\b(?:quantidade|exemplares)[:\s]+(\d+)\b", text, re.IGNORECASE)
        if copies_match:
            extracted["quantidade_exemplares"] = int(copies_match.group(1))

        # Gênero
        genre_match = re.search(r"\b(?:genero|gênero|categoria)[:\s]+([^,\n]+)", text, re.IGNORECASE)
        if genre_match:
            extracted["genero"] = genre_match.group(1).strip()

        # Autor
        author_match = re.search(r"\b(?:autor|autora|escritor)[:\s]+([^,\n]+)", text, re.IGNORECASE)
        if author_match:
            extracted["autor"] = author_match.group(1).strip()

        # Título
        title_match = re.search(r"\b(?:livro|titulo|título)[:\s]+([^,\n]+)", text, re.IGNORECASE)
        if title_match:
            extracted["titulo"] = title_match.group(1).strip()

        return extracted
