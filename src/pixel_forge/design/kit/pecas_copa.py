"""A copa em volumes, para a câmera de cima, em três construções: a massa da folhosa (lóbulos de tamanhos
desencontrados em espiral, por dentro do elipsoide da copa, com raminhos na borda), a copa aberta (uma nuvem de
folhas em cada ponta de galho, com os galhos à mostra) e a conífera em andares (saias pregueadas, de pontas
caídas). A folhagem de um nó é uma massa de luz só, com cada volume em relevo nela: a luz, a oclusão e a sombra no
chão saem da forma no render, e a peça desenha qualquer vista. A copa é ``[meia largura, meia altura, altura do
centro]``. Tudo é sorteado pela semente do nó: outra semente dá outra planta da mesma espécie."""

from __future__ import annotations

import math
from typing import Any

from ...core.rng import Stream
from ..construtor import Parte, bound_polygon, ellipse, q, qv
from .peca import Arg, Ctx, Peca

TESTE = "tests/test_flora.py::test_a_copa_e_uma_massa_so"
QUATRO = ("S", "E", "N", "W")
AUREO = math.pi * (3 - math.sqrt(5))  # o passo da espiral dos lóbulos: nenhum cai em anel com outro
BAIXO = -0.8  # o seno da elevação do lóbulo mais baixo: os lóbulos enchem o elipsoide até perto do fundo
SO_O_ALTO = 0.9  # com o perfil em −1, o mais baixo sobe tanto: a copa fica com a metade de cima (o guarda-sol)
AFINA = 0.6  # com o perfil em 1, a copa afina tanto no alto (a gota)
RAMINHO = 0.14  # o raminho na borda do lóbulo, em fração da copa
VARIA = 2.5  # o tamanho do lóbulo varia ``irregular`` vezes isto
RECUA = 1.2  # e o lóbulo recua da borda da copa até ``irregular`` vezes isto
RAMOS_QUE_CAEM = 3  # por lóbulo
ACIMA_DO_CHAO = 0.18  # a ponta do ramo para a esta fração da altura de onde ele sai (de 0,4 a 1,4 vezes isto)
RAMO_FINO = 0.045  # o raio do ramo que cai, em fração da meia largura da copa (1 px no mínimo)
PONTA_DO_RAMO = 0.45  # o raio na ponta, em fração do raio no alto
RAIO_MINIMO = 32  # o menor raio do ramo na IR (q8): 1/8 px
MIOLO = 0.6  # o miolo escuro, em fração da copa: fecha os vãos entre os lóbulos
TUFO_DO_GALHO = 0.8  # o tufo na ponta de um galho, em fração do lóbulo
PARA_CIMA = 0.3  # o ponto da âncora ``superficie`` sobe tanto da direção de fora (a face de cima do volume)
SOBE = 1.6  # cada saia da conífera sobe 1,6 passo: entra na de cima
MAX_PONTAS = 15  # as pontas de uma saia (o leque tem até 32 vértices)
Vec = tuple[float, float, float]
Tufo = tuple[Vec, float]  # o centro e o raio, em frações da copa (a copa é a esfera de raio 1)
X = Arg


def _sorte(st: Stream) -> float:
    """De −1 a 1."""
    return st.randint(-100, 100) / 100


def _lobulos(st: Stream, a: dict[str, Any], folga: float) -> list[Tufo]:
    """Os lóbulos, do alto para baixo, numa espiral em volta do eixo (o giro dela é da semente): o primeiro no
    topo; os outros com o tamanho, o lugar e o recuo sorteados, por dentro da copa menos a ``folga`` do raminho.
    O ``perfil`` afina o alto (a gota) ou tira a metade de baixo (o guarda-sol)."""
    n, irr, perfil = a["tufos"], a["irregular"], a["perfil"]
    baixo = BAIXO + SO_O_ALTO * max(0.0, -perfil)
    giro = st.randint(0, 999) / 1000
    out: list[Tufo] = [((0.0, 0.0, 1 - folga - a["tamanho"]), a["tamanho"])]
    for i in range(1, n):
        t = min(1.0, max(0.1, (i + 0.5 * irr * _sorte(st)) / (n - 1)))
        az = 2 * math.pi * giro + i * AUREO + irr * _sorte(st)
        s = 1 - t * (1 - baixo)
        w = 1 - AFINA * max(0.0, perfil) * (1 - t)
        f = min(0.7, max(0.18, a["tamanho"] * (1 + VARIA * irr * _sorte(st)))) * math.sqrt(w)
        k = max(0.0, 1 - folga - f) * (1 - RECUA * irr * abs(_sorte(st)))
        ce = math.sqrt(1 - s * s)
        out.append(((ce * math.sin(az) * k * w, ce * math.cos(az) * k * w, s * k), f))
    return out


def _raminhos(st: Stream, lobulos: list[Tufo], por_lobulo: int) -> list[Tufo]:
    """Os raminhos: bolas pequenas na superfície de cada lóbulo, do lado de fora, que quebram o arco liso dele. O
    primeiro fica no topo do lóbulo do alto, com o raio inteiro: a altura da copa é a pedida."""
    out: list[Tufo] = []
    for j, ((x, y, z), f) in enumerate(lobulos):
        fora = math.hypot(x, y, z) or 1.0
        for i in range(por_lobulo):
            if i == 0 and j == 0:
                out.append(((x, y, z + f), RAMINHO))
                continue
            e = [v / fora + 0.9 * _sorte(st) for v in (x, y, z)]
            tam = math.hypot(*e) or 1.0
            out.append(((x + e[0] / tam * f, y + e[1] / tam * f, z + e[2] / tam * f),
                        RAMINHO * (0.6 + 0.4 * abs(_sorte(st)))))
    return out


def tufos(st: Stream, a: dict[str, Any]) -> list[tuple[Vec, Vec]]:
    """O centro e os raios de cada volume da copa: os lóbulos e os raminhos. Nenhum passa do elipsoide da copa."""
    meia_l, meia_a, cz = a["copa"]
    eixos = (meia_l, meia_l * a["fundo"], meia_a)
    lobulos = _lobulos(st, a, RAMINHO if a["raminhos"] else 0.0)
    return [((x * eixos[0], y * eixos[1], cz + z * eixos[2]), (eixos[0] * f, eixos[1] * f, eixos[2] * f))
            for (x, y, z), f in lobulos + _raminhos(st, lobulos, a["raminhos"])]


def ramos(st: Stream, a: dict[str, Any], lobulos: list[tuple[Vec, Vec]]) -> list[tuple[Vec, Vec, float]]:
    """Os ramos que caem (``pende``): três de cada lóbulo da metade de baixo da copa, cada um de dentro do lóbulo
    até ``pende`` meias alturas abaixo do meio da copa. O quanto desce é sorteado, e a barra da cortina é
    desigual: nenhum ramo chega ao chão. Devolve o alto, a ponta e o raio de cada um."""
    meia_l, meia_a, cz = a["copa"]
    baixos = sorted(lobulos, key=lambda v: v[0][2])[:(len(lobulos) + 1) // 2] if a["pende"] > 0 else []
    out = []
    for (x, y, z), (rx, ry, _) in baixos:
        for _ in range(RAMOS_QUE_CAEM):
            px, py = x + 0.6 * rx * _sorte(st), y + 0.6 * ry * _sorte(st)
            desce = cz - meia_a * a["pende"] * (0.45 + 0.55 * abs(_sorte(st)))
            ponta = max(z * ACIMA_DO_CHAO * (0.4 + abs(_sorte(st))), desce)
            raio = max(1.0, meia_l * RAMO_FINO * (0.7 + 0.6 * abs(_sorte(st))))
            out.append(((px, py, z), (px * 1.03, py * 1.03, ponta), raio))
    return out


def _na_massa(c: Ctx) -> tuple[str, ...]:
    """As marcas do volume de folhagem: um relevo na massa de luz do grupo de contorno do nó (os nós do mesmo
    grupo são uma massa só; ``raster/tons.py``), com a beira recortada em folhas (``raster/montagem.py``)."""
    return ("volume_sphere", f"massa_{c.grupo}", "borda_de_folha")


def _volumes(c: Ctx, material: str, massas: list[tuple[Vec, Vec]], meio: Vec) -> None:
    """Os volumes como partes do nó, no grupo de contorno dele (sem linha entre eles) e numa massa de luz só; deixa
    a âncora ``superficie``: um ponto na face de cada volume, para fora do ``meio`` e para cima (a face que a
    câmera de cima vê), se nenhum outro volume o cobre."""
    fora: list[Vec] = []
    for i, (centro, raios) in enumerate(massas):
        c.b.part(f"{c.pid}_{i:02d}", material, ellipse(qv(*centro), qv(*raios)),
                 Parte(group=c.grupo, tags=_na_massa(c)))
        d = [(v - o) / r for v, o, r in zip(centro, meio, raios, strict=True)]
        tam = math.hypot(*d) or 1.0
        d = [d[0] / tam, d[1] / tam, d[2] / tam + PARA_CIMA]
        tam = math.hypot(*d)
        p = (centro[0] + d[0] / tam * raios[0], centro[1] + d[1] / tam * raios[1], centro[2] + d[2] / tam * raios[2])
        if not any(j != i and math.hypot(*((p[k] - o[k]) / r[k] for k in range(3))) < 1
                   for j, (o, r) in enumerate(massas)):
            fora.append(p)
    c.deixa("superficie", fora)


def _copa(c: Ctx, a: dict[str, Any]) -> None:
    """O miolo escuro, os volumes da copa, um tufo na ponta de cada galho de ``pontas`` e os ramos que caem; a
    copa inteira sai do eixo pelo ``desvio`` (os tufos das pontas ficam nas pontas)."""
    meia_l, meia_a, cz = a["copa"]
    eixos = (meia_l, meia_l * a["fundo"], meia_a)
    dx, dy = a["desvio"]

    def fora_do_eixo(p: Vec) -> Vec:
        return (p[0] + dx, p[1] + dy, p[2])

    c.b.part(f"{c.pid}_miolo", a["miolo"], ellipse(qv(dx, dy, cz), qv(*(e * MIOLO for e in eixos))),
             Parte(group=c.grupo))
    f = a["tamanho"] * TUFO_DO_GALHO
    nas_pontas = [((x, y, z), (eixos[0] * f, eixos[1] * f, eixos[2] * f)) for x, y, z in c.ancora(a["pontas"])]
    volumes = tufos(c.st, a)
    _volumes(c, a["material"], [(fora_do_eixo(o), r) for o, r in volumes] + nas_pontas, (dx, dy, cz))
    for i, (alto, ponta, raio) in enumerate(ramos(c.st, a, volumes[:a["tufos"]])):
        geo = {"type": "tapered_polyline", "points_q8": [qv(*fora_do_eixo(alto)), qv(*fora_do_eixo(ponta))],
               "radii_q8": [max(RAIO_MINIMO, q(raio)), max(RAIO_MINIMO, q(raio * PONTA_DO_RAMO))]}
        c.b.part(f"{c.pid}_ramo_{i:02d}", a["material"], geo,
                 Parte(group=c.grupo, tags=("volume_sphere", f"massa_{c.grupo}", "no_outline")))


def _aberta(c: Ctx, a: dict[str, Any]) -> None:
    """Uma nuvem de folhas em cada ponta de ``pontas``: uma copa pequena e chata, de tamanho sorteado, assentada
    sobre a ponta. As nuvens não se fecham numa massa: os galhos e o chão aparecem entre elas."""
    massas: list[tuple[Vec, Vec]] = []
    pontas = c.ancora(a["pontas"])
    for x, y, z in pontas:
        raio = a["raio"] * (1 + 2 * a["irregular"] * _sorte(c.st))
        nuvem = {"copa": (raio, raio * a["achata"], z + raio * a["achata"] * a["assenta"]), "fundo": 1.0,
                 "tufos": a["tufos"], "tamanho": a["tamanho"], "irregular": a["irregular"], "perfil": 0.0,
                 "raminhos": a["raminhos"]}
        massas += [((cx + x, cy + y, cz), raios) for (cx, cy, cz), raios in tufos(c.st, nuvem)]
    alto = sum(p[2] for p in pontas) / max(1, len(pontas))
    _volumes(c, a["material"], massas, (0.0, 0.0, alto))


def _saia(c: Ctx, a: dict[str, Any], andar: tuple[float, float, float, int]) -> list[Vec]:
    """Os pontos de uma saia pregueada: o bico no eixo e, em volta, as pontas (que caem abaixo da barra) e as
    reentrâncias entre elas (mais para dentro e mais altas); a volta fecha na primeira ponta."""
    z0, r0, alto, pontas = andar
    irr = a["irregular"]
    desvio = 0.5 * irr * r0 * _sorte(c.st)  # a saia nunca é um torneado perfeito
    giro = c.st.randint(0, 999) / 1000
    volta: list[Vec] = []
    for j in range(pontas):
        az = 2 * math.pi * (j + giro + 0.6 * irr * _sorte(c.st)) / pontas
        r = r0 * (1 + 1.5 * irr * _sorte(c.st))
        cai = a["cai"] * alto * (0.5 + 0.5 * abs(_sorte(c.st)))
        volta.append((desvio + math.sin(az) * r, math.cos(az) * r, max(0.0, z0 - cai)))
        az += math.pi / pontas
        r = r0 * (1 - a["recorte"]) * (1 + irr * _sorte(c.st))
        volta.append((desvio + math.sin(az) * r, math.cos(az) * r, z0 + 0.12 * alto))
    return [(0.0, 0.0, z0 + alto), *volta, volta[0]]


def _conica(c: Ctx, a: dict[str, Any]) -> None:
    """Os andares de baixo para cima: cada saia abre no raio do andar (que cai com a altura) e fecha no eixo, por
    dentro da de cima; a última fecha na ponta. Cada andar tem o seu grupo de contorno: a linha e a sombra sob a
    saia separam os andares, e as pontas recortam a silhueta. A luz é a da árvore inteira, com cada saia em relevo."""
    base, n = a["base"], a["andares"]
    passo = (a["altura"] - base) / (n - 1 + SOBE)
    for i in range(n):
        z0 = base + i * passo
        r0 = a["raio"] * (1 - i / n) * (1 + a["irregular"] * _sorte(c.st))
        alto = a["altura"] - z0 if i == n - 1 else passo * SOBE
        pontas = max(5, min(MAX_PONTAS, round(a["pontas"] * (0.45 + 0.55 * (1 - i / n)))))
        c.b.part(f"{c.pid}_{i:02d}", a["material"], bound_polygon(_saia(c, a, (z0, r0, alto, pontas))),
                 Parte(group=f"{c.grupo}_{i:02d}", tags=_na_massa(c)))


COPA = X("copa", "ponto", "a copa: meia largura, meia altura e a altura do centro")
FOLHAGEM = X("material", "material", "a folhagem (copa_folhosa, copa_folha, copa_agulha)", "copa_folhosa")
PECAS_COPA = [
    Peca("copa", "A copa da folhosa em massa: lóbulos de tamanhos desencontrados em espiral, por dentro do elipsoide "
         "da copa, com raminhos na borda; a luz é da massa inteira. O perfil faz a redonda, a gota e o guarda-sol; "
         "no chão, sem tronco, é a moita. Deixa a superfície (o ponto de fora de cada volume)", (
             COPA, X("fundo", "escalar", "a meia profundidade, em fração da meia largura (1 = redonda vista de cima)",
                     "1"),
             X("tufos", "inteiro", "os lóbulos (poucos e grandes: a copa pesada; muitos e pequenos: a leve)", "10"),
             X("tamanho", "escalar", "o raio do lóbulo, em fração da copa", "0.32"),
             X("irregular", "escalar", "quanto o tamanho, o lugar e o recuo de cada lóbulo variam (0 = regular)",
               "0.2"),
             X("perfil", "escalar", "de -1 (só a metade de cima, chata por baixo: o guarda-sol) a 1 (larga embaixo "
               "e fina no alto: a gota); 0 = redonda", "0"),
             X("raminhos", "inteiro", "as bolas pequenas na borda de cada lóbulo (0 = lóbulos lisos)", "2"),
             X("pende", "escalar", "os ramos finos que caem dos lóbulos de baixo: até onde descem abaixo do meio da "
               "copa, em meias alturas dela (0 = nenhum; 1 = até o fundo da copa; 2 = a cortina do chorão)", "0"),
             X("desvio", "faixa", "quanto a copa sai do eixo: para a direita da tela e para a frente (a copa de "
               "um lado só; a moita de duas massas, com dois nós no mesmo grupo)", ["0", "0"]),
             X("pontas", "ancora", "as pontas dos galhos onde sai um tufo a mais ('<nó>.pontas')", ""),
             FOLHAGEM, X("miolo", "material", "o miolo escuro entre os lóbulos", "folhosa_funda")),
         _copa, (("redonda", {"copa": ["1.2m", "1m", "1.9m"]}),
                 ("gota", {"copa": ["85cm", "1.4m", "2.1m"], "tufos": "11", "tamanho": "0.34", "perfil": "0.9",
                           "material": "copa_folha", "miolo": "folha_escura"}),
                 ("guarda-sol", {"copa": ["1.5m", "60cm", "2.2m"], "tufos": "9", "tamanho": "0.36", "perfil": "-1"}),
                 ("pendente", {"copa": ["1.3m", "70cm", "2.4m"], "perfil": "-0.6", "pende": "2.4",
                               "material": "copa_folha", "miolo": "folha_escura"}),
                 ("moita", {"copa": ["70cm", "45cm", "45cm"], "tufos": "6", "tamanho": "0.45"})),
         TESTE, (_copa, _volumes, _na_massa, tufos, ramos, _lobulos, _raminhos, _sorte), vistas=QUATRO,
         flora="folhagem", ancoras=("superficie",)),
    Peca("copa_aberta", "A copa aberta: uma nuvem de folhas em cada ponta de galho, com os galhos e o chão à mostra "
         "entre elas (a árvore de galhos abertos, a de copa rala, a velha). Pede as pontas de um nó de antes. Deixa "
         "a superfície", (
             X("pontas", "ancora", "onde cai cada nuvem ('<nó>.pontas')"),
             X("raio", "comprimento", "a meia largura da nuvem"),
             X("achata", "escalar", "a meia altura da nuvem, em fração do raio", "0.6"),
             X("assenta", "escalar", "quanto o centro da nuvem fica acima da ponta, em fração da meia altura", "0.4"),
             X("tufos", "inteiro", "os lóbulos de cada nuvem", "4"),
             X("tamanho", "escalar", "o raio do lóbulo, em fração da nuvem", "0.5"),
             X("irregular", "escalar", "quanto as nuvens e os lóbulos variam", "0.15"),
             X("raminhos", "inteiro", "as bolas pequenas na borda de cada lóbulo", "1"), FOLHAGEM),
         _aberta, (("nuvens", {"pontas": "galhos.pontas", "raio": "55cm"}),
                   ("chatas", {"pontas": "galhos.pontas", "raio": "70cm", "achata": "0.35", "tufos": "5"}),
                   ("ralas", {"pontas": "galhos.pontas", "raio": "35cm", "tufos": "3", "material": "copa_folha"})),
         "tests/test_flora.py::test_a_copa_aberta_deixa_os_galhos_a_mostra",
         (_aberta, _volumes, _na_massa, tufos, _lobulos, _raminhos, _sorte), vistas=QUATRO, flora="folhagem",
         ancoras=("superficie",),
         apoio=(("tronco", "tronco_em_pe", {"altura": "2.2m", "base": "26cm", "topo": "12cm",
                                            "casca": "casca_sulcada"}),
                ("galhos", "galhos", {"base": "1.1m", "copa": ["1.3m", "70cm", "2.3m"], "n": "6", "alcance": "0.95",
                                      "ponta_v": ["-0.6", "0.4"], "largura": ["9cm", "13cm"], "ponta": "4cm",
                                      "bifurca": "0", "sobe": "90cm"}))),
    Peca("copa_conica", "A copa da conífera em andares: saias pregueadas, de pontas que caem, cada uma cobrindo a de "
         "baixo, e a ponta no topo. Com a base baixa a saia de baixo esconde o tronco (a câmera é de cima)", (
             X("base", "comprimento", "a altura da barra da saia de baixo"),
             X("altura", "comprimento", "a altura da ponta"), X("raio", "comprimento", "o raio da saia de baixo"),
             X("andares", "inteiro", "os andares (saias)", "6"),
             X("pontas", "inteiro", "as pontas da saia de baixo (as de cima têm menos; até 15)", "9"),
             X("recorte", "escalar", "quanto a saia entra entre duas pontas, em fração do raio dela", "0.35"),
             X("cai", "escalar", "quanto as pontas caem abaixo da barra, em fração da altura da saia", "0.3"),
             X("irregular", "escalar", "quanto o raio, o prumo e as pontas de cada andar variam", "0.12"),
             X("material", "material", "a folhagem (copa_agulha, copa_folhosa)", "copa_agulha")),
         _conica, (("alta", {"base": "50cm", "altura": "4m", "raio": "90cm", "andares": "8"}),
                   ("larga", {"base": "30cm", "altura": "2.4m", "raio": "1m", "andares": "5", "pontas": "11"}),
                   ("esguia", {"base": "90cm", "altura": "3.6m", "raio": "55cm", "andares": "7", "pontas": "6",
                               "recorte": "0.2", "material": "copa_folhosa"})),
         "tests/test_flora.py::test_a_conifera_lanca_a_sombra_dela", (_conica, _saia, _na_massa, _sorte), vistas=QUATRO,
         flora="folhagem"),
]
