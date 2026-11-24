"""As peças de alvenaria: o muro de pedra em fiadas desencontradas (com vãos e empena) e o bocal redondo de pedra seca.

Cada pedra é uma face chapada que tira o tom da normal; a pedra só sorteia o desvio dela (algumas um degrau acima,
poucas um abaixo), sem olhar a posição.
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

from ...core.rng import Stream
from ..construtor import FLAT, UNLIT, Vec
from ..escala import K, m
from .construcao import ALVENARIA, pela_luz
from .peca import Arg, Ctx, Peca

TESTE = "tests/test_kit.py::test_cada_variacao_monta"
Vao = tuple[float, float, float, float]
X = Arg


def desvio_da_pedra(stream: Stream) -> int:
    r = stream.randint(0, 99)
    return 1 if r < 18 else -1 if r > 88 else 0


def _corta_no_vao(xs: tuple[float, float], zs: tuple[float, float], vaos: list[Vao]) -> tuple[float, float]:
    """A pedra (``xs`` de borda a borda, ``zs`` de base a topo) que encosta num vão é cortada na borda dele; a que cai
    dentro some (as bordas se igualam)."""
    a, c = xs
    zb, zt = zs
    for hx0, hx1, hz0, hz1 in vaos:
        if zb < hz1 + 0.5 * K and zt > hz0 - 0.5 * K and a < hx1 + 0.5 * K and c > hx0 - 0.5 * K:
            if a < hx0 - 0.5 * K:
                c = min(c, hx0 - 1.0 * K)
            elif c > hx1 + 0.5 * K:
                a = max(a, hx1 + 1.0 * K)
            else:
                c = a
    return a, c


def _pedra(ctx: Ctx, pid: str, xs: tuple[float, float], zs: tuple[float, float], y: float) -> None:
    """A pedra octogonal de tom inteiro, com 1 px de rejunte em volta e o topo que sobe ou desce um pouco."""
    (a, c), (zb, zt) = xs, zs
    ch = min(1.5 * K, (c - a) / 3, (zt - zb) / 3)
    dz = ctx.st.randint(-6, 6) / 10 * K
    pts = [(a + ch, y, zb), (c - ch, y, zb), (c, y, zb + ch), (c, y, zt - ch + dz), (c - ch, y, zt + dz),
           (a + ch, y, zt), (a, y, zt - ch), (a, y, zb + ch)]
    mat, tags = pela_luz(ALVENARIA, desvio_da_pedra(ctx.st))
    ctx.poly(pid, mat, pts, 1, tags)


class _Muro:
    """O muro em montagem: os argumentos, o topo (empena) e quantas pedras já foram desenhadas."""

    def __init__(self, c: Ctx, a: dict[str, Any]) -> None:
        self.c, self.a, self.n = c, a, 0
        x0, x1 = a["x0"], a["x1"]
        self.xc, self.meia = (x0 + x1) / 2, (x1 - x0) / 2

    def topo(self, x: float) -> float:
        return float(self.a["altura"] + self.a["empena"] * max(0.0, 1 - abs(x - self.xc) / self.meia))

    def fiada(self, z: float, row: int) -> float:
        """Uma fiada de altura sorteada a partir de ``z``; devolve a altura dela."""
        c, a = self.c, self.a
        x0, x1 = a["x0"], a["x1"]
        rh = (a["fiada"][0] / K, a["fiada"][1] / K)
        sw = (a["pedra"][0] / K, a["pedra"][1] / K)
        h = c.st.randint(int(rh[0] * 10), int(rh[1] * 10)) / 10 * K
        x = x0 - (c.st.randint(20, 70) / 10 * K if row % 2 else 0.0)
        while x < x1:
            w = c.st.randint(int(sw[0] * 10), int(sw[1] * 10)) / 10 * K
            zs = (z + 0.5 * K, z + h - 0.5 * K)
            xs = _corta_no_vao((max(x, x0) + 0.5 * K, min(x + w, x1) - 0.5 * K), zs, list(a["vaos"]))
            x += w
            if xs[1] - xs[0] < 2.5 * K or zs[1] > min(self.topo(xs[0]), self.topo(xs[1])) - 0.5 * K:
                continue
            _pedra(c, f"{c.pid}_s{self.n:03d}", xs, zs, a["y"])
            self.n += 1
        return h


def _muro(c: Ctx, a: dict[str, Any]) -> None:
    x0, x1, y, z0 = a["x0"], a["x1"], a["y"], a["z0"]
    mu = _Muro(c, a)
    if a["rejunte"]:  # a parede de baixo, que aparece entre as pedras
        pts = [(x0, y, z0), (x1, y, z0), (x1, y, mu.topo(x1)), *([(mu.xc, y, mu.topo(mu.xc))] if a["empena"] else []),
               (x0, y, mu.topo(x0))]
        c.poly(c.pid, "rejunte", pts, 0, (*FLAT, UNLIT))
    z, row = z0, 0
    while True:
        z += mu.fiada(z, row)
        row += 1
        if z >= max(mu.topo(x0), mu.topo(x1), mu.topo((x0 + x1) / 2)) - 2 * K:
            return


def _ponto(r: float, ang: float, z: float) -> Vec:
    return (r * math.cos(ang), r * math.sin(ang), z)


def anel(r: float, z: float, n: int, y0: float = 0.0) -> list[Vec]:
    """O círculo de raio ``r`` no plano z, de trás pela direita até a frente e de volta."""
    return [(r * math.cos(2 * math.pi * i / n), y0 + r * math.sin(2 * math.pi * i / n), z) for i in range(n)]


def _fiadas_do_bocal(c: Ctx, r: float, h: float, fiadas: int) -> list[list[float]]:
    """As pedras da meia-volta da frente, fiada a fiada, desencontradas; devolve os cortes de cada fiada."""
    cortes_por_fiada: list[list[float]] = []
    for f in range(fiadas):
        z0, z1 = h * f / fiadas, h * (f + 1) / fiadas
        n = c.st.randint(5, 6)
        desloca = (0.5 if f % 2 else 0.0) + c.st.randint(-12, 12) / 100
        fr = sorted({min(float(n), max(0.0, k + desloca)) for k in range(n + 1)} | {0.0, float(n)})
        cortes = [math.pi * x / n for x in fr]
        cortes_por_fiada.append(cortes)
        for k in range(len(cortes) - 1):
            a0, a1 = cortes[k], cortes[k + 1]
            if a1 - a0 < 0.05:
                continue
            base = [(a0 + (a1 - a0) * t / 3) for t in range(4)]
            pts = [_ponto(r, aa, z0) for aa in base] + [_ponto(r, aa, z1) for aa in reversed(base)]
            mat, tags = pela_luz(ALVENARIA, desvio_da_pedra(c.st))
            c.poly(f"stone_{f}_{k}", mat, pts, 2, tags)
    return cortes_por_fiada


def _bocal(c: Ctx, a: dict[str, Any]) -> None:
    """A meia-volta da frente em fiadas de pedra com as juntas desenhadas; a capa em anel, 4 cm para fora, com a sombra
    da borda; a boca escura com a parede de dentro (o revestimento de 25 cm) descendo no escuro."""
    r, h, fiadas = a["raio"], a["altura"], a["fiadas"]
    junta = ALVENARIA["shade"]
    pp = replace(c, grupo="parapet")
    cortes_por_fiada = _fiadas_do_bocal(pp, r, h, fiadas)
    for f in range(1, fiadas):
        pp.line(f"course_{f}", junta, [_ponto(r + 0.2, math.pi * i / 8, h * f / fiadas) for i in range(9)], 3)
    for f, cortes in enumerate(cortes_por_fiada):
        z0, z1 = h * f / fiadas, h * (f + 1) / fiadas
        for k, ang in enumerate(cortes[1:-1]):
            pp.line(f"joint_{f}_{k}", junta, [_ponto(r + 0.2, ang, z0), _ponto(r + 0.2, ang, z1)], 3)
    rb = r - m(0.25)
    cp = replace(c, grupo="coping")
    mat, tags = pela_luz(ALVENARIA, 0)
    cp.poly("coping", mat, anel(r + m(0.04), h + 0.4, 24), 5, tags)
    cp.line("coping_lip", junta, [_ponto(r + m(0.04), math.pi * i / 10, h - 0.3) for i in range(11)], 4)
    for j in range(5):
        ang = 2 * math.pi * (j + 0.2 + c.st.randint(0, 40) / 100) / 5
        cp.line(f"coping_joint_{j}", ALVENARIA["mid"], [_ponto(rb + 0.8, ang, h + 0.5),
                                                         _ponto(r + m(0.03), ang, h + 0.5)], 6)
    boca = replace(c, grupo="mouth")
    boca.poly("mouth", ALVENARIA["shade"], anel(rb, h + 0.6, 20), 7, (*FLAT, UNLIT))
    boca.poly("mouth_deep", "rejunte", anel(rb * 0.7, h + 0.7, 16, y0=rb * 0.3), 8, (*FLAT, UNLIT))


PECAS_PEDRA = [
    Peca("muro_fiadas", "Muro de pedra em fiadas desencontradas, com vãos e empena opcional", (
        X("x0", "comprimento", "borda esquerda"), X("x1", "comprimento", "borda direita"),
        X("y", "comprimento", "o plano da face (frente = +y)"), X("z0", "comprimento", "base", "0"),
        X("altura", "comprimento", "altura nas bordas"), X("empena", "comprimento", "quanto o meio sobe", "0"),
        X("vaos", "vaos", "[x0, x1, z0, z1] de cada vão (porta, janela)", []),
        X("fiada", "faixa", "altura da fiada", ["18cm", "24cm"]),
        X("pedra", "faixa", "largura da pedra", ["30cm", "50cm"]),
        X("rejunte", "bool", "a parede de baixo entre as pedras", True)),
        _muro, (("baixo", {"x0": "-1m", "x1": "1m", "y": "0", "altura": "70cm"}),
                ("com vão", {"x0": "-1m", "x1": "1m", "y": "0", "altura": "1.4m",
                             "vaos": [["-30cm", "30cm", "0", "1m"]]}),
                ("empena", {"x0": "-1m", "x1": "1m", "y": "0", "altura": "1m", "empena": "60cm"})),
        TESTE, (_muro, _Muro, _pedra, _corta_no_vao, desvio_da_pedra)),
    Peca("bocal", "Bocal redondo de pedra seca: fiadas desencontradas, capa em anel e a boca escura", (
        X("raio", "comprimento", "raio de fora"), X("altura", "comprimento", "altura até a capa"),
        X("fiadas", "inteiro", "fiadas de pedra", "3")),
        _bocal, (("baixo", {"raio": "70cm", "altura": "60cm", "fiadas": "2"}),
                 ("médio", {"raio": "70cm", "altura": "85cm"}), ("largo", {"raio": "1m", "altura": "80cm"})),
        TESTE, (_bocal, _fiadas_do_bocal, anel, desvio_da_pedra)),
]
