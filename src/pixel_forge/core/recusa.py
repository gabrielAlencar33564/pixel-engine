"""A recusa da engine: todo erro de domínio tem código estável, mensagem, onde ocorreu e a dica de como corrigir
(I8)."""

from __future__ import annotations


class Recusa(Exception):
    def __init__(self, codigo: str, mensagem: str, dica: str, onde: str = "") -> None:
        super().__init__(f"{codigo}: {mensagem}")
        self.codigo = codigo
        self.mensagem = mensagem
        self.dica = dica
        self.onde = onde
