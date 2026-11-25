"""A flora de lâminas e de pontos: a touceira (lâminas que saem de um pé e abrem em arco: o capim, o junco, a
samambaia, a folha em espada e, no alto de um tronco, a palma) e o salpico (pontos de cor nas âncoras de outro nó:
a flor, o fruto, a espiga). São a planta que não é uma massa de folhas: a silhueta é de lâminas, e cada lâmina tem
o comprimento, a abertura e o tom sorteados pela semente do nó. As duas desenham qualquer vista."""

from __future__ import annotations

import math
from typing import Any

from ..construtor import LINE, Parte, ellipse, polyline, q, qv
from .peca import Arg, Ctx, Peca

QUATRO = ("S", "E", "N", "W")
TRECHOS = 5  # os trechos do arco da lâmina
SOBE_ANTES = 0.3  # o ponto de controle do arco: a 30 % do alcance a lâmina já está no alto
ABRE_MENOS = 0.35  # a lâmina mais fechada abre 35 % do pedido (poucas: a maioria abre perto do pedido)
TOM = 0.4  # a lâmina sai clara ou escura quando o sorteio dela (de −1 a 1) passa disto
# a largura da folha em cada ponto do arco (fração da largura): estreita no pé, larga antes do meio, ponta fina
LARGURA_NO_ARCO = (0.3, 0.6, 1.0, 0.9, 0.55, 0.15)
RAIO_MINIMO = 32  # o menor raio da folha na IR (q8): 1/8 px
# de onde se vê a vista S (o chão a 0,6 e a altura a cos 45°): o ponto do lado de lá não ganha salpico
CAMERA = (0.0, 0.6, math.sqrt(0.5))
DE_FRENTE = 0.5  # na vista única, o salpico sorteia entre a metade dos pontos mais virada para a câmera
Vec = tuple[float, float, float]
X = Arg


def _arco(pe: Vec, az: float, comprimento: float, forma: tuple[float, float]) -> list[Vec]:
    """Os pontos da lâmina: sai do pé quase a prumo e abre no azimute ``az`` até ``abre`` do comprimento; a ponta
    cai ``cai`` da altura do arco (acima de 1, desce abaixo do pé, sem entrar no chão)."""
    abre, cai = forma
    alcance = comprimento * abre
    alto = comprimento * math.sqrt(max(0.04, 1 - abre * abre))
    dx, dy = math.sin(az), math.cos(az)
    ctrl = (pe[0] + dx * alcance * SOBE_ANTES, pe[1] + dy * alcance * SOBE_ANTES, pe[2] + alto * (1 + 0.5 * cai))
    fim = (pe[0] + dx * alcance, pe[1] + dy * alcance, max(0.0, pe[2] + alto * (1 - cai)))
    out = []
    for i in range(TRECHOS + 1):
        s = i / TRECHOS
        out.append((ctrl[0] * 2 * s * (1 - s) + pe[0] * (1 - s) ** 2 + fim[0] * s * s,
                    ctrl[1] * 2 * s * (1 - s) + pe[1] * (1 - s) ** 2 + fim[1] * s * s,
                    ctrl[2] * 2 * s * (1 - s) + pe[2] * (1 - s) ** 2 + fim[2] * s * s))
    return out


def _lamina(c: Ctx, pid: str, material: str, arco: list[Vec], largura: float) -> None:
    """A lâmina fina (um traço de 1 px, sem contorno) ou, com largura, a folha: roliça ao longo do arco, estreita
    no pé, larga antes do meio e de ponta fina, no grupo de contorno do nó (sem linha entre as folhas)."""
    if largura <= 0:
        c.b.part(pid, material, polyline([qv(*p) for p in arco], 1), Parte(group=c.grupo, tags=LINE))
        return
    geo = {"type": "tapered_polyline", "points_q8": [qv(*p) for p in arco],
           "radii_q8": [max(RAIO_MINIMO, q(largura / 2 * k)) for k in LARGURA_NO_ARCO]}
    c.b.part(pid, material, geo, Parte(group=c.grupo, tags=("no_inner_outline",)))


def _touceira(c: Ctx, a: dict[str, Any]) -> None:
    """``n`` lâminas em volta do pé, uma a cada fatia da volta: cada uma com o pé sorteado dentro do ``raio``, o
    comprimento na faixa, a abertura de 35 % a 100 % do pedido (a maioria perto dele) e o tom (o comum, o claro
    ou o escuro) sorteados. Deixa a âncora ``pontas`` (a ponta de cada lâmina)."""
    st, n = c.st, a["n"]
    giro = st.randint(0, 999) / 1000
    pontas: list[Vec] = []
    for i in range(n):
        az = 2 * math.pi * (i + giro + st.randint(-30, 30) / 100) / n
        longe = a["raio"] * st.randint(0, 100) / 100
        pe = (a["pe"][0] + math.sin(az) * longe, a["pe"][1] + math.cos(az) * longe, a["pe"][2])
        comprimento = a["altura"][0] + (a["altura"][1] - a["altura"][0]) * st.randint(0, 100) / 100
        abre = min(0.98, a["abre"] * (1 - (1 - ABRE_MENOS) * (st.randint(0, 100) / 100) ** 2))
        arco = _arco(pe, az, comprimento, (abre, a["cai"]))
        tom = st.randint(-100, 100) / 100
        material = a["claro"] if tom > TOM else a["escuro"] if tom < -TOM else a["material"]
        _lamina(c, f"{c.pid}_{i:02d}", material, arco, a["largura"])
        pontas.append(arco[-1])
    c.deixa("pontas", pontas)


def _salpico(c: Ctx, a: dict[str, Any]) -> None:
    """Um ponto de cor em ``n`` dos pontos da âncora ``em``, sorteados; na composição de vista única, só entre os
    mais virados para a câmera (o ponto do lado de lá ficaria escondido, e o da beira, fora da figura)."""
    pts = c.ancora(a["em"])
    meio = [sum(p[k] for p in pts) / max(1, len(pts)) for k in range(3)]
    if len(c.vistas) == 1:
        pts.sort(key=lambda p: -sum((p[k] - meio[k]) * CAMERA[k] for k in range(3)))
        pts = pts[:max(a["n"], round(DE_FRENTE * len(pts)))]
    for i in range(min(a["n"], len(pts))):
        x, y, z = pts.pop(c.st.randint(0, len(pts) - 1))
        c.b.part(f"{c.pid}_{i:02d}", a["material"], ellipse(qv(x, y, z), qv(a["raio"], a["raio"], a["raio"])),
                 Parte(group=c.grupo, tags=LINE))


MOITA = ("moita", "copa", {"copa": ["60cm", "40cm", "40cm"], "tufos": "6", "tamanho": "0.45"})
PECAS_ERVAS = [
    Peca("touceira", "Lâminas que saem de um pé e abrem em arco, cada uma com o comprimento, a abertura e o tom "
         "sorteados: finas, o capim e o junco; largas, a samambaia e a folha em espada; com o pé no alto de um "
         "tronco, a palma. Deixa as pontas", (
             X("altura", "faixa", "o comprimento das lâminas, sorteado na faixa"),
             X("n", "inteiro", "lâminas", "9"),
             X("abre", "escalar", "quanto a lâmina mais aberta se afasta do pé, em fração do comprimento (0.2 = em "
               "pé; 0.9 = deitada)", "0.5"),
             X("cai", "escalar", "quanto a ponta cai da altura do arco (0 = reta; 1 = volta à altura do pé)", "0.3"),
             X("largura", "comprimento", "a largura da folha (0 = lâmina fina, de 1 px)", "0"),
             X("raio", "comprimento", "o raio do pé: as lâminas nascem espalhadas nele", "0"),
             X("pe", "ponto", "de onde nasce (o chão, ou o alto de um tronco)", ["0", "0", "0"]),
             X("material", "material", "a lâmina comum", "capim"),
             X("claro", "material", "a lâmina clara (uma em cada três ou quatro)", "capim_claro"),
             X("escuro", "material", "a lâmina escura", "capim_escuro")),
         _touceira, (("capim", {"altura": ["18cm", "40cm"], "n": "14", "abre": "0.45", "raio": "12cm"}),
                     ("junco", {"altura": ["70cm", "1.2m"], "n": "9", "abre": "0.22", "cai": "0.05",
                                "raio": "15cm"}),
                     ("samambaia", {"altura": ["50cm", "75cm"], "n": "8", "abre": "0.75", "cai": "0.45",
                                    "largura": "12cm", "material": "folha", "claro": "folha_clara",
                                    "escuro": "folha_escura"}),
                     ("espada", {"altura": ["50cm", "80cm"], "n": "11", "abre": "0.6", "cai": "0",
                                 "largura": "10cm", "material": "agulha", "claro": "agulha_clara",
                                 "escuro": "agulha_escura"})),
         "tests/test_ervas.py::test_a_touceira_e_de_laminas", (_touceira, _lamina, _arco), vistas=QUATRO,
         flora="lamina", ancoras=("pontas",)),
    Peca("salpico", "Pontos de cor sobre outro nó: a flor e o fruto na superfície de uma copa, a espiga na ponta "
         "de uma lâmina, o broto na ponta de um galho. Pede a âncora de um nó de antes", (
             X("em", "ancora", "onde caem os pontos ('<nó>.superficie', '<nó>.pontas')"),
             X("material", "material", "a cor do ponto"), X("n", "inteiro", "quantos pontos", "8"),
             X("raio", "comprimento", "o raio do ponto (3 cm = 1 px)", "3cm")),
         _salpico, (("flores", {"em": "moita.superficie", "material": "olho_claro", "n": "9"}),
                    ("frutos", {"em": "moita.superficie", "material": "pano_vermelho", "n": "6", "raio": "5cm"}),
                    ("botões", {"em": "moita.superficie", "material": "ambar", "n": "14"})),
         "tests/test_ervas.py::test_o_salpico_cai_do_lado_da_camera", (_salpico,), vistas=QUATRO, apoio=(MOITA,)),
]
