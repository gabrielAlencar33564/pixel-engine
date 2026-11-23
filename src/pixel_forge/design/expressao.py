"""As expressões da composição: números, medidas (``$nome``), + − × ÷, ``min``, ``max``, ``round`` e parênteses. Não
há condição, laço, função nem referência a outro nó.

Unidades: ``m``, ``cm``, ``mm`` e ``px`` dão comprimento em px do mundo; ``%`` divide por 100; ``deg`` dá radianos.
Um número sem unidade é escalar. A conta é em float64 e só é quantizada quando vira geometria. A expressão é lida uma
vez (:func:`compilar`) e avaliada em cada repetição do nó com as variáveis dela.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from typing import Any

from ..core.recusa import Recusa
from .escala import PPM

_TOKEN = re.compile(r"\s*(?:(\d+(?:\.\d+)?)(m|cm|mm|px|%|deg)?(?![a-z0-9_])|(\$[a-z][a-z0-9_]*)"
                    r"|(min|max|round)\s*(?=\()|([-+*/(),]))")
FUNCOES: dict[str, Callable[..., float]] = {"min": min, "max": max, "round": lambda x: float(round(x))}
UNIDADES = {"m": PPM, "cm": PPM / 100, "mm": PPM / 1000, "%": 0.01, "deg": math.pi / 180}
Node = tuple[Any, ...]
DICA = "Use números, medidas ($nome), unidades (m, cm, mm, px, %, deg), + - * /, min, max, round e parênteses."


def _erro(texto: str, motivo: str, onde: str) -> Recusa:
    return Recusa("EXPRESSAO", f"Expressão '{texto}': {motivo}.", DICA, onde)


def _tokens(texto: str, onde: str) -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []
    pos = 0
    while pos < len(texto) and texto[pos:].strip():
        m = _TOKEN.match(texto, pos)
        if m is None:
            raise _erro(texto, f"não entendi '{texto[pos:].strip()[:12]}'", onde)
        num, unidade, var, fn, op = m.groups()
        if num is not None:
            out.append(("num", (float(num), unidade)))
        elif var is not None:
            out.append(("var", var[1:]))
        elif fn is not None:
            out.append(("fn", fn))
        else:
            out.append(("op", op))
        pos = m.end()
    return out


class _Leitor:
    def __init__(self, texto: str, onde: str) -> None:
        self.texto, self.onde = texto, onde
        self.toks = _tokens(texto, onde)
        self.i = 0

    def _ve(self) -> tuple[str, Any] | None:
        return self.toks[self.i] if self.i < len(self.toks) else None

    def _op(self, *ops: str) -> str | None:
        t = self._ve()
        if t is not None and t[0] == "op" and t[1] in ops:
            self.i += 1
            return str(t[1])
        return None

    def _fecha(self, motivo: str) -> None:
        if self._op(")") is None:
            raise _erro(self.texto, motivo, self.onde)

    def expr(self) -> Node:
        n = self.termo()
        while (o := self._op("+", "-")) is not None:
            n = (o, n, self.termo())
        return n

    def termo(self) -> Node:
        n = self.unario()
        while (o := self._op("*", "/")) is not None:
            n = (o, n, self.unario())
        return n

    def unario(self) -> Node:
        if self._op("-") is not None:
            return ("neg", self.unario())
        return self.atomo()

    def _funcao(self, nome: str) -> Node:
        if self._op("(") is None:
            raise _erro(self.texto, f"{nome} sem '('", self.onde)
        args = [self.expr()]
        while self._op(",") is not None:
            args.append(self.expr())
        self._fecha(f"{nome}( sem ')'")
        if nome == "round" and len(args) != 1:
            raise _erro(self.texto, "round leva um argumento", self.onde)
        return ("fn", nome, tuple(args))

    def atomo(self) -> Node:
        t = self._ve()
        if t is None:
            raise _erro(self.texto, "terminou no meio", self.onde)
        self.i += 1
        if t[0] in ("num", "var"):
            return (t[0], *t[1]) if t[0] == "num" else ("var", t[1])
        if t[0] == "fn":
            return self._funcao(t[1])
        if t == ("op", "("):
            n = self.expr()
            self._fecha("'(' sem ')'")
            return n
        raise _erro(self.texto, f"'{t[1]}' fora de lugar", self.onde)


def compilar(texto: str, onde: str = "") -> Node:
    """A árvore da expressão; recusa o que não é da gramática."""
    leitor = _Leitor(texto, onde)
    n = leitor.expr()
    if leitor.i != len(leitor.toks):
        raise _erro(texto, f"sobrou '{leitor.toks[leitor.i][1]}'", onde)
    return n


def variaveis(n: Node) -> set[str]:
    """As medidas e variáveis de repetição que a expressão usa."""
    if n[0] == "var":
        return {n[1]}
    if n[0] == "num":
        return set()
    filhos = n[2] if n[0] == "fn" else n[1:]
    return set().union(*(variaveis(a) for a in filhos))


def _binaria(tipo: str, a: float, b: float, onde: str) -> float:
    if tipo == "/" and b == 0:
        raise Recusa("EXPRESSAO", "Divisão por zero.", "Confira as medidas.", onde)
    return {"+": a + b, "-": a - b, "*": a * b, "/": a / b if b else 0.0}[tipo]


def avaliar(n: Node, env: dict[str, float], onde: str = "") -> float:
    """O valor da árvore com as variáveis de ``env`` (os comprimentos já em px)."""
    tipo = n[0]
    if tipo == "num":
        v, unidade = n[1], n[2]
        return float(v) if unidade is None or unidade == "px" else float(v * UNIDADES[unidade])
    if tipo == "var":
        if n[1] not in env:
            raise Recusa("EXPRESSAO", f"Medida '${n[1]}' não declarada.",
                         "Declare em 'medidas' (antes de quem a usa) ou use a variável da repetição.", onde)
        return env[n[1]]
    if tipo == "neg":
        return -avaliar(n[1], env, onde)
    if tipo == "fn":
        return float(FUNCOES[n[1]](*(avaliar(a, env, onde) for a in n[2])))
    return _binaria(tipo, avaliar(n[1], env, onde), avaliar(n[2], env, onde), onde)


def valor(texto: str, env: dict[str, float], onde: str = "") -> float:
    return avaliar(compilar(texto, onde), env, onde)
