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
COM_CONTORNO = 5.0  # px: a folha lisa desta largura para cima tem o contorno dela (a mais fina seria só linha)
SOBE_ANTES = 0.3  # o ponto de controle do arco: a 30 % do alcance a lâmina já está no alto
ABRE_MENOS = 0.35  # a lâmina mais fechada abre 35 % do pedido (poucas: a maioria abre perto do pedido)
ABRE_MENOS_A_LARGA = 0.75  # e a folha larga, 75 %: a roseta abre por igual
TOM = 0.3  # a lâmina sai clara ou escura quando o tom dela (de −1 a 1) passa disto
LADO_DA_LUZ = 0.45  # o tom é isto do lado para onde a lâmina abre (a esquerda da tela é a da luz) e o resto, sorteio
# a largura da folha em cada ponto do arco (fração da largura): estreita no pé, larga antes do meio, ponta fina
LARGURA_NO_ARCO = (0.3, 0.6, 1.0, 0.9, 0.55, 0.15)
RAIO_MINIMO = 32  # o menor raio da folha na IR (q8): 1/8 px
MIOLO_DA_ROSETA = 0.55  # o raio do miolo escuro no pé das folhas largas, em larguras da folha
FRENTE_LIVRE = 0.3  # a roseta de folhas largas gira até 0,15 do vão entre as câmeras para cada lado do meio dele (e
# cada folha sai até 0,15 fatia do lugar dela: na vista S, a mais próxima da frente fica a 0,2 fatia ou mais)
FOLGA = 0.2  # e em toda vista declarada: a folha a menos de 0,2 fatia de uma câmera é empurrada até 0,2 dela
# a direção em que a câmera olha, girada com a vista (o chão a cos 45° e a altura a 0,6: a que a projeção achata num
# ponto): o ponto da massa com a normal nela cai no meio da figura, e o de normal deitada nela, no contorno
OLHAR = (math.cos(math.radians(ELEVACAO_MDEG / 1000)), PROFUNDIDADE_PERMILLE / 1000)
BEIRA = 0.3  # o salpico sorteia entre os pontos de normal a menos de ~45° da câmera de uma vista (``_beiras``)
SUPERFICIE = ".superficie"  # a âncora na face de um volume (a copa): o ponto entra na folhagem
VENCE = 2.0  # o detalhe vence a superfície que está até 2 px à frente dele (``raster/montagem.py``)
# o ponto da face entra na folhagem 0,6 do raio dele mais o que o detalhe vence: aparece na face que olha para a
# câmera até ~53° de lado, e a folhagem o cobre na beira do volume (onde ele cairia no contorno)
MERGULHO = 0.6
NERVURA = 0.5  # px que a nervura da folha larga vem à frente do corpo dela (o raio, no eixo), no z-buffer
# nas pontas (da lâmina, do galho) o salpico sorteia entre esta fração das mais altas na tela (no mínimo ``n``): a
# ponta que abre para a câmera desce na tela, e a flor nela ficava na altura do pé
PONTAS_ALTAS = 0.5
LONGE = 1.0  # px entre as beiras de dois pontos de cor nas pontas, em toda vista: as flores não se amontoam
Vec = tuple[float, float, float]
Tela = tuple[float, float]  # (u, v) na tela de uma vista, em px
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
    """A folha larga: o corpo ao longo do arco (estreito no pé, largo antes do meio e de ponta fina) e a nervura
    escura no eixo: cada folha se lê pela nervura dela. Em pena, o corpo é roliço e a beira sai serrilhada dente a
    dente (a marca ``borda_serrilhada``, no render), no grupo de contorno do nó (sem linha entre as folhas); lisa, o
    corpo é chapado e, se cabe o contorno, a nervura e o tom, tem o grupo de contorno dele: a linha entre ela e a de
    trás separa as folhas (no grupo do nó, a roseta de poucas folhas largas lia como uma estrela só)."""
    corpo, nervura = materiais
    largura, pena = forma
    geo = {"type": "tapered_polyline", "points_q8": [qv(*p) for p in arco],
           "radii_q8": [max(RAIO_MINIMO, q(largura / 2 * k)) for k in LARGURA_NO_ARCO]}
    grupo, tags = c.grupo, tuple(PENA if pena else FOLHA_LISA)
    if not pena and largura >= COM_CONTORNO:
        grupo, tags = f"{c.grupo}_{pid}", tuple(t for t in FOLHA_LISA if t != "no_inner_outline")
    c.b.part(pid, corpo, geo, Parte(group=grupo, tags=tags))
    nid = f"{pid}_{'pena' if pena else 'nervura'}"
    eixo, adianta = _nervura(arco, largura)
    c.b.part(nid, nervura, polyline([qv(*p) for p in eixo], 1), Parte(group=grupo, tags=LINE))
    c.b.adianta(nid, adianta)


def _nervura(arco: list[Vec], largura: float) -> tuple[list[Vec], int]:
    """Os pontos da nervura e o quanto ela vem para a câmera no z-buffer (q8): corre no eixo da folha, da base até
    antes da ponta, e vem à frente do corpo roliço (o raio dele mais ``NERVURA``) sem sair do eixo na tela; erguida
    acima do corpo, ela corria na metade de cima da folha deitada."""
    return arco[:-1], q(largura / 2 + NERVURA)


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


def _outro_tom(a: dict[str, Any], tom: str, lado: float, vizinhas: set[str]) -> str:
    """O tom da folha lisa que as vizinhas na volta não têm (duas folhas chapadas do mesmo tom lado a lado viram uma
    mancha só): o dela, senão o do meio, senão o do lado da luz para onde ela abre (``lado``, de −1 a 1)."""
    do_lado, do_outro = (a["claro"], a["escuro"]) if lado > 0 else (a["escuro"], a["claro"])
    return str(next((t for t in (tom, a["material"], do_lado, do_outro) if t not in vizinhas), tom))


def _vao(cameras: list[float], n: int) -> tuple[float, float]:
    """O meio e o tamanho, em fatias, do maior vão entre as câmeras das vistas na volta de ``n`` fatias (a câmera da
    vista S cai na fatia 0, e o vão dela é a volta toda: a roseta gira em volta da meia fatia)."""
    fatias = sorted({round(cam * n / (2 * math.pi) % 1, 9) % 1 for cam in cameras})
    vaos = [((b - f) % 1 or 1.0, f) for f, b in zip(fatias, [*fatias[1:], fatias[0]], strict=True)]
    vao, comeco = max(vaos, key=lambda v: v[0])
    return comeco + vao / 2, vao


def _fora_das_cameras(az: float, cameras: list[float], folga: float) -> float:
    """O azimute da folha a ``folga`` (rad) ou mais da direção da câmera de cada vista: a que cai mais perto é
    empurrada para o lado dela (só quando o vão entre as câmeras não cabe a roseta inteira)."""
    for cam in cameras:
        d = (az - cam + math.pi) % (2 * math.pi) - math.pi
        if abs(d) < folga:
            az = cam + math.copysign(folga, d)
    return az


def _touceira(c: Ctx, a: dict[str, Any]) -> None:
    """``n`` lâminas em volta do pé, uma a cada fatia da volta: cada uma com o pé sorteado dentro do ``raio``, o
    comprimento na faixa, a abertura de 35 % a 100 % do pedido (a maioria perto dele) e o tom (o claro do lado da
    luz, o escuro do outro, com sorteio). O lado da luz é o da tela: em cada vista a lâmina toma o tom dela ali (o
    material da vista S, trocado nas outras), e a folha lisa não repete o da vizinha. Nenhuma folha larga aponta para
    a câmera de uma vista declarada. A roseta de folhas largas tem o miolo escuro no pé. Deixa a âncora ``pontas``
    (a ponta de cada lâmina)."""
    st, n = c.st, a["n"]
    larga = a["largura"] > 0
    giro = st.randint(0, 999) / 1000
    cameras = [math.radians(az / 1000) for az in c.vistas.values()]
    if larga:  # nenhuma folha larga aponta para a câmera de uma vista (viraria um talo em pé no meio da roseta)
        centro, vao = _vao(cameras, n)
        giro = centro + FRENTE_LIVRE * vao * (giro - 0.5)
    fecha = 1 - (ABRE_MENOS_A_LARGA if larga else ABRE_MENOS)
    pontas: list[Vec] = []
    vizinhas: list[dict[str, str]] = []  # os tons de cada folha lisa já feita, por vista
    for i in range(n):
        az = 2 * math.pi * (i + giro + st.randint(-30, 30) / 100 * (0.5 if larga else 1.0)) / n
        if larga:
            az = _fora_das_cameras(az, cameras, FOLGA * 2 * math.pi / n)
        longe = a["raio"] * st.randint(0, 100) / 100
        pe = (a["pe"][0] + math.sin(az) * longe, a["pe"][1] + math.cos(az) * longe, a["pe"][2])
        comprimento = a["altura"][0] + (a["altura"][1] - a["altura"][0]) * st.randint(0, 100) / 100
        abre = min(0.98, a["abre"] * (1 - fecha * (st.randint(0, 100) / 100) ** 2))
        arco = _arco(pe, az, comprimento, (abre, a["cai"], TRECHOS))
        sorteio = (1 - LADO_DA_LUZ) * st.randint(-100, 100) / 100
        pid = f"{c.pid}_{i:02d}"
        tons = {v: _material(a, LADO_DA_LUZ * _lado_da_luz(az, giro_da_vista) + sorteio, larga and a["pena"])
                for v, giro_da_vista in c.vistas.items()}
        if larga and not a["pena"]:  # a folha lisa não repete o tom das vizinhas na volta (a última fecha com a 1ª)
            junto = vizinhas[-1:] + (vizinhas[:1] if i == n - 1 else [])
            tons = {v: _outro_tom(a, t, _lado_da_luz(az, c.vistas[v]), {w[v] for w in junto}) for v, t in tons.items()}
            vizinhas.append(tons)
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


def _na_tela(p: Vec, azimute_mdeg: int) -> Tela:
    """O ponto na tela da vista, em px e sem o pivô: para a direita e para baixo (a altura sobe; a frente desce)."""
    a = math.radians(azimute_mdeg / 1000)
    return (p[0] * math.cos(a) - p[1] * math.sin(a),
            OLHAR[1] * (p[0] * math.sin(a) + p[1] * math.cos(a)) - OLHAR[0] * p[2])


def _livre(ponto: list[Tela], outros: list[list[Tela]], minimo: float) -> bool:
    """Se o ponto (na tela de cada vista) fica a ``minimo`` px ou mais de cada um dos outros, em toda vista."""
    return all(math.dist(p, o[j]) >= minimo for o in outros for j, p in enumerate(ponto))


def _nas_pontas(c: Ctx, pts: list[Vec], a: dict[str, Any]) -> list[int]:
    """Os pontos de uma âncora de pontas (da lâmina, do galho) que levam a cor: sorteados entre os mais altos na tela
    da vista que os mostra mais baixos (a ponta alta em toda vista fica no alto da figura), e livres: longe dos
    outros pontos de cor, os deste nó e os de antes (a flor de outro salpico nas mesmas pontas). Sem ponta alta
    livre, a mais alta das livres; sem nenhuma livre, o sorteio segue entre as altas."""
    azimutes = list(c.vistas.values())
    tela = [[_na_tela(p, az) for az in azimutes] for p in pts]
    ordem = sorted(range(len(pts)), key=lambda k: sum(v for _, v in tela[k]))
    altas = set(ordem[:max(a["n"], round(PONTAS_ALTAS * len(pts)))])
    pontos = [[_na_tela((x / 256, y / 256, z / 256), az) for az in azimutes]
              for x, y, z in (p["geometry"]["center_q8"] for p in c.b.parts
                              if p["geometry"]["type"] == "ellipse" and tuple(p["tags"]) == tuple(sorted(LINE)))]
    escolha = []
    for _ in range(min(a["n"], len(pts))):
        livres = [k for k in ordem if _livre(tela[k], pontos, 2 * a["raio"] + LONGE)]
        sorteio = [k for k in livres if k in altas] or livres[:1] or [k for k in ordem if k in altas]
        k = sorteio[c.st.randint(0, len(sorteio) - 1)]
        ordem.remove(k)
        pontos.append(tela[k])
        escolha.append(k)
    return escolha


def _ponto(c: Ctx, i: int, centro: Vec, a: dict[str, Any]) -> None:
    """O ponto de cor ``i`` do nó: redondo ou, com ``alonga``, em pé."""
    raios = qv(a["raio"], a["raio"], a["raio"] * a["alonga"])
    c.b.part(f"{c.pid}_{i:02d}", a["material"], ellipse(qv(*centro), raios), Parte(group=c.grupo, tags=LINE))


def _salpico(c: Ctx, a: dict[str, Any]) -> None:
    """Um ponto de cor em ``n`` dos pontos da âncora ``em``. Na face de um volume (``.superficie``), sorteados entre
    os que alguma vista vê de frente, no meio da figura (os ``n`` de menos beira, se não há tantos): o ponto da beira
    cai no contorno, e o do lado de lá, escondido; e o ponto entra na folhagem: a vista que vê a face de frente o
    mostra, e a que a vê de lado (onde ele cairia no contorno) o tem coberto pela folhagem. Nas pontas, os mais altos
    na tela e longe uns dos outros (``_nas_pontas``)."""
    pts = c.ancora(a["em"])
    if not a["em"].endswith(SUPERFICIE):
        for i, k in enumerate(_nas_pontas(c, pts, a)):
            _ponto(c, i, pts[k], a)
        return
    normais = _normais(pts) if pts else []
    beiras = _beiras(normais, list(c.vistas.values()))
    ordem = sorted(range(len(pts)), key=lambda k: beiras[k])
    escolha = [k for j, k in enumerate(ordem) if j < a["n"] or beiras[k] <= BEIRA]
    afunda = MERGULHO * (a["raio"] + VENCE)
    for i in range(min(a["n"], len(escolha))):
        k = escolha.pop(c.st.randint(0, len(escolha) - 1))
        _ponto(c, i, (pts[k][0] - normais[k][0] * afunda, pts[k][1] - normais[k][1] * afunda,
                      pts[k][2] - normais[k][2] * afunda), a)


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
         (_touceira, _lamina, _folha, _nervura, _arco, _lado_da_luz, _material, _outro_tom, _vao,
          _fora_das_cameras), vistas=QUATRO, flora="lamina", ancoras=("pontas",)),
    Peca("salpico", "Pontos de cor sobre outro nó: a flor e o fruto na superfície de uma copa, a espiga na ponta "
         "de uma lâmina, o broto na ponta de um galho. Pede a âncora de um nó de antes", (
             X("em", "ancora", "onde caem os pontos ('<nó>.superficie', '<nó>.pontas')"),
             X("material", "material", "a cor do ponto"), X("n", "inteiro", "quantos pontos", "8"),
             X("raio", "comprimento", "o raio do ponto (3 cm = 1 px)", "3cm"),
             X("alonga", "escalar", "a altura do ponto, em raios (1 = redondo; 3 = a espiga em pé)", "1")),
         _salpico, (("flores", {"em": "moita.superficie", "material": "olho_claro", "n": "9"}),
                    ("frutos", {"em": "moita.superficie", "material": "pano_vermelho", "n": "6", "raio": "5cm"}),
                    ("botões", {"em": "moita.superficie", "material": "ambar", "n": "14"})),
         "tests/test_ervas.py::test_o_salpico_cai_do_lado_da_camera",
         (_salpico, _normais, _beiras, _na_tela, _livre, _nas_pontas, _ponto), vistas=QUATRO, apoio=(MOITA,)),
]
