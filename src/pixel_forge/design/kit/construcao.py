"""O kit de construção: as famílias de material (tábua, alvenaria, palha), o tom da face pela normal e a tábua com
as variações dela (tom, canto gasto, rachadura, nó, pregos), sorteadas pela semente do nó.

A face sai no tom do meio da família com ``lit_by_normal``: o render escolhe o degrau pela normal e pela luz do
estilo, e a peça declara só o desvio dela (``tone_up``, ``tone_down``). A tábua do piso e da face (o ``tabuado``)
fica no tom sorteado da variação, como a madeira gasta de um piso real.
Coordenadas: +X = direita da tela, +Y = frente (S), +Z = altura; px do mundo.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...core.rng import Stream
from ..construtor import FLAT, LIT, Vec
from .peca import Ctx

TABUA = {"light": "tabua_clara", "mid": "tabua", "shade": "tabua_escura", "deep": "tabua_funda"}
ALVENARIA = {"light": "alvenaria_clara", "mid": "alvenaria", "shade": "alvenaria_escura"}
PALHA = {"light": "palha_clara", "mid": "palha", "shade": "palha_escura"}
DESVIO = {1: "tone_up", -1: "tone_down"}
DESVIO_DO_TOM = {"light": 1, "mid": 0, "shade": -1}


def pela_luz(familia: dict[str, str], desvio: int) -> tuple[str, tuple[str, ...]]:
    """O material e as marcas da face que tira o tom da normal: o meio da família e o desvio da peça (−1, 0, 1)."""
    return familia["mid"], (*FLAT, LIT, *((DESVIO[desvio],) if desvio else ()))


def soma(v: Vec, w: Vec, s: float = 1.0) -> Vec:
    return (v[0] + w[0] * s, v[1] + w[1] * s, v[2] + w[2] * s)


def lerp(p: Vec, r: Vec, t: float) -> Vec:
    return (p[0] + (r[0] - p[0]) * t, p[1] + (r[1] - p[1]) * t, p[2] + (r[2] - p[2]) * t)


def retangulo(x: tuple[float, float], z: tuple[float, float], y: float) -> list[Vec]:
    """O retângulo de ``x[0]``–``x[1]`` por ``z[0]``–``z[1]`` no plano ``y`` (uma face de frente)."""
    return [(x[0], y, z[0]), (x[1], y, z[0]), (x[1], y, z[1]), (x[0], y, z[1])]


@dataclass(frozen=True)
class Tabua:
    """Uma variação de tábua: o tom (``light``, ``mid``, ``shade``), o canto da ponta gasto, a rachadura ao longo, o
    nó escuro e os pregos nas duas pontas."""

    tom: str = "mid"
    gasta: bool = False
    rachada: bool = False
    no: bool = False
    pregos: bool = False


def sortear_tabua(stream: Stream, luz: float, desgaste: int, pregos: int) -> Tabua:
    """A variação por semente. ``luz`` (0–1) puxa para o tom claro; ``desgaste`` e ``pregos``: as chances (%)."""
    r = stream.randint(0, 99)
    tom = "light" if r < 12 + int(36 * luz) else "shade" if r > 86 - int(10 * (1 - luz)) else "mid"
    return Tabua(tom, stream.randint(0, 99) < desgaste, stream.randint(0, 99) < 16, stream.randint(0, 99) < 20,
                 stream.randint(0, 99) < pregos)


@dataclass(frozen=True)
class Lugar:
    """Onde a tábua fica: o canto ``o``, o eixo ``u`` ao longo e ``v`` na largura (unitários), o comprimento e a
    largura em px."""

    o: Vec
    u: Vec
    v: Vec
    comp: float
    larg: float


@dataclass(frozen=True)
class Modo:
    """Como a tábua se desenha: a camada, a borda escura longe da luz, o bojo (as bordas compridas curvam para fora no
    meio, a aduela) e o tom pela normal (com ele, o tom da variação vira desvio)."""

    camada: int
    aresta: bool = True
    bojo: float = 0.0
    luz: bool = False


def _contorno(lg: Lugar, var: Tabua, bojo: float) -> list[Vec]:
    o, u, v, comp, larg = lg.o, lg.u, lg.v, lg.comp, lg.larg
    a, c = o, soma(o, u, comp)
    d, e = soma(o, v, larg), soma(soma(o, u, comp), v, larg)
    mid_l = soma(soma(o, u, comp / 2), v, -bojo)
    mid_r = soma(soma(soma(o, u, comp / 2), v, larg), v, bojo)
    pts = [a, mid_l, c, e, mid_r, d] if bojo else [a, c, e, d]
    if var.gasta:  # o canto da ponta comido em diagonal
        cut = min(1.4, larg * 0.45)
        i = pts.index(c)
        pts[i:i + 1] = [soma(c, u, -cut), soma(c, v, cut)]
    return pts


def _marcas(c: Ctx, pid: str, lg: Lugar, var: Tabua, camada: int) -> int:
    """A rachadura e o nó (sorteados) e os pregos nas pontas; devolve quantas partes desenhou."""
    o, u, v, comp, larg = lg.o, lg.u, lg.v, lg.comp, lg.larg
    n = 0
    if var.rachada and comp >= 8:
        s0, s1 = c.st.randint(20, 45) / 100, c.st.randint(55, 80) / 100
        w = c.st.randint(35, 65) / 100
        c.line(f"{pid}_rc", TABUA["deep"], [soma(soma(o, u, comp * s0), v, larg * w),
                                            soma(soma(o, u, comp * s1), v, larg * w)], camada + 1)
        n += 1
    if var.no and comp >= 6:
        s, w = c.st.randint(25, 75) / 100, c.st.randint(30, 70) / 100
        p = soma(soma(o, u, comp * s), v, larg * w)
        c.line(f"{pid}_no", TABUA["deep"], [p, soma(p, u, 0.6)], camada + 1)
        n += 1
    if var.pregos and larg >= 2.0:
        for j, s in enumerate((1.0, comp - 1.0)):
            p = soma(soma(o, u, s), v, larg / 2)
            c.line(f"{pid}_pr{j}", "metal", [p, soma(p, u, 0.3)], camada + 2)
            n += 1
    return n


def tabua(c: Ctx, pid: str, lg: Lugar, var: Tabua, modo: Modo) -> int:
    """A tábua com a variação dela; devolve quantas partes desenhou."""
    if modo.luz:
        mat, tags = pela_luz(TABUA, DESVIO_DO_TOM[var.tom])
    else:
        mat, tags = TABUA[var.tom], FLAT
    c.poly(pid, mat, _contorno(lg, var, modo.bojo), modo.camada, tags)
    n = 1
    if modo.aresta and lg.larg >= 2.0:
        d, e = soma(lg.o, lg.v, lg.larg), soma(soma(lg.o, lg.u, lg.comp), lg.v, lg.larg)
        c.line(f"{pid}_ar", TABUA["deep"], [soma(d, lg.v, -0.35), soma(e, lg.v, -0.35)], modo.camada + 1)
        n += 1
    return n + _marcas(c, pid, lg, var, modo.camada)
