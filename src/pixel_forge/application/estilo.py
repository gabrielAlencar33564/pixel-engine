"""O estilo do jogo: o base da engine (a paleta por função, com luz neutra; a hora do dia é do jogo)."""

from __future__ import annotations

from functools import cache
from pathlib import Path

from ..contracts.carregar import ler
from ..contracts.estilo import StyleDoc

ARQUIVO = Path(__file__).resolve().parents[1] / "dados" / "estilo_base.json"


@cache
def estilo_base() -> StyleDoc:
    return ler(ARQUIVO, StyleDoc)
