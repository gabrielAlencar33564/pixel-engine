"""A flora de lâminas e de pontos: a touceira (lâminas que saem de um pé e abrem em arco: o capim, o junco, a
samambaia, a folha em espada e, no alto de um tronco, a palma) e o salpico (pontos de cor nas âncoras de outro nó:
a flor, o fruto, a espiga). São a planta que não é uma massa de folhas: a silhueta é de lâminas, e cada lâmina tem
o comprimento, a abertura e o tom sorteados pela semente do nó. As duas desenham qualquer vista."""

from __future__ import annotations

import math
from typing import Any

from ...views.camera import ELEVACAO_MDEG, PROFUNDIDADE_PERMILLE
from ..construtor import LINE, Parte, ellipse, polyline, q, qv
from .peca import Arg, Ctx, Peca

QUATRO = ("S", "E", "N", "W")
TRECHOS = 5  # os trechos do arco da lâmina
FIO = ("flat", "no_outline")  # a lâmina fina: chapada e sem contorno, mas lança a sombra dela no chão (não é detalhe)
PENA = ("no_inner_outline", "borda_serrilhada")  # a folha em pena: o corpo roliço, de beira serrilhada
# a folha larga lisa: chapada (um tom só, o do lado da luz dela), com o contorno de fora; com as faixas de luz e de
# sombra da peça lisa ela lia como um tubo
FOLHA_LISA = ("flat", "no_inner_outline")
SOBE_ANTES = 0.3  # o ponto de controle do arco: a 30 % do alcance a lâmina já está no alto
ABRE_MENOS = 0.35  # a lâmina mais fechada abre 35 % do pedido (poucas: a maioria abre perto do pedido)
ABRE_MENOS_A_LARGA = 0.75  # e a folha larga, 75 %: a roseta abre por igual
TOM = 0.3  # a lâmina sai clara ou escura quando o tom dela (de −1 a 1) passa disto
LADO_DA_LUZ = 0.45  # o tom é isto do lado para onde a lâmina abre (a esquerda da tela é a da luz) e o resto, sorteio
# a largura da folha em cada ponto do arco (fração da largura): estreita no pé, larga antes do meio, ponta fina
LARGURA_NO_ARCO = (0.3, 0.6, 1.0, 0.9, 0.55, 0.15)
RAIO_MINIMO = 32  # o menor raio da folha na IR (q8): 1/8 px
MIOLO_DA_ROSETA = 0.55  # o raio do miolo escuro no pé das folhas largas, em larguras da folha
FRENTE_LIVRE = 0.3  # a roseta de folhas largas gira até 0,15 fatia para cada lado de deixar a frente livre (e
# cada folha sai até 0,15 fatia do lugar dela: a mais próxima da frente fica a 0,2 fatia ou mais)
# a direção em que a câmera olha, girada com a vista (o chão a cos 45° e a altura a 0,6: a que a projeção achata num
# ponto): o ponto da massa com a normal nela cai no meio da figura, e o de normal deitada nela, no contorno
OLHAR = (math.cos(math.radians(ELEVACAO_MDEG / 1000)), PROFUNDIDADE_PERMILLE / 1000)
BEIRA = 0.3  # o salpico sorteia entre os pontos de normal a menos de ~45° da câmera de uma vista (``_beiras``)
SUPERFICIE = ".superficie"  # a âncora na face de um volume (a copa): o ponto entra na folhagem
VENCE = 2.0  # o detalhe vence a superfície que está até 2 px à frente dele (``raster/montagem.py``)
# o ponto da face entra na folhagem 0,6 do raio dele mais o que o detalhe vence: aparece na face que olha para a
# câmera até ~53° de lado, e a folhagem o cobre na beira do volume (onde ele cairia no contorno)
MERGULHO = 0.6
Vec = tuple[float, float, float]
X = Arg


def _arco(pe: Vec, az: float, comprimento: float, forma: tuple[float, float, int]) -> list[Vec]:
    """Os pontos da lâmina (``trechos`` mais um): sai do pé quase a prumo e abre no azimute ``az`` até ``abre`` do
    comprimento; a ponta cai ``cai`` da altura do arco (acima de 1, desce abaixo do pé, sem entrar no chão)."""
    abre, cai, trechos = forma
    alcance = comprimento * abre
    alto = comprimento * math.sqrt(max(0.04, 1 - abre * abre))
    dx, dy = math.sin(az), math.cos(az)
    ctrl = (pe[0] + dx * alcance * SOBE_ANTES, pe[1] + dy * alcance * SOBE_ANTES, pe[2] + alto * (1 + 0.5 * cai))
    fim = (pe[0] + dx * alcance, pe[1] + dy * alcance, max(0.0, pe[2] + alto * (1 - cai)))
    out = []
    for i in range(trechos + 1):
        s = i / trechos
        out.append((ctrl[0] * 2 * s * (1 - s) + pe[0] * (1 - s) ** 2 + fim[0] * s * s,
                    ctrl[1] * 2 * s * (1 - s) + pe[1] * (1 - s) ** 2 + fim[1] * s * s,
                    ctrl[2] * 2 * s * (1 - s) + pe[2] * (1 - s) ** 2 + fim[2] * s * s))
    return out


def _folha(c: Ctx, pid: str, materiais: tuple[str, str], arco: list[Vec], forma: tuple[float, bool]) -> None:
    """A folha larga: o corpo ao longo do arco (estreito no pé, largo antes do meio e de ponta fina), no grupo de
    contorno do nó (sem linha entre as folhas), e a nervura escura por cima: cada folha se lê pela nervura dela. Em
    pena, o corpo é roliço e a beira sai serrilhada dente a dente (a marca ``borda_serrilhada``, no render); lisa, o
    corpo é chapado."""
    corpo, nervura = materiais
    largura, pena = forma
    geo = {"type": "tapered_polyline", "points_q8": [qv(*p) for p in arco],
           "radii_q8": [max(RAIO_MINIMO, q(largura / 2 * k)) for k in LARGURA_NO_ARCO]}
    c.b.part(pid, corpo, geo, Parte(group=c.grupo, tags=PENA if pena else FOLHA_LISA))
    # a nervura corre por cima do corpo (o raio dele acima do eixo): por dentro, o corpo a cobriria
    alto = [(x, y, z + largura / 2 * k) for (x, y, z), k in zip(arco[:-1], LARGURA_NO_ARCO, strict=False)]
    c.b.part(f"{pid}_{'pena' if pena else 'nervura'}", nervura, polyline([qv(*p) for p in alto], 1),
             Parte(group=c.grupo, tags=LINE))


def _lamina(c: Ctx, pid: str, material: str, arco: list[Vec]) -> None:
    """A lâmina fina: um traço de 1 px, sem contorno."""
    c.b.part(pid, material, polyline([qv(*p) for p in arco], 1), Parte(group=c.grupo, tags=FIO))


def _lado_da_luz(az: float, azimute_mdeg: int) -> float:
    """De −1 a 1: quanto a lâmina que abre no azimute ``az`` (do mundo) vai para a esquerda da tela da vista (a luz
    vem de cima à esquerda da tela em toda vista)."""
    return -math.sin(az - math.radians(azimute_mdeg / 1000))


def _material(a: dict[str, Any], tom: float, pena: bool) -> str:
    """O material da lâmina pelo tom dela (de −1 a 1); o corpo da folha em pena nunca é do tom escuro (esse é o da
    nervura, que lê cada folha da fronde). A folha lisa do lado da sombra é escura, e a nervura some nela."""
    if tom > TOM:
        return str(a["claro"])
    return str(a["escuro"] if tom < -TOM and not pena else a["material"])


def _touceira(c: Ctx, a: dict[str, Any]) -> None:
    """``n`` lâminas em volta do pé, uma a cada fatia da volta: cada uma com o pé sorteado dentro do ``raio``, o
    comprimento na faixa, a abertura de 35 % a 100 % do pedido (a maioria perto dele) e o tom (o claro do lado da
    luz, o escuro do outro, com sorteio). O lado da luz é o da tela: em cada vista a lâmina toma o tom dela ali (o
    material da vista S, trocado nas outras). A roseta de folhas largas tem o miolo escuro no pé. Deixa a âncora
    ``pontas`` (a ponta de cada lâmina)."""
    st, n = c.st, a["n"]
    larga = a["largura"] > 0
    giro = st.randint(0, 999) / 1000
    if larga:  # nenhuma folha larga aponta para a câmera (viraria um talo em pé no meio da roseta)
        giro = 0.5 + FRENTE_LIVRE * (giro - 0.5)
    fecha = 1 - (ABRE_MENOS_A_LARGA if larga else ABRE_MENOS)
    pontas: list[Vec] = []
    for i in range(n):
        az = 2 * math.pi * (i + giro + st.randint(-30, 30) / 100 * (0.5 if larga else 1.0)) / n
        longe = a["raio"] * st.randint(0, 100) / 100
        pe = (a["pe"][0] + math.sin(az) * longe, a["pe"][1] + math.cos(az) * longe, a["pe"][2])
        comprimento = a["altura"][0] + (a["altura"][1] - a["altura"][0]) * st.randint(0, 100) / 100
        abre = min(0.98, a["abre"] * (1 - fecha * (st.randint(0, 100) / 100) ** 2))
        arco = _arco(pe, az, comprimento, (abre, a["cai"], TRECHOS))
        sorteio = (1 - LADO_DA_LUZ) * st.randint(-100, 100) / 100
        pid = f"{c.pid}_{i:02d}"
        tons = {v: _material(a, LADO_DA_LUZ * _lado_da_luz(az, giro_da_vista) + sorteio, larga and a["pena"])
                for v, giro_da_vista in c.vistas.items()}
        material = tons.get("S", next(iter(tons.values())))
        if larga:
            _folha(c, pid, (material, a["escuro"]), arco, (a["largura"], a["pena"]))
        else:
            _lamina(c, pid, material, arco)
        for v, outro in tons.items():
            if outro != material:
                c.b.na_vista(v, pid, outro)
        pontas.append(arco[-1])
    if larga:  # o miolo da roseta: o pé das folhas largas é o ponto mais escuro da planta
        raio = a["largura"] * MIOLO_DA_ROSETA
        x, y, z = a["pe"]
        c.b.part(f"{c.pid}_miolo", a["escuro"], ellipse(qv(x, y, z + raio), qv(raio, raio, raio)),
                 Parte(group=c.grupo, tags=LINE))
    c.deixa("pontas", pontas)


def _normais(pts: list[Vec]) -> list[Vec]:
    """A normal de cada ponto na massa dos pontos (o elipsoide da caixa deles): sai do meio dela."""
    meio = [(max(p[k] for p in pts) + min(p[k] for p in pts)) / 2 for k in range(3)]
    meia = [max(1.0, (max(p[k] for p in pts) - min(p[k] for p in pts)) / 2) for k in range(3)]
    out = []
    for p in pts:
        u = [(p[k] - meio[k]) / meia[k] for k in range(3)]
        tam = math.hypot(*u) or 1.0
        out.append((u[0] / tam, u[1] / tam, u[2] / tam))
    return out


def _beiras(normais: list[Vec], azimutes: list[int]) -> list[float]:
    """Quanto cada ponto fica perto do contorno da massa na vista que melhor o vê: 1 menos o quanto a normal dele
    olha para a câmera dela (0 no meio da figura; 1 no contorno; mais, do lado de lá em toda vista)."""
    olhar = [(math.sin(math.radians(az / 1000)) * OLHAR[0], math.cos(math.radians(az / 1000)) * OLHAR[0], OLHAR[1])
             for az in azimutes]
    return [1 - max(sum(n[k] * m[k] for k in range(3)) / math.hypot(*m) for m in olhar) for n in normais]


def _salpico(c: Ctx, a: dict[str, Any]) -> None:
    """Um ponto de cor em ``n`` dos pontos da âncora ``em``, sorteados entre os que alguma vista vê de frente, no meio
    da figura (os ``n`` de menos beira, se não há tantos): o ponto da beira cai no contorno, e o do lado de lá,
    escondido. Na face de um volume, o ponto entra na folhagem: a vista que vê a face de frente o mostra, e a que a
    vê de lado (onde ele cairia no contorno) o tem coberto pela folhagem."""
    pts = c.ancora(a["em"])
    normais = _normais(pts) if pts else []
    beiras = _beiras(normais, list(c.vistas.values()))
    ordem = sorted(range(len(pts)), key=lambda k: beiras[k])
    escolha = [k for j, k in enumerate(ordem) if j < a["n"] or beiras[k] <= BEIRA]
    afunda = MERGULHO * (a["raio"] + VENCE) if a["em"].endswith(SUPERFICIE) else 0.0
    for i in range(min(a["n"], len(escolha))):
        k = escolha.pop(c.st.randint(0, len(escolha) - 1))
        x, y, z = (pts[k][t] - normais[k][t] * afunda for t in range(3))
        alto = a["raio"] * a["alonga"]
        c.b.part(f"{c.pid}_{i:02d}", a["material"], ellipse(qv(x, y, z), qv(a["raio"], a["raio"], alto)),
                 Parte(group=c.grupo, tags=LINE))


MOITA = ("moita", "copa", {"copa": ["60cm", "40cm", "40cm"], "tufos": "6", "tamanho": "0.45"})
PECAS_ERVAS = [
    Peca("touceira", "Lâminas que saem de um pé e abrem em arco, cada uma com o comprimento, a abertura e o tom "
         "sorteados: finas, o capim e o junco; largas, a folha em espada; largas e em pena, a samambaia; com o pé no "
         "alto de um tronco, a palma. Deixa as pontas", (
             X("altura", "faixa", "o comprimento das lâminas, sorteado na faixa"),
             X("n", "inteiro", "lâminas", "9"),
             X("abre", "escalar", "quanto a lâmina mais aberta se afasta do pé, em fração do comprimento (0.2 = em "
               "pé; 0.9 = deitada)", "0.5"),
             X("cai", "escalar", "quanto a ponta cai da altura do arco (0 = reta; 1 = volta à altura do pé)", "0.3"),
             X("largura", "comprimento", "a largura da folha (0 = lâmina fina, de 1 px)", "0"),
             X("pena", "bool", "a folha larga em pena (a samambaia, a palma): roliça e de beira serrilhada, em vez "
               "de chapada e lisa (as duas com a nervura no tom escuro)", False),
             X("raio", "comprimento", "o raio do pé: as lâminas nascem espalhadas nele", "0"),
             X("pe", "ponto", "de onde nasce (o chão, ou o alto de um tronco)", ["0", "0", "0"]),
             X("material", "material", "a lâmina comum", "capim"),
             X("claro", "material", "a lâmina do lado da luz (a esquerda da tela)", "capim_claro"),
             X("escuro", "material", "a lâmina do lado da sombra", "capim_escuro")),
         _touceira, (("capim", {"altura": ["18cm", "40cm"], "n": "14", "abre": "0.45", "raio": "12cm"}),
                     ("junco", {"altura": ["70cm", "1.2m"], "n": "9", "abre": "0.22", "cai": "0.05",
                                "raio": "15cm"}),
                     ("samambaia", {"altura": ["50cm", "75cm"], "n": "8", "abre": "0.75", "cai": "0.45",
                                    "largura": "22cm", "pena": True, "material": "folha", "claro": "folha_clara",
                                    "escuro": "folha_escura"}),
                     ("espada", {"altura": ["50cm", "80cm"], "n": "11", "abre": "0.6", "cai": "0",
                                 "largura": "10cm", "material": "agulha", "claro": "agulha_clara",
                                 "escuro": "agulha_escura"})),
         "tests/test_ervas.py::test_a_touceira_e_de_laminas",
         (_touceira, _lamina, _folha, _arco, _lado_da_luz, _material), vistas=QUATRO, flora="lamina",
         ancoras=("pontas",)),
    Peca("salpico", "Pontos de cor sobre outro nó: a flor e o fruto na superfície de uma copa, a espiga na ponta "
         "de uma lâmina, o broto na ponta de um galho. Pede a âncora de um nó de antes", (
             X("em", "ancora", "onde caem os pontos ('<nó>.superficie', '<nó>.pontas')"),
             X("material", "material", "a cor do ponto"), X("n", "inteiro", "quantos pontos", "8"),
             X("raio", "comprimento", "o raio do ponto (3 cm = 1 px)", "3cm"),
             X("alonga", "escalar", "a altura do ponto, em raios (1 = redondo; 3 = a espiga em pé)", "1")),
         _salpico, (("flores", {"em": "moita.superficie", "material": "olho_claro", "n": "9"}),
                    ("frutos", {"em": "moita.superficie", "material": "pano_vermelho", "n": "6", "raio": "5cm"}),
                    ("botões", {"em": "moita.superficie", "material": "ambar", "n": "14"})),
         "tests/test_ervas.py::test_o_salpico_cai_do_lado_da_camera", (_salpico, _normais, _beiras), vistas=QUATRO,
         apoio=(MOITA,)),
]
