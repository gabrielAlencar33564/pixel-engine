"""A copa em volumes, para a câmera de cima: a da folhosa em tufos (elipsoides em anéis em volta do centro, por
dentro do elipsoide da copa) e a da conífera em andares (saias cônicas, sólidos de revolução). São formas simples,
que se preveem no pixel: a luz, a oclusão e a sombra no chão saem da forma no render, e a peça desenha qualquer
vista. A copa é ``[meia largura, meia altura, altura do centro]``."""

from __future__ import annotations

import math
from typing import Any

from ...core.rng import Stream
from ..construtor import Parte, ellipse, q, qv
from .peca import Arg, Ctx, Peca

TESTE = "tests/test_flora.py::test_a_copa_e_uma_massa_so"
QUATRO = ("S", "E", "N", "W")
# os anéis de tufos: a elevação (graus), os tufos em fração do anel do meio (0 = um só, no alto) e a fase na volta
ANEIS = ((90.0, 0.0, 0.0), (42.0, 0.7, 0.0), (4.0, 1.0, 0.5), (-32.0, 0.7, 0.0))
PENDE_ABAIXO_DE = 20.0  # os anéis abaixo desta elevação pendem (o ramo que cai)
AFINA = 0.4  # quanto o tufo que pende afina (com ``pende`` 1 ou mais)
MIOLO = 0.62  # o miolo escuro, em fração da copa: fecha os vãos entre os tufos
TUFO_DO_GALHO = 0.8  # o tufo na ponta de um galho, em fração do tufo da copa
ESTACOES = 8  # as estações de cada saia da conífera
CURVA_DA_SAIA = 0.8  # a saia fecha depressa embaixo e devagar em cima (o expoente do perfil)
SOBE = 1.6  # cada saia sobe 1,6 passo: entra na de cima
PONTA = 0.3  # o raio da ponta da conífera (px)
Vec = tuple[float, float, float]
X = Arg


def _sorte(st: Stream) -> float:
    """De −1 a 1."""
    return st.randint(-100, 100) / 100


def tufos(st: Stream, a: dict[str, Any]) -> list[tuple[Vec, Vec]]:
    """O centro e os raios de cada tufo, do alto para baixo. O tufo de tamanho ``f`` fica a ``1 − f`` do centro da
    copa, na direção dele: encosta por dentro no elipsoide da copa e nunca passa dele (a altura da copa é exata)."""
    meia_l, meia_a, cz = a["copa"]
    eixos = (meia_l, meia_l * a["fundo"], meia_a)
    irr = a["irregular"]
    out: list[tuple[Vec, Vec]] = []
    for el, fracao, fase in ANEIS:
        n = max(1, round(a["tufos"] * fracao))
        for i in range(n):
            az = 2 * math.pi * (i + fase + irr * _sorte(st)) / n
            e = math.radians(el) + (0.5 * irr * _sorte(st) if fracao else 0.0)
            f = min(0.95, a["tamanho"] * (1 + irr * _sorte(st)))
            d = (math.cos(e) * math.sin(az), math.cos(e) * math.cos(az), math.sin(e))
            cx, cy, z = (d[k] * eixos[k] * (1 - f) for k in range(3))
            rz = eixos[2] * f
            cai = rz * a["pende"] if el < PENDE_ABAIXO_DE else 0.0
            cai = max(0.0, min(cai, (cz + z - rz) / 2))  # a ponta do ramo não entra no chão
            fino = 1 - AFINA * min(1.0, cai / rz)  # o ramo que cai é mais fino que o tufo
            out.append(((cx, cy, cz + z - cai), (eixos[0] * f * fino, eixos[1] * f * fino, rz + cai)))
    return out


def _copa(c: Ctx, a: dict[str, Any]) -> None:
    """O miolo escuro e os tufos, cada um sombreado como um volume e todos no grupo de contorno do nó (sem linha
    entre eles); mais um tufo na ponta de cada galho de ``pontas``."""
    meia_l, meia_a, cz = a["copa"]
    eixos = (meia_l, meia_l * a["fundo"], meia_a)
    c.b.part(f"{c.pid}_miolo", a["miolo"], ellipse(qv(0, 0, cz), qv(*(e * MIOLO for e in eixos))),
             Parte(group=c.grupo))
    massas = tufos(c.st, a)
    f = a["tamanho"] * TUFO_DO_GALHO
    massas += [((x, y, z), (eixos[0] * f, eixos[1] * f, eixos[2] * f)) for x, y, z in c.ancora(a["pontas"])]
    for i, (centro, raios) in enumerate(massas):
        c.b.part(f"{c.pid}_{i:02d}", a["material"], ellipse(qv(*centro), qv(*raios)),
                 Parte(group=c.grupo, tags=("volume_sphere",)))


def _conica(c: Ctx, a: dict[str, Any]) -> None:
    """Os andares de baixo para cima: cada saia abre no raio do andar (que cai com a altura) e fecha para dentro da
    de cima; a última fecha na ponta. Cada andar tem o seu grupo de contorno: a linha e a sombra sob a saia separam
    os andares."""
    base, n, irr = a["base"], a["andares"], a["irregular"]
    passo = (a["altura"] - base) / (n - 1 + SOBE)
    for i in range(n):
        z0 = base + i * passo
        topo = i == n - 1
        r0 = a["raio"] * (1 - i / n) * (1 + irr * _sorte(c.st))
        r1 = PONTA if topo else r0 * a["saia"]
        alto = a["altura"] - z0 if topo else passo * SOBE
        desvio = 0.0 if topo else 0.5 * irr * r0 * _sorte(c.st)  # a saia nunca é um torneado perfeito
        est = [[q(alto * k / ESTACOES), q(r0 + (r1 - r0) * (k / ESTACOES) ** CURVA_DA_SAIA),
                q(desvio * (1 - k / ESTACOES))] for k in range(ESTACOES + 1)]
        c.b.part(f"{c.pid}_{i:02d}", a["material"], {"type": "revolution", "origin_q8": qv(0, 0, z0), "stations": est},
                 Parte(group=f"{c.grupo}_{i:02d}"))


COPA = X("copa", "ponto", "a copa: meia largura, meia altura e a altura do centro")
PECAS_COPA = [
    Peca("copa", "A copa da folhosa em volumes: tufos redondos em volta do centro, por dentro do elipsoide da copa. "
         "Cobre o tronco pela frente (a câmera é de cima) e lança a sombra dela no chão; no chão, sem tronco, é a "
         "moita", (
             COPA, X("fundo", "escalar", "a meia profundidade, em fração da meia largura (1 = redonda vista de cima)",
                     "1"),
             X("tufos", "inteiro", "os tufos do anel do meio (o de cima e o de baixo têm 70 % dele; mais um no alto)",
               "7"),
             X("tamanho", "escalar", "o raio do tufo, em fração da copa (maior = menos recortada)", "0.45"),
             X("irregular", "escalar", "quanto o tamanho e o lugar de cada tufo variam (0 = regular)", "0.12"),
             X("pende", "escalar", "os tufos de baixo descem tanto, em fração da altura deles (o ramo que cai)", "0"),
             X("pontas", "ancora", "as pontas dos galhos onde sai um tufo a mais ('<nó>.pontas')", ""),
             X("material", "material", "a folhagem (copa_folhosa, copa_folha, copa_agulha)", "copa_folhosa"),
             X("miolo", "material", "o miolo escuro entre os tufos", "folhosa_funda")),
         _copa, (("redonda", {"copa": ["1.2m", "1m", "1.9m"]}),
                 ("pendente", {"copa": ["1.3m", "60cm", "2.4m"], "tufos": "12", "tamanho": "0.28", "pende": "2.5",
                               "material": "copa_folha", "miolo": "folha_escura"}),
                 ("moita", {"copa": ["70cm", "45cm", "45cm"], "tufos": "5", "tamanho": "0.5"})),
         TESTE, (_copa, tufos, _sorte), vistas=QUATRO),
    Peca("copa_conica", "A copa da conífera em volumes: andares em saia, cada um cobrindo o de baixo, e a ponta no "
         "topo. Com a base baixa a saia de baixo esconde o tronco (a câmera é de cima)", (
             X("base", "comprimento", "a altura da barra da saia de baixo"),
             X("altura", "comprimento", "a altura da ponta"), X("raio", "comprimento", "o raio da saia de baixo"),
             X("andares", "inteiro", "os andares (saias)", "6"),
             X("saia", "escalar", "quanto cada saia fecha no alto, em fração do raio dela (menor = mais recortada)",
               "0.4"),
             X("irregular", "escalar", "quanto o raio e o prumo de cada andar variam (0 = regular)", "0.08"),
             X("material", "material", "a folhagem (copa_agulha, copa_folhosa)", "copa_agulha")),
         _conica, (("alta", {"base": "50cm", "altura": "4m", "raio": "90cm", "andares": "8"}),
                   ("larga", {"base": "30cm", "altura": "2.4m", "raio": "1m", "andares": "5"}),
                   ("esguia", {"base": "90cm", "altura": "3.6m", "raio": "55cm", "andares": "7", "saia": "0.55",
                               "material": "copa_folhosa"})),
         "tests/test_flora.py::test_a_conifera_lanca_a_sombra_dela", (_conica, _sorte), vistas=QUATRO),
]
