"""A carpintaria: o corpo de aduelas (balde, barril, tina) com os aros e o tampo, e o lanço de cerca de varas.

Cada aduela fica no plano dela, na corda do círculo: a normal dá a volta e a luz do estilo dá o tom; a tábua só
sorteia o desvio. O aro é o arco de verdade em volta do centro, e a câmera o curva.
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

from ..construtor import FLAT, LIT, Parte, bound_polygon, polyline, q, qv
from ..escala import K
from .construcao import TABUA, Lugar, Modo, sortear_tabua, tabua
from .peca import Arg, Ctx, Peca

TESTE = "tests/test_kit.py::test_cada_variacao_monta"
X = Arg


def _aduela(c: Ctx, a: dict[str, Any], i: int) -> None:
    (cx, cy, cz), raio, n, folga = a["centro"], a["raio"], a["n"], a["folga"]
    a0, a1 = math.pi * (1 - i / n), math.pi * (1 - (i + 1) / n)
    curva = a["bojo"] * abs(math.sin((a0 + a1) / 2)) * 0.5
    var = sortear_tabua(c.st, 0.5, 15, 0)
    p0 = (cx + raio * math.cos(a0), cy + raio * math.sin(a0), cz)
    p1 = (cx + raio * math.cos(a1), cy + raio * math.sin(a1), cz)
    corda = math.dist(p0, p1)
    v = ((p1[0] - p0[0]) / corda, (p1[1] - p0[1]) / corda, 0.0)
    o = (p0[0] + v[0] * folga / 2, p0[1] + v[1] * folga / 2, cz)
    tabua(c, f"{c.pid}_{i}", Lugar(o, (0, 0, 1), v, a["altura"], max(1.0, corda - folga)), var,
          Modo(0, a["aresta"], curva, luz=True))


def _aros_e_tampo(c: Ctx, a: dict[str, Any]) -> None:
    """Os aros de metal (o arco na altura de cada fração, que segue o bojo) e o tampo de tábuas no corte da madeira."""
    (cx, cy, cz), h, r_fim = a["centro"], a["altura"], a["raio"]
    big_r = r_fim + a["bojo"]
    aros = replace(c, grupo="hoops")
    for j, f in enumerate(a["aros"]):
        z = h * f
        rr = r_fim + (big_r - r_fim) * math.sin(math.pi * z / h)
        aros.line(f"{c.pid}_hoop_{j}", "metal", [(cx + (rr + 0.2) * math.cos(math.pi * t / 6),
                                                    cy + (rr + 0.2) * math.sin(math.pi * t / 6), cz + z)
                                                   for t in range(7)], 3)
    if not a["tampo"]:
        return
    tampo = replace(c, grupo="lid")
    oct_pts = [(cx + r_fim * math.cos(2 * math.pi * i / 10), cy + r_fim * math.sin(2 * math.pi * i / 10) * 0.95,
                cz + h) for i in range(10)]
    tampo.poly(f"{c.pid}_lid", "madeira_cortada", oct_pts, 4, (*FLAT, LIT))
    for j, yy in enumerate((-r_fim * 0.35, r_fim * 0.35)):
        seam = [qv(cx - r_fim * 0.85, cy + yy, cz + h + 0.05), qv(cx + r_fim * 0.85, cy + yy, cz + h + 0.05)]
        c.b.part(f"{c.pid}_lid_seam_{j}", TABUA["shade"], polyline(seam, 1),
                 Parte(group="lid", tags=("flat", "detail", "no_outline")))
        c.empilha(f"{c.pid}_lid_seam_{j}", 5, [(cx - r_fim, cy + yy, cz + h), (cx + r_fim, cy + yy, cz + h)])


def _aduelas(c: Ctx, a: dict[str, Any]) -> None:
    for i in range(a["n"]):
        _aduela(c, a, i)
    if a["aros"] or a["tampo"]:
        _aros_e_tampo(c, a)


def _mourao(c: Ctx, i: int, x: float, hp: float) -> None:
    lean = c.st.randint(-6, 6) / 10 * K
    geo = {"type": "tapered_polyline", "points_q8": [qv(x, 0, 0), qv(x + lean, 0, hp)],
           "radii_q8": [q(1.5 * K), q(1.3 * K)]}
    c.b.part(f"post_{i}", TABUA["shade"], geo,
             Parte(group=c.grupo, tags=("no_inner_outline",)))
    disco = [(x + lean + 1.2 * K * math.cos(math.pi * j / 4), 0.2 + 1.0 * K * math.sin(math.pi * j / 4), hp)
             for j in range(8)]
    c.b.part(f"post_top_{i}", TABUA["mid"], bound_polygon(disco), Parte(group=c.grupo, tags=(*FLAT, LIT)))


def _cercado(c: Ctx, a: dict[str, Any]) -> None:
    """Dois mourões de tronco e duas varas tortas (galho, não tábua); lanços lado a lado dividem o mourão da ponta."""
    lg, hp = a["meio_comprimento"], a["altura"]
    for i, sx in enumerate((-1, 1)):
        _mourao(c, i, sx * lg, hp)
    for j, z in enumerate((hp * 0.40, hp * 0.78)):
        sag = c.st.randint(4, 12) / 10 * K
        pts = [qv(-lg - 1.5 * K, 0.6, z + c.st.randint(-5, 5) / 10 * K), qv(-lg * 0.3, 0.6, z - sag),
               qv(lg * 0.35, 0.6, z - sag * 0.8), qv(lg + 1.5 * K, 0.6, z + c.st.randint(-5, 5) / 10 * K)]
        c.b.part(f"rail_{j}", TABUA["mid"], {"type": "tapered_polyline", "points_q8": pts,
                                             "radii_q8": [q(1.0 * K), q(0.9 * K), q(0.9 * K), q(1.0 * K)]},
                 Parte(group=c.grupo, tags=("no_inner_outline",)))
        c.b.part(f"rail_{j}_lit", TABUA["light"],
                 polyline([qv(-lg, 0.7, z + 0.6 * K), qv(-lg * 0.3, 0.7, z - sag + 0.6 * K)], 1),
                 Parte(group=c.grupo, tags=("flat", "detail", "no_outline")))
    c.regras.extend({"front": f"rail_{j}_lit", "back": f"rail_{j}"} for j in range(2))
    c.regras.extend({"front": f"rail_{j}", "back": f"post_{i}"} for j in range(2) for i in range(2))
    c.regras.extend({"front": f"post_top_{i}", "back": f"post_{i}"} for i in range(2))


PECAS_CARPINTARIA = [
    Peca("aduelas", "Corpo de aduelas (balde, tina, tonel): a meia-volta da frente, bojo, aros e tampo", (
        X("centro", "ponto", "centro do fundo", ["0", "0", "0"]), X("raio", "comprimento", "raio no fundo"),
        X("altura", "comprimento", "altura"), X("n", "inteiro", "aduelas na meia-volta", "7"),
        X("bojo", "comprimento", "o raio a mais no meio", "0"),
        X("folga", "comprimento", "fresta entre aduelas", "0.4px"),
        X("aros", "fracoes", "a altura de cada aro (fração)", []), X("tampo", "bool", "o tampo de tábuas", False),
        X("aresta", "bool", "a borda escura de cada aduela", True)),
        _aduelas, (("balde", {"raio": "14cm", "altura": "26cm", "n": "3", "aros": ["35%"], "aresta": False}),
                   ("tonel", {"raio": "25cm", "altura": "90cm", "n": "9", "bojo": "5cm",
                               "aros": ["15%", "50%", "85%"], "tampo": True}),
                   ("tina", {"raio": "45cm", "altura": "40cm", "n": "11", "aros": ["30%", "75%"]})),
        TESTE, (_aduelas, _aduela, _aros_e_tampo)),
    Peca("cercado", "Lanço de cerca de varas: dois mourões e duas varas tortas", (
        X("meio_comprimento", "comprimento", "do meio ao mourão"), X("altura", "comprimento", "altura do mourão")),
        _cercado, (("curto", {"meio_comprimento": "60cm", "altura": "70cm"}),
                   ("médio", {"meio_comprimento": "90cm", "altura": "80cm"}),
                   ("alto", {"meio_comprimento": "90cm", "altura": "1.1m"})),
        TESTE, (_cercado, _mourao)),
]
