from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Optional, Dict, Any


class BookValidationError(ValueError):
    """Exceção levantada quando algum campo do livro é inválido."""
    pass


def normalize_isbn(raw_isbn: str) -> str:
    """Remove traços, espaços e caracteres especiais do ISBN."""
    if not raw_isbn:
        return ""
    return re.sub(r"[^0-9X]", "", raw_isbn.strip().upper())


def validate_isbn(raw_isbn: str) -> str:
    """
    Valida se a string corresponde a um formato de ISBN-10 ou ISBN-13 válido.
    Retorna o ISBN normalizado (apenas dígitos).
    """
    normalized = normalize_isbn(raw_isbn)
    if len(normalized) not in (10, 13):
        raise BookValidationError(
            f"ISBN '{raw_isbn}' inválido! O ISBN deve conter exatamente 10 ou 13 dígitos numéricos."
        )
    if len(normalized) == 13 and not normalized.isdigit():
        raise BookValidationError(f"ISBN-13 '{raw_isbn}' deve conter apenas dígitos numéricos.")
    if len(normalized) == 10:
        if not (normalized[:9].isdigit() and (normalized[9].isdigit() or normalized[9] == 'X')):
            raise BookValidationError(f"ISBN-10 '{raw_isbn}' possui formato inválido.")
    return normalized


def validate_year(year: Any) -> int:
    """Valida o ano de publicação."""
    try:
        y = int(year)
    except (TypeError, ValueError):
        raise BookValidationError(f"Ano '{year}' deve ser um número inteiro válido.")
    
    current_year = datetime.now().year
    if y < 1 or y > current_year + 1:
        raise BookValidationError(
            f"Ano de publicação '{y}' é inválido. Deve estar entre 1 e {current_year + 1}."
        )
    return y


def validate_copies(copies: Any) -> int:
    """Valida a quantidade de exemplares."""
    try:
        c = int(copies)
    except (TypeError, ValueError):
        raise BookValidationError(f"Quantidade '{copies}' deve ser um número inteiro.")
    if c < 1:
        raise BookValidationError("A quantidade de exemplares deve ser de pelo menos 1.")
    return c


@dataclass
class Book:
    titulo: str
    autor: str
    isbn: str
    ano_publicacao: int
    genero: str
    quantidade_exemplares: int = 1
    id: Optional[int] = None
    criado_em: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def __post_init__(self):
        if not self.titulo or not self.titulo.strip():
            raise BookValidationError("O título do livro não pode ser vazio.")
        if not self.autor or not self.autor.strip():
            raise BookValidationError("O autor do livro não pode ser vazio.")
        if not self.genero or not self.genero.strip():
            raise BookValidationError("O gênero do livro não pode ser vazio.")

        self.titulo = self.titulo.strip()
        self.autor = self.autor.strip()
        self.genero = self.genero.strip().title()
        self.isbn = validate_isbn(self.isbn)
        self.ano_publicacao = validate_year(self.ano_publicacao)
        self.quantidade_exemplares = validate_copies(self.quantidade_exemplares)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "autor": self.autor,
            "isbn": self.isbn,
            "ano_publicacao": self.ano_publicacao,
            "genero": self.genero,
            "quantidade_exemplares": self.quantidade_exemplares,
            "criado_em": self.criado_em
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Book":
        return cls(
            id=data.get("id"),
            titulo=data["titulo"],
            autor=data["autor"],
            isbn=data["isbn"],
            ano_publicacao=data["ano_publicacao"],
            genero=data["genero"],
            quantidade_exemplares=data.get("quantidade_exemplares", 1),
            criado_em=data.get("criado_em", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
