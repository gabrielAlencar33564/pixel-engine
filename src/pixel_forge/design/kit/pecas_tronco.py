"""O tronco e os galhos: o tronco em pé como sólido de revolução (o volume e a textura do material fazem a sombra, a
base e as marcas), os galhos finos de 1 px entre as massas e os galhos grossos em leque do topo do tronco até a copa,
que deixam a âncora das pontas para a folhagem pôr um cacho em cada uma."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..construtor import LINE, Parte, polygon, polyline, q, qv
from ..escala import K
from .peca import Arg, Ctx, Peca

TESTE = "tests/test_kit.py::test_cada_variacao_monta"
X = Arg
COPA = X("copa", "ponto", "a copa: meia largura, meia altura e a altura do centro")
COPA_V = ["1.1m", "1.3m", "2.6m"]
OssoDaAltura = Callable[[float], tuple[str, float]]


def _tronco(c: Ctx, a: dict[str, Any]) -> None:
    """O sólido de revolução que afina e inclina pelas estações: a base em arco, o topo em tampa oval."""
    h, b0, b1, lean = a["altura"], a["base"], a["topo"], a["inclinacao"]
    st = [[q(h * i / 20), q((b0 + (b1 - b0) * i / 20) / 2), q(lean * (i / 20) ** 2)] for i in range(21)]
    c.b.part(c.pid, a["casca"], {"type": "revolution", "origin_q8": qv(0, 0, 0), "stations": st},
             Parte(bone=c.osso(0.0)[0], group=c.grupo))


@dataclass(frozen=True)
class Galho:
    """Um galho fino: o osso, a origem (q8), a base (x, z), a direção (rad), o comprimento e a curva para fora."""

    bone: str
    origin: list[int]
    base: tuple[float, float]
    ang: float
    length: float
    bend: float


def twig(c: Ctx, pid: str, g: Galho, material: str) -> None:
    dx, dz = math.cos(g.ang), math.sin(g.ang)
    x0, z0 = g.base
    mid = (x0 + dx * g.length * 0.5 - dz * g.bend, z0 + dz * g.length * 0.5 + dx * g.bend)
    end = (x0 + dx * g.length, z0 + dz * g.length)
    pts = [[g.origin[0] + q(x), g.origin[1], g.origin[2] + q(z)] for x, z in ((x0, z0), mid, end)]
    c.b.part(pid, material, polyline(pts, 1), Parte(bone=g.bone, group=c.grupo, tags=LINE))


def _galhos_finos(c: Ctx, a: dict[str, Any]) -> None:
    """Um galho por lado de ``lados``, subindo ``passo`` a cada um, no ângulo e no comprimento sorteados."""
    (a0, a1), (l0, l1) = a["angulo"], a["comprimento"]
    for i, lado in enumerate(a["lados"]):
        bone, zl = c.osso(a["base"] + i * a["passo"])
        ang = math.radians(90) + lado * (a0 + (a1 - a0) * c.st.randint(0, 100) / 100)
        twig(c, f"{c.pid}_{i}", Galho(bone, qv(0, a["profundidade"], zl), (0.0, 0.0), ang,
                                      l0 + (l1 - l0) * c.st.randint(0, 100) / 100, lado * a["curva"]), a["material"])


@dataclass(frozen=True)
class Curva:
    """O galho grosso: a Bézier quadrática de ``p0`` por ``ctrl`` até ``p1`` no plano xz, afinando de ``w0`` a ``w1``,
    na profundidade ``y``."""

    p0: tuple[float, float]
    ctrl: tuple[float, float]
    p1: tuple[float, float]
    w: tuple[float, float]
    y: float


def _linhas(cv: Curva, osso: OssoDaAltura) -> list[tuple[Any, ...]]:
    (x0, z0), (cx, cz), (x1, z1) = cv.p0, cv.ctrl, cv.p1
    n = max(4, round(math.hypot(x1 - x0, z1 - z0) / (2.5 * K)))
    rows = []
    for i in range(n + 1):
        s = i / n
        x = (1 - s) ** 2 * x0 + 2 * (1 - s) * s * cx + s * s * x1
        z = (1 - s) ** 2 * z0 + 2 * (1 - s) * s * cz + s * s * z1
        tx, tz = 2 * (1 - s) * (cx - x0) + 2 * s * (x1 - cx), 2 * (1 - s) * (cz - z0) + 2 * s * (z1 - cz)
        m = math.hypot(tx, tz) or 1.0
        nx, nz = -tz / m, tx / m
        if nz < 0 or (abs(nz) < 1e-9 and nx > 0):  # "de cima" = normal com z positivo
            nx, nz = -nx, -nz
        bone, zl = osso(z)
        rows.append((x, z, nx, nz, cv.w[0] + (cv.w[1] - cv.w[0]) * s, (bone, z - zl)))
    return rows


def _trechos(rows: list[tuple[Any, ...]]) -> list[list[int]]:
    """O galho cortado em trechos por osso; o trecho seguinte repete o último ponto (sem fresta na emenda)."""
    runs: list[list[int]] = []
    for i, r in enumerate(rows):
        if runs and rows[runs[-1][0]][5][0] == r[5][0]:
            runs[-1].append(i)
        else:
            if runs:
                runs[-1].append(i)
            runs.append([i])
    return runs


def limb(c: Ctx, pid: str, cv: Curva, osso: OssoDaAltura, mats: tuple[str, str]) -> list[tuple[float, float]]:
    """O galho grosso em trechos por osso da cadeia (o degrau do balanço fica no meio do galho), com o traço de luz em
    cima onde ele tem 2,5 px ou mais. Devolve os pontos do eixo (para a bifurcação)."""
    rows = _linhas(cv, osso)
    for j, run in enumerate(_trechos(rows)):
        if len(run) < 2:
            continue
        bone, zb = rows[run[0]][5]
        o = qv(0, cv.y, -zb)
        up = [(rows[i][0] + rows[i][2] * rows[i][4] / 2, rows[i][1] + rows[i][3] * rows[i][4] / 2) for i in run]
        lo = [(rows[i][0] - rows[i][2] * rows[i][4] / 2, rows[i][1] - rows[i][3] * rows[i][4] / 2) for i in run]
        bid = f"{pid}_{j}"
        c.b.part(bid, mats[0], polygon(o, [[q(x), q(z)] for x, z in up + lo[::-1]]),
                 Parte(bone=bone, group=c.grupo, tags=("flat", "no_inner_outline")))
        pts = [[q(rows[i][0] + rows[i][2] * (rows[i][4] / 2 - 0.6 * K)), o[1],
                q(rows[i][1] + rows[i][3] * (rows[i][4] / 2 - 0.6 * K)) + o[2]] for i in run if rows[i][4] >= 2.5 * K]
        if len(pts) >= 2:
            c.b.part(f"{bid}_lit", mats[1], polyline(pts, 1), Parte(bone=bone, group=c.grupo, tags=LINE))
            c.regras.append({"front": f"{bid}_lit", "back": bid})
    return [(r[0], r[1]) for r in rows]


def _bifurca(c: Ctx, j: int, eixo: list[tuple[float, float]], saida: tuple[float, float], a: dict[str, Any]
             ) -> tuple[float, float, float]:
    """O galho fino que sai a 2/3 do grosso, sempre para cima; devolve a ponta dele. ``saida``: a altura de saída do
    grosso e a profundidade dele."""
    (x1, z1), (z0, y) = eixo[-1], saida
    i = len(eixo) * 2 // 3
    (fx, fz), (gx, gz) = eixo[i], eixo[min(i + 1, len(eixo) - 1)]
    lado = 1 if x1 >= 0 else -1
    ang = math.atan2(gz - fz, gx - fx) + lado * math.radians(35)
    ang = ang if math.sin(ang) > 0 else math.atan2(abs(math.sin(ang)), math.cos(ang))
    bone, zl = _osso_do_galho(c)(fz)
    ln = math.hypot(x1, z1 - z0) * 0.35
    twig(c, f"{c.pid}_{j}_fork", Galho(bone, qv(0, y, zl), (fx, 0.0), ang, ln, lado * 0.8 * K), a["material"])
    return fx + math.cos(ang) * ln, fz + math.sin(ang) * ln, y


def _osso_do_galho(c: Ctx) -> OssoDaAltura:
    def osso(z: float) -> tuple[str, float]:  # abaixo da cadeia, o galho fica no tronco
        return ("trunk", z) if c.cadeia and z < c.cadeia[0][1] else c.osso(z)

    return osso


def _galhos_grossos(c: Ctx, a: dict[str, Any]) -> None:
    """O galho ``j`` de ``n`` aponta para a fração da largura dele; a ponta sobe no meio e desce nos de fora; com
    ``espalha``, o de ponta mais alta sai mais alto (andares). Deixa a âncora ``pontas`` (x, z, y)."""
    meia_l, meia_a, cz = a["copa"]
    (v0, v1), st, m = a["ponta_v"], c.st, a["n"]
    pontas = []
    for j in range(m):
        u = (-1 + (2 * j + 1) / m + st.randint(-30, 30) / 100 / m) * a["alcance"]
        v = v1 - (v1 - v0) * abs(u) + st.randint(-100, 100) / 1000
        z1, x1 = cz + v * meia_a, u * meia_l
        z0 = a["base"] * (1 + a["espalha"] * min(1.0, max(0.0, (v - v0) / max(1e-3, v1 - v0))))
        w0 = a["largura"][0] + (a["largura"][1] - a["largura"][0]) * st.randint(0, 100) / 100
        y = a["profundidade"][0] + (a["profundidade"][1] - a["profundidade"][0]) * st.randint(0, 100) / 100
        eixo = limb(c, f"{c.pid}_{j}", Curva((0.0, z0), (x1 * 0.25, z0 + (z1 - z0) * 0.75), (x1, z1),
                                              (w0, a["ponta"]), y), _osso_do_galho(c), (a["material"], a["claro"]))
        pontas.append((x1, z1, y))
        if st.randint(0, 999) < a["bifurca"] * 1000:
            pontas.append(_bifurca(c, j, eixo, (z0, y), a))
    c.deixa("pontas", pontas)


PECAS_TRONCO = [
    Peca("tronco_em_pe", "Tronco em pé, sólido de revolução que afina e inclina: o volume e a textura da casca fazem a "
         "sombra e o veio", (
             X("altura", "comprimento", "até onde ele sobe"), X("base", "comprimento", "a largura no chão"),
             X("topo", "comprimento", "a largura em cima"), X("inclinacao", "comprimento", "quanto o topo desvia", "0"),
             X("casca", "material", "a casca (casca, casca_clara)")),
        _tronco, (("fino", {"altura": "2.4m", "base": "13cm", "topo": "8cm", "casca": "casca_clara"}),
                  ("grosso", {"altura": "1.6m", "base": "28cm", "topo": "20cm", "casca": "casca"}),
                  ("inclinado", {"altura": "2m", "base": "20cm", "topo": "14cm", "inclinacao": "10cm",
                                 "casca": "casca"})),
        TESTE, (_tronco,)),
    Peca("galhos_finos", "Galhos finos de 1 px entre as massas da copa, um por lado, subindo", (
        X("base", "comprimento", "a altura do primeiro"), X("passo", "comprimento", "quanto cada um sobe"),
        X("lados", "fracoes", "o lado de cada um (-1 esquerda, 1 direita)"),
        X("angulo", "faixa", "o ângulo a partir da vertical", ["30deg", "50deg"]),
        X("comprimento", "faixa", "o comprimento"), X("curva", "comprimento", "a curva para fora", "0.8px"),
        X("profundidade", "comprimento", "a profundidade (atrás das massas)", "-0.5px"),
        X("material", "material", "a casca", "casca")),
        _galhos_finos, (("três", {"base": "1m", "passo": "40cm", "lados": ["-1", "1", "-1"],
                                  "comprimento": ["30cm", "36cm"], "material": "casca_clara"}),
                        ("dois", {"base": "70cm", "passo": "30cm", "lados": ["-1", "1"],
                                  "comprimento": ["20cm", "25cm"]}),
                        ("abertos", {"base": "1m", "passo": "20cm", "lados": ["-1", "1", "1"],
                                     "angulo": ["50deg", "70deg"], "comprimento": ["40cm", "60cm"]})),
        TESTE, (_galhos_finos, twig)),
    Peca("galhos_grossos", "Galhos grossos em leque do topo do tronco até a copa, com bifurcação; deixa as pontas", (
        X("base", "comprimento", "a altura de saída"), X("espalha", "escalar", "o mais alto sai tanto mais alto", "0"),
        COPA, X("n", "inteiro", "galhos"), X("alcance", "escalar", "a fração da largura que eles alcançam", "0.9"),
        X("ponta_v", "faixa", "a altura das pontas na copa (de -1 a 1): nos de fora e no meio", ["-0.4", "0.6"]),
        X("largura", "faixa", "a largura na saída"), X("ponta", "comprimento", "a largura na ponta"),
        X("profundidade", "faixa", "a profundidade", ["-2.2px", "0px"]),
        X("bifurca", "escalar", "a chance de um galho fino a 2/3", "0.5"), X("material", "material", "a casca"),
        X("claro", "material", "o traço de luz em cima")),
        _galhos_grossos, (("em leque", {"base": "1.1m", "copa": COPA_V, "n": "5", "largura": ["12cm", "16cm"],
                                        "ponta": "4cm", "material": "tabua_escura", "claro": "casca"}),
                          ("andares", {"base": "70cm", "espalha": "0.7", "copa": COPA_V, "n": "4",
                                       "ponta_v": ["-0.7", "0.7"], "largura": ["12cm", "17cm"], "ponta": "5cm",
                                       "bifurca": "0.9", "material": "tabua_escura", "claro": "casca"}),
                          ("aberto", {"base": "1.2m", "copa": COPA_V, "n": "7", "alcance": "1",
                                      "largura": ["12cm", "17cm"], "ponta": "5cm", "material": "casca",
                                      "claro": "madeira_cortada"})),
        TESTE, (_galhos_grossos, limb, _linhas, _trechos, _bifurca, _osso_do_galho, twig), ancoras=("pontas",)),
]
