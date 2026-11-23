"""A peça do kit como dado: o schema dos argumentos, as variações da prancha e o teste.

Uma peça é uma função registrada (``desenha(ctx, args)``) que recebe os argumentos já em px do mundo e acrescenta
partes da IR ao construtor do contexto. A composição escreve os argumentos em expressões com unidades de gente (m, cm,
%); :func:`ler_args` confere o schema e avalia. Cada peça declara o schema (até :data:`MAX_ARGS`), pelo menos 3
variações (a prancha do catálogo), o teste com controle negativo, as funções que ela usa (o teto de
:data:`MAX_LINHAS` linhas conta todas), as vistas que desenha e as âncoras que deixa para os nós seguintes.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

from ...core.recusa import Recusa
from ...core.rng import Stream
from ..construtor import FLAT, LINE, AssetBuilder, Parte, Vec, bound_polygon, polyline, qv
from ..expressao import avaliar, compilar, variaveis
from .movimento import bone_for
from .pilha import Pilha

MAX_ARGS = 12
MAX_LINHAS = 250
Tipo = Literal["comprimento", "escalar", "inteiro", "ponto", "pontos", "faixa", "vaos", "bool", "material", "fracoes",
               "tons", "ancora"]
CLASSES = ("light", "mid", "dark")  # as linhas de um argumento ``tons``: claro, médio e escuro
Elo = tuple[str, float, float]


@dataclass(frozen=True)
class Arg:
    nome: str
    tipo: Tipo
    descricao: str
    padrao: Any = None  # None = obrigatório; o padrão é escrito como na composição (expressão)


@dataclass
class Ctx:
    """O que a peça recebe além dos argumentos: o construtor, a semente do nó, o id (prefixo das partes), o grupo de
    contorno, a pilha da face e a camada; as vistas da composição (com o azimute), a cadeia do balanço e o osso do
    nó, as âncoras dos nós de antes e o que a peça muda por vista."""

    b: AssetBuilder
    st: Stream
    pid: str
    grupo: str
    pilha: Pilha
    camada: int
    regras: list[dict[str, Any]] = field(default_factory=list)
    vistas: dict[str, int] = field(default_factory=lambda: {"S": 0})
    cadeia: Sequence[Elo] = ()
    modo_osso: str = "raiz"
    ancoras: dict[str, list[Any]] = field(default_factory=dict)
    por_vista: dict[str, dict[str, dict[str, Any]]] = field(default_factory=dict)
    no: str = ""

    def deixa(self, nome: str, pontos: list[Any]) -> None:
        """Deixa a âncora ``<nó>.<nome>`` (as repetições do nó somam os pontos) para os nós seguintes."""
        self.ancoras.setdefault(f"{self.no or self.pid}.{nome}", []).extend(pontos)

    def ancora(self, ref: str) -> list[Any]:
        return list(self.ancoras.get(ref, [])) if ref else []

    def poly(self, pid: str, mat: str, pts: list[Vec], camada: int, tags: tuple[str, ...] = FLAT) -> None:
        """Uma face chapada pelos pontos (na raiz), empilhada na pilha da face."""
        self.b.part(pid, mat, bound_polygon(pts), Parte(group=self.grupo, tags=tags))
        self.pilha.add(pid, camada, pts)

    def line(self, pid: str, mat: str, pts: list[Vec], camada: int, width: int = 1) -> None:
        """Um traço de ``width`` px pelos pontos (detalhe, sem contorno), empilhado na pilha da face."""
        self.b.part(pid, mat, polyline([qv(*p) for p in pts], width), Parte(group=self.grupo, tags=LINE))
        self.pilha.add(pid, camada, pts)

    def osso(self, z: float) -> tuple[str, float]:
        """(osso, z local) da massa na altura ``z``: o elo da cadeia que contém ``z``, o tronco ou a raiz."""
        if self.modo_osso == "cadeia" and self.cadeia:
            return bone_for(self.cadeia, z)
        return ("trunk" if self.modo_osso == "tronco" and self.cadeia else "root"), z


@dataclass(frozen=True)
class Peca:
    id: str
    descricao: str
    args: tuple[Arg, ...]
    desenha: Callable[[Ctx, dict[str, Any]], None]
    variacoes: tuple[tuple[str, dict[str, Any]], ...]
    teste: str
    funcoes: tuple[Callable[..., Any], ...] = ()
    vistas: tuple[str, ...] = ("S",)
    ancoras: tuple[str, ...] = ()
    tipo: Literal["prop", "humanoide", "quadrupede"] = "prop"


def _erro(peca: str, msg: str, onde: str) -> Recusa:
    return Recusa("ARGUMENTO", f"Peça '{peca}': {msg}.", "Veja o schema da peça em `pfe catalogo`.", onde)


@dataclass(frozen=True)
class _Leitura:
    """Um argumento sendo lido: o nome, o valor bruto, as medidas, onde e a peça."""

    a: Arg
    v: Any
    env: dict[str, float]
    onde: str
    peca: str

    def erro(self, msg: str) -> Recusa:
        return _erro(self.peca, msg, self.onde)

    def num(self, texto: Any, onde: str) -> float:
        if not isinstance(texto, str):
            raise _erro(self.peca, f"esperava uma expressão, veio {texto!r}", onde)
        return avaliar(compilar(texto, onde), self.env, onde)

    def lista(self, n: int | None) -> list[Any]:
        if not isinstance(self.v, list) or (n is not None and len(self.v) != n):
            raise self.erro(f"esperava uma lista{f' de {n}' if n else ''}, veio {self.v!r}")
        return self.v

    def numeros(self, n: int | None) -> tuple[float, ...]:
        return tuple(self.num(c, f"{self.onde}/{i}") for i, c in enumerate(self.lista(n)))


def _id(v: str) -> bool:
    return bool(v) and v.replace("_", "").isalnum()


def _bool(lt: _Leitura) -> bool:
    if not isinstance(lt.v, bool):
        raise lt.erro(f"'{lt.a.nome}' é verdadeiro ou falso")
    return lt.v


def _material(lt: _Leitura) -> str:
    if lt.v == "" and lt.a.padrao == "":  # o material opcional
        return ""
    if not isinstance(lt.v, str) or not _id(lt.v):
        raise lt.erro(f"'{lt.a.nome}' é o id de um material")
    return lt.v


def _ancora(lt: _Leitura) -> str:
    partes = lt.v.split(".") if isinstance(lt.v, str) else []
    if lt.v != "" and (len(partes) != 2 or not all(_id(x) for x in partes)):
        raise lt.erro(f"'{lt.a.nome}' é '<nó>.<âncora>'")
    return str(lt.v)


def _tons(lt: _Leitura) -> dict[str, tuple[str, ...]]:
    """[[núcleo, luz, sombra(, brilho)] claro, médio, escuro]."""
    linhas = lt.lista(3)
    if not all(isinstance(r, list) and len(r) in (3, 4) and all(isinstance(m, str) and _id(m) for m in r)
               for r in linhas):
        raise lt.erro(f"'{lt.a.nome}' são 3 linhas (claro, médio, escuro) de 3 ou 4 materiais")
    return {c: tuple(r) for c, r in zip(CLASSES, linhas, strict=True)}


def _inteiro(lt: _Leitura) -> int:
    x = lt.num(lt.v, lt.onde)
    if x != round(x):
        raise lt.erro(f"'{lt.a.nome}' é inteiro, deu {x}")
    return int(round(x))


def _pontos(lt: _Leitura) -> list[tuple[float, ...]]:
    return [_Leitura(lt.a, p, lt.env, f"{lt.onde}/{i}", lt.peca).numeros(3) for i, p in enumerate(lt.lista(None))]


def _vaos(lt: _Leitura) -> list[tuple[float, ...]]:
    return [_Leitura(lt.a, r, lt.env, f"{lt.onde}/{i}", lt.peca).numeros(4) for i, r in enumerate(lt.lista(None))]


LEITORES: dict[str, Callable[[_Leitura], Any]] = {
    "bool": _bool, "material": _material, "ancora": _ancora, "tons": _tons, "inteiro": _inteiro,
    "comprimento": lambda lt: lt.num(lt.v, lt.onde), "escalar": lambda lt: lt.num(lt.v, lt.onde),
    "ponto": lambda lt: lt.numeros(3), "pontos": _pontos, "faixa": lambda lt: lt.numeros(2),
    "fracoes": lambda lt: lt.numeros(None), "vaos": _vaos,
}


def ler_args(peca: Peca, brutos: dict[str, Any], env: dict[str, float], onde: str = "") -> dict[str, Any]:
    """Os argumentos da peça avaliados: recusa argumento fora do schema e falta de obrigatório; o que falta toma o
    padrão da peça."""
    nomes = {a.nome for a in peca.args}
    sobra = sorted(set(brutos) - nomes)
    if sobra:
        raise _erro(peca.id, f"argumento desconhecido {', '.join(sobra)} (aceita: {', '.join(sorted(nomes))})",
                    f"{onde}/args/{sobra[0]}")
    out: dict[str, Any] = {}
    for a in peca.args:
        v = brutos.get(a.nome, a.padrao)
        if v is None:
            raise _erro(peca.id, f"falta o argumento '{a.nome}' ({a.descricao})", f"{onde}/args")
        out[a.nome] = LEITORES[a.tipo](_Leitura(a, v, env, f"{onde}/args/{a.nome}", peca.id))
    return out


def vars_dos_args(peca: Peca, brutos: dict[str, Any]) -> set[str]:
    """As medidas que os argumentos (escritos ou padrão) usam: a composição confere antes de montar."""
    out: set[str] = set()

    def anda(v: Any) -> None:
        if isinstance(v, str):
            out.update(variaveis(compilar(v)))
        elif isinstance(v, list):
            for x in v:
                anda(x)

    for a in peca.args:
        if a.tipo not in ("material", "bool", "tons", "ancora"):
            anda(brutos.get(a.nome, a.padrao))
    return out


def ancoras_pedidas(peca: Peca, brutos: dict[str, Any]) -> list[str]:
    """As âncoras de outros nós que os argumentos citam (``'<nó>.<âncora>'``): a composição confere a ordem."""
    return [v for a in peca.args if a.tipo == "ancora" and isinstance(v := brutos.get(a.nome, a.padrao), str) and v]
