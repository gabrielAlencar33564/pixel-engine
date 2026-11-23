"""Os vãos da parede: a porta de tábuas e a janela. Desenham numa face ``y`` e empilham na pilha da parede (batente e
verga na camada 2, tábuas e vidros na 3), por cima das pedras. O vidro aceso é a luz de dentro e não muda com a luz do
estilo."""

from __future__ import annotations

from typing import Any

from ..construtor import FLAT, UNLIT
from ..escala import K
from .construcao import ALVENARIA, DESVIO_DO_TOM, TABUA, pela_luz, retangulo
from .peca import Arg, Ctx, Peca

TESTE = "tests/test_kit.py::test_cada_variacao_monta"
X = Arg


def _porta(c: Ctx, a: dict[str, Any]) -> None:
    """Tábuas verticais com batente de pedra clara, travessa e tranca; a tábua do lado da luz é a mais clara."""
    x0, x1, h, y, n = a["x0"], a["x1"], a["altura"], a["y"], a["tabuas"]
    mat, tags = pela_luz(ALVENARIA, 1)
    c.poly(f"{c.pid}_jamb", mat, retangulo((x0 - 1.5 * K, x1 + 1.5 * K), (0, h + 2.5 * K), y), 2, tags)
    bw = (x1 - x0) / n
    tons = ("light", "mid", "shade") if n <= 3 else ("light", "mid", "mid", "shade")
    for i in range(n):
        mat, tags = pela_luz(TABUA, DESVIO_DO_TOM[tons[min(i, len(tons) - 1)]])
        c.poly(f"{c.pid}_b{i}", mat, retangulo((x0 + i * bw + 0.3, x0 + (i + 1) * bw - 0.3), (0, h), y), 3, tags)
    c.poly(f"{c.pid}_rail", TABUA["deep"], retangulo((x0, x1), (h * 0.62, h * 0.62 + 1.2 * K), y), 4)
    c.poly(f"{c.pid}_latch", "metal", retangulo((x1 - 3.0 * K, x1 - 1.6 * K), (h * 0.48, h * 0.48 + 1.4 * K), y), 5,
           ("flat", "detail"))


def _janela(c: Ctx, a: dict[str, Any]) -> None:
    """Verga e peitoril de pedra clara, caixilho de tábua e os quatro vidros acesos por dentro."""
    x0, x1, z0, z1, y = a["x0"], a["x1"], a["z0"], a["z1"], a["y"]
    mat, tags = pela_luz(ALVENARIA, 1)
    c.poly(f"{c.pid}_lintel", mat, retangulo((x0 - 1.5 * K, x1 + 1.5 * K), (z1, z1 + 2.2 * K), y), 2, tags)
    c.poly(f"{c.pid}_sill", mat, retangulo((x0 - 1.0 * K, x1 + 1.0 * K), (z0 - 1.5 * K, z0), y), 2, tags)
    mat, tags = pela_luz(TABUA, -1)
    c.poly(f"{c.pid}_frame", mat, retangulo((x0, x1), (z0, z1), y), 2, tags)
    mx, mz = (x0 + x1) / 2, (z0 + z1) / 2
    vidros = (((x0 + K, mx - 0.5 * K), (mz + 0.5 * K, z1 - K)), ((mx + 0.5 * K, x1 - K), (mz + 0.5 * K, z1 - K)),
              ((x0 + K, mx - 0.5 * K), (z0 + K, mz - 0.5 * K)), ((mx + 0.5 * K, x1 - K), (z0 + K, mz - 0.5 * K)))
    for i, (xs, zs) in enumerate(vidros):
        tags = ("flat", "no_inner_outline", "detail_light", UNLIT) if i == 1 else (*FLAT, UNLIT)
        c.poly(f"{c.pid}_pane{i}", "ambar" if i == 1 else "vidro_aceso", retangulo(xs, zs, y), 3, tags)


PECAS_VAOS = [
    Peca("porta", "Porta de tábuas verticais com batente de pedra, travessa e tranca", (
        X("x0", "comprimento", "borda esquerda"), X("x1", "comprimento", "borda direita"),
        X("altura", "comprimento", "altura"), X("y", "comprimento", "o plano da parede"),
        X("tabuas", "inteiro", "tábuas", "3")),
        _porta, (("estreita", {"x0": "-35cm", "x1": "35cm", "altura": "1.6m", "y": "0"}),
                 ("larga", {"x0": "-50cm", "x1": "50cm", "altura": "1.7m", "y": "0", "tabuas": "4"}),
                 ("baixa", {"x0": "-30cm", "x1": "30cm", "altura": "1.2m", "y": "0", "tabuas": "2"})),
        TESTE, (_porta,)),
    Peca("janela", "Janela pequena: verga e peitoril de pedra, caixilho e o vidro aceso", (
        X("x0", "comprimento", "borda esquerda"), X("x1", "comprimento", "borda direita"),
        X("z0", "comprimento", "peitoril"), X("z1", "comprimento", "verga"),
        X("y", "comprimento", "o plano da parede")),
        _janela, (("quadrada", {"x0": "-25cm", "x1": "25cm", "z0": "0", "z1": "50cm", "y": "0"}),
                  ("alta", {"x0": "-22cm", "x1": "22cm", "z0": "0", "z1": "70cm", "y": "0"}),
                  ("larga", {"x0": "-40cm", "x1": "40cm", "z0": "0", "z1": "45cm", "y": "0"})),
        TESTE, (_janela,)),
]
