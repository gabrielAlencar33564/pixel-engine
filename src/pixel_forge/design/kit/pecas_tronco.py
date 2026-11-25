"""O tronco e os galhos, em volumes: o tronco em pé como sólido de revolução (o volume e a textura do material fazem
a sombra, a base e as marcas) e os galhos roliços em volta dele, que sobem até dentro da copa e deixam a âncora das
pontas para a copa pôr um tufo em cada uma. As duas peças desenham qualquer vista."""

from __future__ import annotations

import math
from typing import Any

from ..construtor import Parte, q, qv
from .peca import Arg, Ctx, Peca

TESTE = "tests/test_kit.py::test_cada_variacao_monta"
QUATRO = ("S", "E", "N", "W")
X = Arg
COPA = X("copa", "ponto", "a copa: meia largura, meia altura e a altura do centro")
COPA_V = ["1.1m", "1.3m", "2.6m"]
TRECHOS = 6  # os trechos do galho roliço
ABRE_NO_ALTO = (0.25, 0.75)  # o ponto de controle: a 25 % da abertura já subiu 75 % (sobe a prumo e depois abre)
SAIDA_DO_FINO = 0.6  # o galho fino sai a 60 % do grosso
DESVIO_NA_FATIA = 15  # quanto o galho sai do meio da fatia dele (% da fatia, para cada lado)
RAIO_MINIMO = 32  # o menor raio do galho roliço na IR (q8): 1/8 px
Vec = tuple[float, float, float]


def _tronco(c: Ctx, a: dict[str, Any]) -> None:
    """O sólido de revolução que afina e inclina pelas estações: a base em arco, o topo em tampa oval."""
    h, b0, b1, lean = a["altura"], a["base"], a["topo"], a["inclinacao"]
    st = [[q(h * i / 20), q((b0 + (b1 - b0) * i / 20) / 2), q(lean * (i / 20) ** 2)] for i in range(21)]
    c.b.part(c.pid, a["casca"], {"type": "revolution", "origin_q8": qv(0, 0, 0), "stations": st},
             Parte(bone=c.osso(0.0)[0], group=c.grupo))


def _no_caminho(p0: Vec, ctrl: Vec, p1: Vec, s: float) -> Vec:
    """O ponto da Bézier quadrática em ``s``."""
    x, y, z = ((1 - s) ** 2 * a + 2 * (1 - s) * s * b + s * s * d for a, b, d in zip(p0, ctrl, p1, strict=True))
    return x, y, z


def _rolico(c: Ctx, pid: str, pts: list[Vec], diametros: tuple[float, float], material: str) -> None:
    """O galho roliço pelos pontos, afinando do primeiro ao último diâmetro. Fica no osso da altura de onde sai:
    abaixo da cadeia do balanço, no tronco (o galho não se solta dele quando a copa balança)."""
    z0 = pts[0][2]
    bone, zl = ("trunk", z0) if c.cadeia and z0 < c.cadeia[0][1] else c.osso(z0)
    n = len(pts) - 1
    raios = [max(RAIO_MINIMO, q((diametros[0] + (diametros[1] - diametros[0]) * i / n) / 2)) for i in range(n + 1)]
    geo = {"type": "tapered_polyline", "points_q8": [qv(x, y, z - z0 + zl) for x, y, z in pts], "radii_q8": raios}
    c.b.part(pid, material, geo, Parte(bone=bone, group=c.grupo, tags=("no_inner_outline",)))


def _galhos(c: Ctx, a: dict[str, Any]) -> None:
    """``n`` galhos em volta do tronco, um a cada fatia da volta a partir da frente (``fase``, em fatias: com 0,5 a
    frente fica livre, e nenhum galho aponta para a câmera): cada um sobe quase a prumo e só então abre até a ponta,
    dentro da copa. Com ``bifurca``, um galho fino sai a 60 % dele. Deixa a âncora ``pontas`` (x, y, z)."""
    meia_l, meia_a, cz = a["copa"]
    st, n = c.st, a["n"]
    pontas: list[Vec] = []
    for j in range(n):
        az = 2 * math.pi * (j + a["fase"] + st.randint(-DESVIO_NA_FATIA, DESVIO_NA_FATIA) / 100) / n
        alcance = meia_l * a["alcance"] * st.randint(80, 100) / 100
        v = a["ponta_v"][0] + (a["ponta_v"][1] - a["ponta_v"][0]) * st.randint(0, 100) / 100
        p0 = (0.0, 0.0, a["base"])
        p1 = (math.sin(az) * alcance, math.cos(az) * alcance * a["fundo"], cz + v * meia_a)
        ctrl = (p1[0] * ABRE_NO_ALTO[0], p1[1] * ABRE_NO_ALTO[0], p0[2] + (p1[2] - p0[2]) * ABRE_NO_ALTO[1])
        grosso = a["largura"][0] + (a["largura"][1] - a["largura"][0]) * st.randint(0, 100) / 100
        _rolico(c, f"{c.pid}_{j}", [_no_caminho(p0, ctrl, p1, i / TRECHOS) for i in range(TRECHOS + 1)],
                (grosso, a["ponta"]), a["material"])
        pontas.append(p1)
        if st.randint(0, 999) < a["bifurca"] * 1000:
            sai = _no_caminho(p0, ctrl, p1, SAIDA_DO_FINO)
            giro = math.radians(st.randint(30, 50) * (1 if j % 2 else -1))
            dx, dy = p1[0] - sai[0], p1[1] - sai[1]
            fim = (sai[0] + dx * math.cos(giro) - dy * math.sin(giro),
                   sai[1] + dx * math.sin(giro) + dy * math.cos(giro), p1[2] + 0.5 * math.hypot(dx, dy))
            _rolico(c, f"{c.pid}_{j}_fino", [sai, fim], (max(a["ponta"], grosso * 0.45), a["ponta"]), a["material"])
            pontas.append(fim)
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
        TESTE, (_tronco,), vistas=QUATRO),
    Peca("galhos", "Os galhos em volta do tronco, roliços: sobem do tronco e abrem até a ponta, dentro da copa (a "
         "copa em volumes cobre quase todos; sem copa, é a árvore seca). Deixa as pontas", (
        X("base", "comprimento", "a altura de onde saem (o alto do tronco)"), COPA,
        X("fundo", "escalar", "a meia profundidade da copa, em fração da meia largura", "1"),
        X("n", "inteiro", "galhos"), X("alcance", "escalar", "onde a ponta cai, em fração da meia largura", "0.6"),
        X("fase", "escalar", "onde cai o primeiro galho, em fatias da volta a partir da frente (0 = um galho para a "
          "câmera; 0.5 = a frente livre)", "0.5"),
        X("ponta_v", "faixa", "a altura das pontas na copa (de -1 a 1), sorteada na faixa", ["-0.4", "0.2"]),
        X("largura", "faixa", "o diâmetro na saída"), X("ponta", "comprimento", "o diâmetro na ponta"),
        X("bifurca", "escalar", "a chance de um galho fino a 60 % do grosso", "0.5"),
        X("material", "material", "a casca", "casca")),
        _galhos, (("em volta", {"base": "1m", "copa": COPA_V, "n": "5", "largura": ["12cm", "16cm"], "ponta": "4cm"}),
                  ("abertos", {"base": "80cm", "copa": COPA_V, "n": "7", "alcance": "0.95", "ponta_v": ["-0.7", "-0.2"],
                               "largura": ["12cm", "17cm"], "ponta": "5cm", "bifurca": "0"}),
                  ("secos", {"base": "1.2m", "copa": COPA_V, "n": "4", "alcance": "0.8", "ponta_v": ["0", "0.8"],
                             "largura": ["10cm", "14cm"], "ponta": "3cm", "bifurca": "1",
                             "material": "casca_clara"})),
        "tests/test_flora.py::test_os_galhos_abrem_em_volta_do_tronco", (_galhos, _rolico, _no_caminho),
        vistas=QUATRO, ancoras=("pontas",)),
]
