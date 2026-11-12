from dataclasses import dataclass
from typing import Protocol


class InvalidDocument(ValueError):
    pass


class BackendUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class Page:
    number: int
    text: str


@dataclass(frozen=True)
class Chunk:
    page: int
    ordinal: int
    text: str


@dataclass(frozen=True)
class Hit:
    id: int
    document_id: str
    name: str
    page: int
    text: str


class Model(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    def answer(self, question: str, hits: list[Hit]) -> dict: ...
