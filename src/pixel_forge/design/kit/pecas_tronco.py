"""O tronco e os galhos, em volumes: o tronco em pé como sólido de revolução com forma de tronco (o pé que abre, o
fuste que engrossa e afina, a curva, as raízes à mostra e os nós; o volume e a textura da casca fazem a sombra e o
veio) e os galhos roliços em volta dele, que sobem até dentro da copa e deixam a âncora das pontas para a copa pôr
um tufo em cada uma. As duas peças desenham qualquer vista."""

from __future__ import annotations

import math
from typing import Any

from ..construtor import Parte, ellipse, q, qv
from .peca import Arg, Ctx, Peca

TESTE = "tests/test_kit.py::test_cada_variacao_monta"
QUATRO = ("S", "E", "N", "W")
X = Arg
COPA = X("copa", "ponto", "a copa: meia largura, meia altura e a altura do centro")
COPA_V = ["1.1m", "1.3m", "2.6m"]
ESTACOES = 20  # as estações do fuste (mais as do pé)
NO_PE = (0.12, 0.25, 0.4, 0.6, 0.9, 1.3)  # as estações a mais onde o pé abre, em larguras do tronco
PE_SOBE = 0.45  # o pé cai a 1/e a esta altura, em larguras do tronco
ONDAS = ((0.6, 1.5), (0.4, 3.7))  # o perfil irregular: o peso e as voltas de cada onda ao longo da altura
RAIZ = (0.45, 0.2, 0.75, 0.45)  # a raiz, em larguras do tronco: de onde sai, o raio, o alcance; e o raio da ponta
NO = (0.3, 0.85, 0.5, 0.75)  # os nós: de onde a onde ficam na altura, o raio e o centro (frações do raio do fuste)
NO_ABRE = 75  # até onde o nó sai da frente, para cada lado (graus)
NO_MINIMO = 1.2  # o menor nó que se lê (px)
TRECHOS = 6  # os trechos do galho roliço
ABRE_NO_ALTO = (0.25, 0.75)  # o ponto de controle: a 25 % da abertura já subiu 75 % (sobe a prumo e depois abre)
SAIDA_DO_FINO = 0.6  # o galho fino sai a 60 % do grosso
DESVIO_NA_FATIA = 15  # quanto o galho sai do meio da fatia dele (% da fatia, para cada lado)
PULA = 3  # os galhos escalonados: o vizinho na volta sai 3 degraus acima (ou abaixo), não o seguinte
CURTO_NO_ALTO = 0.4  # o galho que sai do alto alcança 40 % menos
ALTO_NO_ALTO = 0.6  # e a ponta dele sobe até 60 % do que falta da faixa
RAIO_MINIMO = 32  # o menor raio do galho roliço na IR (q8): 1/8 px
Vec = tuple[float, float, float]


def _perfil(c: Ctx, a: dict[str, Any]) -> list[tuple[float, float, float]]:
    """As estações (z, raio, desvio em x) do tronco, de baixo para cima: o fuste afina de ``base`` a ``topo`` e
    desvia ``inclinacao`` no alto; o pé abre embaixo (``pe``) e some à altura de uma largura do tronco; o raio
    engrossa e afina ao longo da altura (``irregular``, nulo na base e no topo: as duas larguras são as pedidas); o
    eixo ondula em S (``curva``) e volta ao prumo no alto. Com tudo isso em zero, é o cone do `pixel-engine`."""
    h, b0, b1, lean = a["altura"], a["base"], a["topo"], a["inclinacao"]
    fases = [c.st.randint(0, 99) / 100 for _ in range(2)]
    # o cone tem 21 estações iguais (i de 20); o pé pede mais algumas embaixo, onde ele abre (z de h)
    onde: list[tuple[float, float]] = [(float(i), float(ESTACOES)) for i in range(ESTACOES + 1)]
    if a["pe"] > 0:
        passo = h / ESTACOES
        onde += [(z, h) for k in NO_PE if (z := k * b0) < h and min(abs(z - i * passo) for i in range(3)) > 0.5]
    out = []
    for num, den in sorted(onde, key=lambda f: f[0] / f[1]):
        t = num / den
        z = h * num / den
        onda = sum(peso * math.sin(2 * math.pi * (voltas * t + fase))
                   for (peso, voltas), fase in zip(ONDAS, fases, strict=True))
        engrossa = (1 + a["pe"] * math.exp(-z / (PE_SOBE * b0))) * (1 + a["irregular"] * onda * math.sin(math.pi * t))
        out.append((z, (b0 + (b1 - b0) * num / den) / 2 * engrossa,
                    lean * (num / den) ** 2 + a["curva"] * math.sin(2 * math.pi * t)))
    return out


def _no_perfil(perfil: list[tuple[float, float, float]], z: float) -> tuple[float, float]:
    """O raio e o desvio do tronco na altura ``z`` (entre as estações)."""
    for (z0, r0, d0), (z1, r1, d1) in zip(perfil, perfil[1:], strict=False):
        if z <= z1:
            f = (z - z0) / (z1 - z0)
            return r0 + (r1 - r0) * f, d0 + (d1 - d0) * f
    return perfil[-1][1], perfil[-1][2]


def _raizes(c: Ctx, a: dict[str, Any], perfil: list[tuple[float, float, float]], como: Parte) -> None:
    """As raízes à mostra: saem do pé, uma a cada fatia da volta (a primeira para a frente), e deitam no chão."""
    n, b0 = a["raizes"], a["base"]
    for j in range(n):
        az = 2 * math.pi * (j + c.st.randint(-DESVIO_NA_FATIA, DESVIO_NA_FATIA) / 100) / n
        dx, dy = math.sin(az), math.cos(az)
        alto = RAIZ[0] * b0
        r0, desvio = _no_perfil(perfil, alto)
        grossa = RAIZ[1] * b0 * c.st.randint(80, 110) / 100
        longe = r0 + RAIZ[2] * b0 * c.st.randint(75, 115) / 100
        pts = [(desvio + dx * r0 * 0.6, dy * r0 * 0.6, alto), (dx * (r0 + longe) / 2, dy * (r0 + longe) / 2, grossa),
               (dx * longe, dy * longe, RAIZ[3] * grossa)]
        geo = {"type": "tapered_polyline", "points_q8": [qv(*p) for p in pts],
               "radii_q8": [max(RAIO_MINIMO, q(grossa * k)) for k in (1.0, 0.7, RAIZ[3])]}
        c.b.part(f"{c.pid}_raiz_{j}", a["casca"], geo, como)


def _nos(c: Ctx, a: dict[str, Any], perfil: list[tuple[float, float, float]], como: Parte) -> None:
    """Os nós da casca: calombos meio enterrados no fuste, do lado da câmera e dos lados (atrás não se veem)."""
    h = a["altura"]
    for j in range(a["nos"]):
        z = h * (NO[0] + (NO[1] - NO[0]) * (j + c.st.randint(20, 80) / 100) / a["nos"])
        az = math.radians(c.st.randint(-NO_ABRE, NO_ABRE))
        r, desvio = _no_perfil(perfil, z)
        raio = max(NO_MINIMO, r * NO[2])
        c.b.part(f"{c.pid}_no_{j}", a["casca"],
                 ellipse(qv(desvio + math.sin(az) * r * NO[3], math.cos(az) * r * NO[3], z),
                         qv(raio, raio, raio * 1.3)), como)


def _tronco(c: Ctx, a: dict[str, Any]) -> None:
    """O sólido de revolução pelas estações do perfil (a base em arco, o topo em tampa oval), as raízes e os nós, no
    mesmo grupo de contorno."""
    perfil = _perfil(c, a)
    como = Parte(bone=c.osso(0.0)[0], group=c.grupo, tags=("no_inner_outline",))
    c.b.part(c.pid, a["casca"], {"type": "revolution", "origin_q8": qv(0, 0, 0),
                                 "stations": [[q(z), q(r), q(dx)] for z, r, dx in perfil]},
             Parte(bone=c.osso(0.0)[0], group=c.grupo))
    _raizes(c, a, perfil, como)
    _nos(c, a, perfil, como)


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
    dentro da copa. Com ``bifurca``, um galho fino sai a 60 % dele; com ``sobe``, os galhos saem escalonados do
    tronco. Deixa a âncora ``pontas`` (x, y, z)."""
    meia_l, meia_a, cz = a["copa"]
    st, n = c.st, a["n"]
    degrau = st.randint(0, n - 1) if a["sobe"] > 0 else 0
    pontas: list[Vec] = []
    for j in range(n):
        az = 2 * math.pi * (j + a["fase"] + st.randint(-DESVIO_NA_FATIA, DESVIO_NA_FATIA) / 100) / n
        # com ``sobe``, cada galho sai de uma altura (a ordem delas na volta é da semente): o de baixo vai mais
        # longe e fica mais baixo, o de cima sai mais curto e mais alto
        u = ((j * PULA + degrau) % n) / max(1, n - 1) if a["sobe"] > 0 else 0.0
        alcance = meia_l * a["alcance"] * st.randint(80, 100) / 100 * (1 - CURTO_NO_ALTO * u)
        r = st.randint(0, 100) / 100
        v = a["ponta_v"][0] + (a["ponta_v"][1] - a["ponta_v"][0]) * (r + ALTO_NO_ALTO * u * (1 - r))
        p0 = (0.0, 0.0, a["base"] + a["sobe"] * u)
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
    Peca("tronco_em_pe", "Tronco em pé, com forma de tronco e não de cilindro: o pé abre no chão, o fuste engrossa e "
         "afina, pode ondular, mostrar raízes e nós; a casca dá o veio (sulcada, em pé; anelada, deitada)", (
             X("altura", "comprimento", "até onde ele sobe"),
             X("base", "comprimento", "a largura do fuste embaixo (o pé abre além dela)"),
             X("topo", "comprimento", "a largura em cima"), X("inclinacao", "comprimento", "quanto o topo desvia", "0"),
             X("casca", "material", "a casca (casca_sulcada, casca_anelada; lisas: casca, casca_clara)"),
             X("pe", "escalar", "quanto o pé abre no chão, em fração da largura (0 = sem pé; some a 1 largura de "
               "altura)", "0.35"),
             X("irregular", "escalar", "quanto o fuste engrossa e afina ao longo da altura (0 = reto; só se lê em "
               "tronco de 40 cm ou mais)", "0.12"),
             X("curva", "comprimento", "quanto o eixo ondula em S (volta ao prumo no alto)", "0"),
             X("raizes", "inteiro", "raízes à mostra em volta do pé (a primeira para a frente)", "0"),
             X("nos", "inteiro", "nós na casca, do lado da câmera", "0")),
        _tronco, (("novo", {"altura": "2.2m", "base": "16cm", "topo": "10cm", "curva": "5cm",
                            "casca": "casca_anelada"}),
                  ("de quintal", {"altura": "1.6m", "base": "30cm", "topo": "22cm", "inclinacao": "6cm",
                                  "casca": "casca_sulcada"}),
                  ("velho", {"altura": "1.8m", "base": "70cm", "topo": "45cm", "pe": "0.5", "irregular": "0.18",
                             "curva": "6cm", "raizes": "5", "nos": "2", "casca": "casca_sulcada"})),
        "tests/test_flora.py::test_o_pe_do_tronco_abre", (_tronco, _perfil, _no_perfil, _raizes, _nos),
        vistas=QUATRO, flora="lenho"),
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
        X("sobe", "comprimento", "os galhos saem escalonados ao longo desta altura do tronco, a partir da base "
          "(0 = todos do mesmo ponto)", "0"),
        X("material", "material", "a casca", "casca")),
        _galhos, (("em volta", {"base": "1m", "copa": COPA_V, "n": "5", "largura": ["12cm", "16cm"], "ponta": "4cm"}),
                  ("abertos", {"base": "80cm", "copa": COPA_V, "n": "7", "alcance": "0.95", "ponta_v": ["-0.7", "-0.2"],
                               "largura": ["12cm", "17cm"], "ponta": "5cm", "bifurca": "0"}),
                  ("secos", {"base": "1.2m", "copa": COPA_V, "n": "4", "alcance": "0.8", "ponta_v": ["0", "0.8"],
                             "largura": ["10cm", "14cm"], "ponta": "3cm", "bifurca": "1",
                             "material": "casca_clara"})),
        "tests/test_flora.py::test_os_galhos_abrem_em_volta_do_tronco", (_galhos, _rolico, _no_caminho),
        vistas=QUATRO, flora="lenho", ancoras=("pontas",)),
]
