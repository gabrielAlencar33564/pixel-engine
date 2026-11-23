"""As formas genéricas: o polígono, o traço, o elipsoide e os fios de palha num domo. São o detalhe que não é uma peça
de construção (a sombra do beiral, a manivela, o monte de feno), sem Python por asset."""

from __future__ import annotations

import math
from typing import Any

from ..construtor import FLAT, LINE, LIT, UNLIT, Parte, ellipse, polyline, q, qv
from ..escala import K
from .peca import Arg, Ctx, Peca

TESTE = "tests/test_kit.py::test_cada_variacao_monta"
QUATRO = ("S", "E", "N", "W")  # a forma genérica desenha qualquer vista (o tom e o volume saem no render)
X = Arg


def _poligono(c: Ctx, a: dict[str, Any]) -> None:
    """Uma face chapada pelos pontos, com o tom pela normal; sem ela, o material fica como está (a sombra do beiral)."""
    c.poly(c.pid, a["material"], list(a["pontos"]), c.camada, (*FLAT, LIT) if a["pela_normal"] else (*FLAT, UNLIT))


def _traco(c: Ctx, a: dict[str, Any]) -> None:
    """Um traço pelos pontos: de ``largura`` px (o detalhe, sem contorno) ou roliço de ``raio`` (com contorno)."""
    pts = list(a["pontos"])
    if a["raio"] > 0:
        geo = {"type": "tapered_polyline", "points_q8": [qv(*p) for p in pts], "radii_q8": [q(a["raio"])] * len(pts)}
        c.b.part(c.pid, a["material"], geo, Parte(group=c.grupo, tags=("no_inner_outline",)))
    else:
        c.b.part(c.pid, a["material"], polyline([qv(*p) for p in pts], a["largura"]), Parte(group=c.grupo, tags=LINE))
    c.pilha.add(c.pid, c.camada, pts)


def _elipsoide(c: Ctx, a: dict[str, Any]) -> None:
    """Um elipsoide; com ``volume``, sombreado como esfera pixel a pixel e no mesmo grupo de sombra dos outros
    elipsoides de volume do grupo (o domo e o topo de um monte)."""
    (x, y, z), (rx, ry, rz) = a["centro"], a["raios"]
    tags = ("volume_sphere", "shade_group") if a["volume"] else ()
    c.b.part(c.pid, a["material"], ellipse(qv(x, y, z), qv(rx, ry, rz)), Parte(group=c.grupo, tags=tags))
    c.pilha.add(c.pid, c.camada, [(x - rx, y + ry, z - rz), (x + rx, y + ry, z + rz)])


def _fio(c: Ctx, pid: str, mat: str, pts: list[tuple[float, float, float]]) -> None:
    c.b.part(pid, mat, polyline([qv(*p) for p in pts], 1), Parte(group=c.grupo, tags=LINE))
    c.pilha.add(pid, c.camada, pts)


def _fios(c: Ctx, a: dict[str, Any]) -> None:
    """Fios curtos de palha na frente de um domo (o elipsoide de centro a 45 % da altura), quase verticais, os do lado
    esquerdo às vezes claros; na base, a franja de fios soltos, para o monte não ser um ovo liso."""
    r, h = a["raio"], a["altura"]
    for i in range(a["n"]):
        u, v = c.st.randint(-85, 85) / 100, c.st.randint(20, 85) / 100
        x0 = u * r * math.sqrt(max(0.0, 1 - (v - 0.45) ** 2 / 0.3))
        z0 = h * v
        y0 = r * 0.85 * math.sqrt(max(0.0, 1 - (x0 / r) ** 2 - ((z0 - h * 0.45) / (h * 0.55)) ** 2)) + 0.4
        ln = c.st.randint(30, 60) / 10 * K
        mat = a["claro"] if u < -0.1 and c.st.randint(0, 9) > 3 else a["material"]
        _fio(c, f"{c.pid}_{i:02d}", mat, [(x0, y0, z0), (x0 + u * 1.2 * K, y0 + 0.5, z0 - ln)])
    n = a["franja"]
    for i in range(n):
        x = (-0.8 + 1.6 * i / max(1, n - 1)) * r
        _fio(c, f"{c.pid}_franja_{i}", a["escuro"], [(x, r * 0.6, 1.5 * K),
                                                     (x + c.st.randint(-15, 15) / 10 * K, r * 0.75, 0.0)])


PONTOS_RET = [["-30cm", "0", "0"], ["30cm", "0", "0"], ["30cm", "0", "40cm"], ["-30cm", "0", "40cm"]]
PECAS_FORMAS = [
    Peca("poligono", "Face chapada pelos pontos (até 32), com o tom pela normal ou o material como está", (
        X("pontos", "pontos", "os vértices, em ordem"), X("material", "material", "o material"),
        X("pela_normal", "bool", "o tom pela normal e pela luz do estilo", True)),
        _poligono, (("de frente", {"pontos": PONTOS_RET, "material": "tabua"}),
                    ("deitado", {"pontos": [["-30cm", "-20cm", "20cm"], ["30cm", "-20cm", "20cm"],
                                            ["30cm", "20cm", "20cm"], ["-30cm", "20cm", "20cm"]],
                                 "material": "alvenaria"}),
                    ("sombra", {"pontos": PONTOS_RET, "material": "rejunte", "pela_normal": False})),
        TESTE, (_poligono,), vistas=QUATRO),
    Peca("traco", "Traço pelos pontos: fino (detalhe, sem contorno) ou roliço de raio", (
        X("pontos", "pontos", "o caminho"), X("material", "material", "o material"),
        X("largura", "inteiro", "px do traço fino", "1"), X("raio", "comprimento", "raio do traço roliço", "0")),
        _traco, (("fino", {"pontos": [["-30cm", "0", "20cm"], ["30cm", "0", "20cm"]], "material": "metal"}),
                 ("largo", {"pontos": [["0", "0", "40cm"], ["0", "0", "0"]], "material": "metal", "largura": "2"}),
                 ("roliço", {"pontos": [["-40cm", "0", "20cm"], ["40cm", "0", "20cm"]], "material": "palha_escura",
                             "raio": "5cm"})),
        TESTE, (_traco,), vistas=QUATRO),
    Peca("elipsoide", "Elipsoide de centro e raios; com volume, sombreado como esfera", (
        X("centro", "ponto", "o centro"), X("raios", "ponto", "os três raios"), X("material", "material", "o material"),
        X("volume", "bool", "volume por pixel (esfera)", True)),
        _elipsoide, (("domo", {"centro": ["0", "0", "25cm"], "raios": ["50cm", "42cm", "30cm"], "material": "fibra"}),
                     ("bola", {"centro": ["0", "0", "20cm"], "raios": ["20cm", "20cm", "20cm"], "material": "pedra"}),
                     ("chapado", {"centro": ["0", "0", "10cm"], "raios": ["30cm", "20cm", "10cm"],
                                  "material": "pedra", "volume": False})),
        TESTE, (_elipsoide,), vistas=QUATRO),
    Peca("fios", "Fios curtos de palha na frente de um domo e a franja solta na base", (
        X("raio", "comprimento", "raio da base do domo"), X("altura", "comprimento", "altura do domo"),
        X("n", "inteiro", "fios no domo", "16"), X("franja", "inteiro", "fios soltos na base", "6"),
        X("material", "material", "o fio comum", "palha"), X("claro", "material", "o fio claro", "palha_clara"),
        X("escuro", "material", "a franja", "palha_escura")),
        _fios, (("monte", {"raio": "50cm", "altura": "60cm"}), ("ralo", {"raio": "50cm", "altura": "60cm", "n": "6"}),
                ("alto", {"raio": "40cm", "altura": "90cm", "n": "20", "franja": "4"})),
        TESTE, (_fios, _fio)),
]
