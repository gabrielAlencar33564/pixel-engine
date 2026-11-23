"""O código morto por referência (I10): cada função, classe, método e constante de módulo tem de ser citado fora da
própria definição, no código da engine (``src/``) ou nos scripts. A citação num teste não conta: o que só o teste usa
está morto."""

from __future__ import annotations

import ast
import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .fontes import arquivos_py

Def = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Assign | ast.AnnAssign


@dataclass(frozen=True)
class Morto:
    nome: str
    arquivo: Path
    linha: int


def _dunder(nome: str) -> bool:
    return nome.startswith("__") and nome.endswith("__")


def _metodos(classe: ast.ClassDef) -> list[tuple[str, Def]]:
    return [(m.name, m) for m in classe.body if isinstance(m, ast.FunctionDef | ast.AsyncFunctionDef)]


def definicoes(arvore: ast.Module) -> list[tuple[str, Def]]:
    out: list[tuple[str, Def]] = []
    for no in arvore.body:
        if isinstance(no, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            out.append((no.name, no))
            if isinstance(no, ast.ClassDef):
                out.extend(_metodos(no))
        elif isinstance(no, ast.Assign):
            out.extend((t.id, no) for t in no.targets if isinstance(t, ast.Name))
        elif isinstance(no, ast.AnnAssign) and isinstance(no.target, ast.Name):
            out.append((no.target.id, no))
    return [(n, d) for n, d in out if not _dunder(n)]


def citacoes(no: ast.AST) -> Counter[str]:
    """Os nomes lidos dentro de ``no``: variável, atributo e argumento nomeado (o import não é citação)."""
    c: Counter[str] = Counter()
    for x in ast.walk(no):
        if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load):
            c[x.id] += 1
        elif isinstance(x, ast.Attribute) and isinstance(x.ctx, ast.Load):
            c[x.attr] += 1
        elif isinstance(x, ast.keyword) and x.arg:
            c[x.arg] += 1
    return c


def pontos_de_entrada(pyproject: Path) -> set[str]:
    """As funções que o ``[project.scripts]`` chama (``pacote.modulo:funcao``)."""
    if not pyproject.exists():
        return set()
    scripts = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("project", {}).get("scripts", {})
    return {alvo.split(":")[-1] for alvo in scripts.values()}


def mortos(pastas: list[Path], pyproject: Path) -> list[Morto]:
    arvores = {p: ast.parse(p.read_text(encoding="utf-8")) for p in arquivos_py(*pastas)}
    total: Counter[str] = Counter()
    for arvore in arvores.values():
        total.update(citacoes(arvore))
    total.update(pontos_de_entrada(pyproject))
    out = []
    for arquivo, arvore in arvores.items():
        for nome, no in definicoes(arvore):
            if total[nome] - citacoes(no)[nome] <= 0:
                out.append(Morto(nome, arquivo, no.lineno))
    return out
