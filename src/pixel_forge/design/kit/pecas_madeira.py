"""As peças de madeira e de amarração: a parede de tábuas, o poste, a viga, o tabuado (piso ou face), a corda e o aro
de metal. A face de tábua tira o tom da normal; o tabuado fica no tom sorteado de cada tábua."""

from __future__ import annotations

import math
from typing import Any

from ..construtor import FLAT, LIT, Vec
from .construcao import TABUA, Lugar, Modo, pela_luz, sortear_tabua, tabua
from .peca import Arg, Ctx, Peca

TESTE = "tests/test_kit.py::test_cada_variacao_monta"
X = Arg


def _parede_tabuas(c: Ctx, a: dict[str, Any]) -> None:
    """Tábuas em pé numa face, com o topo em empena (o meio sobe ``empena``); a da esquerda puxa para o claro."""
    x0, x1, z0, alt, emp, larg = a["x0"], a["x1"], a["z0"], a["altura"], a["empena"], a["largura"]
    xc, meia = (x0 + x1) / 2, (x1 - x0) / 2

    def topo(x: float) -> float:
        return float(alt + emp * max(0.0, 1 - abs(x - xc) / meia))

    k, x = 0, x0
    while x + 1.0 < x1:
        w = min(larg, x1 - x) - 0.4
        h = min(topo(x), topo(x + w)) - z0
        if h > 1.0:
            var = sortear_tabua(c.st, 1 - (x - x0) / max(1.0, x1 - x0), a["desgaste"], 30)
            tabua(c, f"{c.pid}_{k:02d}", Lugar((x + 0.2, a["y"], z0), (0, 0, 1), (1, 0, 0), h, w), var,
                  Modo(c.camada, luz=True))
        x += larg
        k += 1


def _poste(c: Ctx, a: dict[str, Any]) -> None:
    """A face da frente, a faixa da direita na sombra e o topo de corte."""
    (x, y, z), h, r = a["base"], a["altura"], a["raio"]
    f = y + r
    mat, tags = pela_luz(TABUA, 0)
    c.poly(c.pid, mat, [(x - r, f, z), (x + r, f, z), (x + r, f, z + h), (x - r, f, z + h)], c.camada, tags)
    s = x + r * 0.3
    mat, tags = pela_luz(TABUA, -1)
    c.poly(f"{c.pid}_sh", mat, [(s, f, z), (x + r, f, z), (x + r, f, z + h), (s, f, z + h)], c.camada + 1, tags)
    if a["topo"]:
        t = z + h
        c.poly(f"{c.pid}_top", "madeira_cortada", [(x - r, y - r, t), (x + r, y - r, t), (x + r, f, t), (x - r, f, t)],
               c.camada + 1, (*FLAT, LIT))


def _viga(c: Ctx, a: dict[str, Any]) -> None:
    """A face da frente e, com ``fundo``, o topo; ``giro`` gira a viga em torno do eixo vertical pelo meio."""
    x0, x1, y, z0, z1, fundo, giro = a["x0"], a["x1"], a["y"], a["z0"], a["z1"], a["fundo"], a["giro"]
    cx, ca, sa = (x0 + x1) / 2, math.cos(giro), math.sin(giro)

    def g(pts: list[Vec]) -> list[Vec]:
        if giro == 0:
            return pts
        return [(cx + (x - cx) * ca - (yy - y) * sa, y + (x - cx) * sa + (yy - y) * ca, z) for x, yy, z in pts]

    mat, tags = pela_luz(TABUA, 0)
    c.poly(c.pid, mat, g([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]), c.camada, tags)
    if fundo > 0:
        c.poly(f"{c.pid}_top", mat, g([(x0, y - fundo, z1), (x1, y - fundo, z1), (x1, y, z1), (x0, y, z1)]), c.camada,
               tags)


def _tabuado(c: Ctx, a: dict[str, Any]) -> None:
    """Tábuas lado a lado ao longo de x com a fresta escura atrás: deitadas (um piso) ou de pé na face da frente."""
    (x0, y0, z0), comp, ext, larg = a["canto"], a["comprimento"], a["extensao"], a["largura"]
    if a["deitado"]:
        c.poly(f"{c.pid}_gap", TABUA["deep"], [(x0, y0, z0), (x0 + comp, y0, z0), (x0 + comp, y0 + ext, z0),
                                                (x0, y0 + ext, z0)], c.camada)
        k, y = 0, y0
        while y + 1.0 < y0 + ext:
            w = min(larg, y0 + ext - y) - 0.5
            tabua(c, f"{c.pid}_{k:02d}", Lugar((x0, y + 0.25, z0 + 0.05), (1, 0, 0), (0, 1, 0), comp, w),
                  sortear_tabua(c.st, a["luz"], a["desgaste"], 30), Modo(c.camada + 1, aresta=False))
            y += larg
            k += 1
        return
    c.poly(f"{c.pid}_gap", TABUA["deep"], [(x0, y0, z0), (x0 + comp, y0, z0), (x0 + comp, y0, z0 + ext),
                                            (x0, y0, z0 + ext)], c.camada)
    for i in range(max(1, round(ext / larg))):
        tabua(c, f"{c.pid}_{i:02d}", Lugar((x0, y0 + 0.05, z0 + i * larg + 0.4), (1, 0, 0), (0, 0, 1), comp,
                                          larg - 0.8),
              sortear_tabua(c.st, a["luz"], a["desgaste"], a["pregos"]), Modo(c.camada + 1, aresta=False))


def _corda(c: Ctx, a: dict[str, Any]) -> None:
    """A corda de ``de`` a ``ate`` pendendo ``barriga`` px no meio (parábola em 4 trechos)."""
    p, r, barriga = a["de"], a["ate"], a["barriga"]
    pts = [(p[0] + (r[0] - p[0]) * t, p[1] + (r[1] - p[1]) * t, p[2] + (r[2] - p[2]) * t - barriga * 4 * t * (1 - t))
           for t in (i / 4 for i in range(5))]
    c.line(c.pid, a["material"], pts, c.camada)


def _aro(c: Ctx, a: dict[str, Any]) -> None:
    c.line(c.pid, "metal", list(a["pontos"]), c.camada)


PECAS_MADEIRA = [
    Peca("parede_tabuas", "Parede de tábuas em pé com o topo em empena, cada tábua com a variação dela", (
        X("x0", "comprimento", "borda esquerda"), X("x1", "comprimento", "borda direita"),
        X("y", "comprimento", "o plano da face (frente = +y)"), X("z0", "comprimento", "base", "0"),
        X("altura", "comprimento", "altura nas bordas"), X("empena", "comprimento", "quanto o meio sobe", "0"),
        X("largura", "comprimento", "largura de cada tábua", "16cm"),
        X("desgaste", "inteiro", "a chance (%) de canto gasto", "20")),
        _parede_tabuas, (("parede", {"x0": "-1m", "x1": "1m", "y": "0", "altura": "1.6m"}),
                         ("empena", {"x0": "-1m", "x1": "1m", "y": "0", "z0": "35cm", "altura": "1.9m",
                                     "empena": "90cm"}),
                         ("tábua larga", {"x0": "-60cm", "x1": "60cm", "y": "0", "altura": "1.2m", "largura": "25cm",
                                          "desgaste": "60"})),
        TESTE, (_parede_tabuas, tabua)),
    Peca("poste", "Poste quadrado: a face da frente, a faixa da sombra e o topo de corte", (
        X("base", "ponto", "o pé do poste"), X("altura", "comprimento", "altura"),
        X("raio", "comprimento", "meia largura"), X("topo", "bool", "o topo de corte", True)),
        _poste, (("fino", {"base": ["0", "0", "0"], "altura": "1m", "raio": "5cm"}),
                 ("grosso", {"base": ["0", "0", "0"], "altura": "1.2m", "raio": "10cm"}),
                 ("sem topo", {"base": ["0", "0", "0"], "altura": "2m", "raio": "6cm", "topo": False})),
        TESTE, (_poste,)),
    Peca("viga", "Viga ou tábua ao longo de x (girada com giro): a face da frente e, com fundo, o topo", (
        X("x0", "comprimento", "ponta esquerda"), X("x1", "comprimento", "ponta direita"),
        X("y", "comprimento", "o plano da frente"), X("z0", "comprimento", "base"), X("z1", "comprimento", "topo"),
        X("fundo", "comprimento", "a profundidade do topo", "0"),
        X("giro", "escalar", "o giro em torno do eixo vertical, pelo meio (30deg: a ponta direita vem para a frente)",
          "0")),
        _viga, (("fina", {"x0": "-1m", "x1": "1m", "y": "0", "z0": "50cm", "z1": "56cm"}),
                ("com topo", {"x0": "-1m", "x1": "1m", "y": "0", "z0": "50cm", "z1": "60cm", "fundo": "8cm"}),
                ("girada", {"x0": "-60cm", "x1": "60cm", "y": "0", "z0": "1m", "z1": "1.2m", "fundo": "3cm",
                            "giro": "35deg"})),
        TESTE, (_viga,)),
    Peca("tabuado", "Tábuas lado a lado ao longo de x, com fresta, veio, nó e pregos: um piso (deitado) ou uma face", (
        X("canto", "ponto", "o canto esquerdo, de trás (piso) ou de baixo (face)"),
        X("comprimento", "comprimento", "o comprimento das tábuas (em x)"),
        X("extensao", "comprimento", "quanto as tábuas cobrem: em y (piso) ou em z (face)"),
        X("largura", "comprimento", "a largura de cada tábua"), X("deitado", "bool", "um piso (true) ou a face", True),
        X("luz", "escalar", "puxa as tábuas para o tom claro (0 a 1)", "0.5"),
        X("desgaste", "inteiro", "a chance (%) do canto gasto", "25"),
        X("pregos", "inteiro", "a chance (%) de pregos (só na face)", "30")),
        _tabuado, (("piso", {"canto": ["-60cm", "-40cm", "40cm"], "comprimento": "1.2m", "extensao": "80cm",
                             "largura": "9cm"}),
                   ("frente de caixa", {"canto": ["-21cm", "21cm", "0"], "comprimento": "42cm", "extensao": "42cm",
                                        "largura": "14cm", "deitado": False, "pregos": "50"}),
                   ("gasto e claro", {"canto": ["-60cm", "-40cm", "0"], "comprimento": "1.2m", "extensao": "80cm",
                                      "largura": "12cm", "luz": "0.9", "desgaste": "70"})),
        TESTE, (_tabuado, tabua, sortear_tabua)),
    Peca("corda", "Corda pendendo entre dois pontos (parábola)", (
        X("de", "ponto", "uma ponta"), X("ate", "ponto", "a outra"), X("barriga", "comprimento", "quanto pende", "0"),
        X("material", "material", "o material", "linho")),
        _corda, (("esticada", {"de": ["-50cm", "0", "50cm"], "ate": ["50cm", "0", "50cm"]}),
                 ("frouxa", {"de": ["-50cm", "0", "50cm"], "ate": ["50cm", "0", "50cm"], "barriga": "15cm"}),
                 ("vertical", {"de": ["0", "0", "1m"], "ate": ["0", "0", "20cm"], "material": "fibra"})),
        TESTE, (_corda,)),
    Peca("aro", "Aro ou ferragem: traço de metal de 1 px pelos pontos (a alça do balde, a cinta)", (
        X("pontos", "pontos", "o caminho do traço"),),
        _aro, (("reto", {"pontos": [["-30cm", "0", "30cm"], ["30cm", "0", "30cm"]]}),
               ("curvo", {"pontos": [["-30cm", "0", "30cm"], ["0", "0", "27cm"], ["30cm", "0", "30cm"]]}),
               ("alça", {"pontos": [["-15cm", "0", "0"], ["0", "0", "15cm"], ["15cm", "0", "0"]]})),
        TESTE, (_aro,)),
]
