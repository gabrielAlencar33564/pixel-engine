"""Os telhados: a água de palha em fiadas com fios curtos, e as duas águas de tabuinhas com a empena de frente.

Cada face tira o tom da normal (a água da esquerda clareia e a da direita escurece pela luz do estilo); os traços
(fios de palha, juntas, beiras) são marcas de desenho e ficam no tom que a peça diz.
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

from ..construtor import Vec
from ..escala import K, m
from .construcao import PALHA, TABUA, lerp, pela_luz
from .peca import Arg, Ctx, Peca

TESTE = "tests/test_kit.py::test_cada_variacao_monta"
X = Arg


def _fios(c: Ctx, pid: str, faixa: tuple[Vec, Vec, Vec, Vec], claros: bool) -> None:
    """Os fios curtos de palha de uma fiada, quase na vertical; os do lado da luz às vezes claros."""
    a0, a1, c1, c0 = faixa
    strands = max(1, int(math.dist(a0, a1) / (7.5 * K)))
    for s in range(strands):
        u = (s + 0.5 + c.st.randint(-30, 30) / 100) / strands
        v0, v1 = c.st.randint(10, 30) / 100, c.st.randint(65, 95) / 100
        top = lerp(lerp(a0, a1, u), lerp(c0, c1, u), v1)
        bot = lerp(lerp(a0, a1, u + c.st.randint(-4, 4) / 100), lerp(c0, c1, u), v0)
        lit = claros and u < 0.5 and c.st.randint(0, 9) > 4
        tom = PALHA["light"] if lit else (PALHA["shade"] if claros else TABUA["shade"])
        c.line(f"{pid}_f{s:02d}", tom, [top, bot], 1)


def _palha(c: Ctx, a: dict[str, Any]) -> None:
    """O quadrilátero (beiral esq., beiral dir., cume dir., cume esq.; triângulo com os dois últimos iguais) em
    ``fiadas`` faixas do beiral ao cume, sem linha entre elas (a linha fazia a palha ler como tábua)."""
    e0, e1, r1, r0 = a["beiral_esq"], a["beiral_dir"], a["cume_dir"], a["cume_esq"]
    mat, tags = pela_luz(PALHA, 0)
    n = a["fiadas"]
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        faixa = (lerp(e0, r0, t0), lerp(e1, r1, t0), lerp(e1, r1, t1), lerp(e0, r0, t1))
        c.poly(f"{c.pid}_c{k}", mat, list(faixa), 0, tags)
        _fios(c, f"{c.pid}_c{k}", faixa, a["fios_claros"])


def _empena(c: Ctx, x: float, d: float, zs: tuple[float, float]) -> None:
    """O triângulo sob as duas águas, ``d`` px à frente do eixo: 5 tábuas em pé, uma sim outra não na sombra, e as duas
    tábuas da beira seguindo as águas."""
    zb, zc = zs

    def alto(xx: float) -> float:
        return zb + (zc - zb) * (1 - abs(xx) / x)

    for i in range(5):
        xa, xb = -x + 2 * x * i / 5 + 0.3, -x + 2 * x * (i + 1) / 5 - 0.3
        topo = [(xb, d + 0.2, alto(xb)), *([(0.0, d + 0.2, zc)] if xa < 0 < xb else []), (xa, d + 0.2, alto(xa))]
        mat, tags = pela_luz(TABUA, 0 if i % 2 else -1)
        c.poly(f"gable_{i}", mat, [(xa, d + 0.2, zb), (xb, d + 0.2, zb), *topo], 30, tags)
    for lado, sx in (("l", -1), ("r", 1)):
        c.line(f"barge_{lado}", TABUA["deep"], [(sx * (x + 0.5), d + 0.4, zb - 0.6), (0.0, d + 0.4, zc + 0.6)], 31, 2)


def _agua_de_tabuinhas(c: Ctx, lado: tuple[str, int], i: int, a: dict[str, Any]) -> None:
    """A fiada ``i`` de uma água: a face, a borda escura de baixo e as juntas curtas desencontradas a cada 20 cm."""
    x, d, zb, zc, n = a["meia_largura"], a["meio_fundo"], a["beiral"], a["cume"], a["fiadas"]
    nome, sx = lado
    t0, t1 = i / n, min(1.0, (i + 1) / n + 0.08)
    x0, x1 = sx * x * (1 - t0), sx * x * (1 - t1)
    z0, z1 = zb + (zc - zb) * t0, zb + (zc - zb) * t1
    mat, tags = pela_luz(TABUA, 0)
    pid = f"roof_{nome}_{i}"
    c.poly(pid, mat, [(x0, -d, z0), (x1, -d, z1), (x1, d, z1), (x0, d, z0)], 20 + i, tags)
    c.line(f"{pid}_edge", TABUA["deep"], [(x0, -d, z0 - 0.3), (x0, d, z0 - 0.3)], 20 + i)
    y = -d + c.st.randint(0, 6) / 10 + (m(0.1) if i % 2 else 0.0)
    k = 0
    while y + m(0.2) < d:
        y += m(0.2)
        c.line(f"{pid}_j{k}", TABUA["deep"], [(x0, y, z0 - 0.2), (x0 * 0.6 + x1 * 0.4, y, z0 * 0.6 + z1 * 0.4)],
               20 + i)
        k += 1


def _tabuinhas(c: Ctx, a: dict[str, Any]) -> None:
    """Duas águas de tabuinhas com a cumeeira de frente para trás: de frente aparece a empena, e por cima dela as duas
    águas subindo para trás."""
    r = replace(c, grupo="roof")
    for lado in (("l", -1), ("r", 1)):
        for i in range(a["fiadas"]):
            _agua_de_tabuinhas(r, lado, i, a)
    if a["empena"]:
        _empena(r, a["meia_largura"], a["meio_fundo"], (a["beiral"], a["cume"]))
    r.line("ridge", TABUA["deep"], [(0.0, -a["meio_fundo"], a["cume"] + 0.4), (0.0, a["meio_fundo"], a["cume"] + 0.4)],
           31)


PECAS_TELHADO = [
    Peca("telhado_palha", "Uma água de palha em fiadas com fios curtos (quadrilátero ou triângulo)", (
        X("beiral_esq", "ponto", "canto do beiral à esquerda"), X("beiral_dir", "ponto", "canto do beiral à direita"),
        X("cume_dir", "ponto", "ponta da cumeeira à direita"), X("cume_esq", "ponto", "ponta da cumeeira à esquerda"),
        X("fiadas", "inteiro", "fiadas do beiral ao cume", "4"),
        X("fios_claros", "bool", "fios de palha claros entre os escuros (a água do lado da luz)", True)),
        _palha, (("água da frente", {"beiral_esq": ["-1m", "50cm", "0"], "beiral_dir": ["1m", "50cm", "0"],
                                     "cume_dir": ["50cm", "0", "60cm"], "cume_esq": ["-50cm", "0", "60cm"]}),
                 ("quadril", {"beiral_esq": ["-1m", "-50cm", "0"], "beiral_dir": ["-1m", "50cm", "0"],
                              "cume_dir": ["-50cm", "0", "60cm"], "cume_esq": ["-50cm", "0", "60cm"], "fiadas": "3"}),
                 ("sem fio claro", {"beiral_esq": ["-1m", "50cm", "0"], "beiral_dir": ["1m", "50cm", "0"],
                                    "cume_dir": ["50cm", "0", "60cm"], "cume_esq": ["-50cm", "0", "60cm"],
                                    "fios_claros": False})),
        TESTE, (_palha, _fios)),
    Peca("telhado_tabuinhas", "Duas águas de tabuinhas, cumeeira de frente para trás, com a empena", (
        X("meia_largura", "comprimento", "do eixo ao beiral"), X("meio_fundo", "comprimento", "do eixo à frente"),
        X("beiral", "comprimento", "altura do beiral"), X("cume", "comprimento", "altura da cumeeira"),
        X("fiadas", "inteiro", "fiadas de tabuinhas por água", "3"), X("empena", "bool", "a empena de frente", True)),
        _tabuinhas, (("alto", {"meia_largura": "1m", "meio_fundo": "42cm", "beiral": "2m", "cume": "2.5m"}),
                     ("raso", {"meia_largura": "1m", "meio_fundo": "40cm", "beiral": "1m", "cume": "1.25m"}),
                     ("sem empena", {"meia_largura": "80cm", "meio_fundo": "60cm", "beiral": "1m", "cume": "1.5m",
                                     "fiadas": "4", "empena": False})),
        TESTE, (_tabuinhas, _agua_de_tabuinhas, _empena)),
]
