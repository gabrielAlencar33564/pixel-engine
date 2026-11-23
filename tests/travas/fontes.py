"""O que as travas leem do repositório: os arquivos Python, os módulos que cada um importa e as palavras de um texto."""

from __future__ import annotations

import ast
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


def arquivos_py(*pastas: Path) -> list[Path]:
    return sorted(p for pasta in pastas if pasta.exists() for p in pasta.rglob("*.py"))


def modulo_de(arquivo: Path, raiz: Path) -> str:
    partes = list(arquivo.relative_to(raiz).with_suffix("").parts)
    if partes[-1] == "__init__":
        partes.pop()
    return ".".join(partes)


def importados(arquivo: Path, raiz: Path) -> set[str]:
    """Os módulos que o arquivo importa, com os relativos resolvidos pelo pacote dele."""
    modulo = modulo_de(arquivo, raiz)
    pacote = modulo.split(".") if arquivo.name == "__init__.py" else modulo.split(".")[:-1]
    out: set[str] = set()
    for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
        if isinstance(no, ast.Import):
            out.update(a.name for a in no.names)
        elif isinstance(no, ast.ImportFrom):
            base = pacote[: len(pacote) - no.level + 1] if no.level else []
            alvo = ".".join([*base, *(no.module.split(".") if no.module else [])])
            out.add(alvo)
            out.update(f"{alvo}.{a.name}" for a in no.names)
    return out


def palavras(texto: str) -> set[str]:
    """As palavras do texto sem acento e em minúsculas, separadas por tudo que não é letra ou dígito (o `_` também)."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return {p for p in re.split(r"[^a-z0-9]+", sem_acento) if p}
