"""O hábito: a planta descrita pelos traços dela (``planta`` na composição), e não peça por peça. A engine deriva os
nós (o tronco, os galhos, a copa) por regras gerais da forma das plantas, as mesmas para qualquer espécie:

- **a esbeltez** (a altura sobre o diâmetro do pé): a árvore nova é esguia, a velha engrossa, a que se abre em
  galhos é mais atarracada que a de eixo único;
- **o fuste** (a parte da altura sem copa): onde a copa começa;
- **o hábito**: decurrente (o tronco se desfaz em galhos e a copa arredonda), excurrente (um eixo só até a ponta, e
  a copa afina no alto: de folha larga é a gota; de agulha, a conífera em andares), aberto (os galhos à mostra, com
  a folhagem nas pontas; ao vento, em bandeira), pendente (a cúpula de lóbulos miúdos e a cortina densa de ramos
  que desce pelo fuste até perto do chão), guarda-sol, seco (sem folha), moita (sem tronco, em uma a três massas
  pela proporção dela) e touceira (lâminas a partir de um pé: finas e quase em pé, ou, de folha larga, em pena);
- **o galho é mais fino que o eixo de onde sai** e nasce dele (a soma das seções dos galhos é a do tronco);
- **o lóbulo tem o tamanho da folhagem**, não o da copa: a copa pequena tem poucos lóbulos grandes;
- **o tronco entra na copa**: nada fica no ar;
- **a altura é a pedida**: onde o alto sai de uma ponta sorteada na peça, a engine mede o que derivou e acerta.

Os nós derivados chamam-se ``tronco``, ``galhos`` (no aberto e no seco) e ``copa`` (a moita: ``copa``, ``copa_b``,
``copa_c``; o aberto ao vento: ``galhos_b`` e ``copa_b``; a touceira: ``folhas``); os nós que a composição declara
vêm depois e podem citar as âncoras deles (``copa.superficie``, ``folhas.pontas``)."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from ..contracts.composicao import Composicao, No, Planta, Vista
from ..core.recusa import Recusa
from .composicao import medidas
from .escala import PPM
from .expressao import valor
from .porte import topo
from .prop import ir_do_prop
from .vistas import no_mundo


@dataclass(frozen=True)
class _Habito:
    """Os traços de um hábito: o fuste e a esbeltez de partida, o diâmetro do alto do tronco (em fração do pé), até
    onde o tronco entra na copa (em fração da altura dela), e, da copa em massa, o perfil, a cortina de ramos que
    caem (a parte do fuste que ela cobre) e os lóbulos a mais (cada lóbulo de baixo dá os ramos dele)."""

    fuste: float
    esbeltez: float
    topo: float
    entra: float
    perfil: float = 0.0
    cortina: float = 0.0
    mais: int = 0


HABITOS = {
    "decurrente": _Habito(0.38, 10, 0.6, 0.5), "excurrente": _Habito(0.22, 15, 0.3, 0.7, perfil=0.7, mais=3),
    "aberto": _Habito(0.42, 12, 0.55, 0.65),
    "pendente": _Habito(0.45, 10, 0.6, 0.5, perfil=-0.6, cortina=0.75, mais=8),
    "guarda_sol": _Habito(0.55, 11, 0.6, 0.5, perfil=-1.0), "seco": _Habito(0.40, 11, 0.4, 0.37),
    # sem tronco: o fuste e a esbeltez não contam
    "moita": _Habito(0.05, 10, 1.0, 0.0), "touceira": _Habito(0.05, 10, 1.0, 0.0),
}
# a idade: quanto muda a esbeltez, a irregularidade da copa e, do tronco, a curva (em diâmetros), o pé, a
# irregularidade e as raízes (os nós da casca ficariam quase todos sob a copa: não se derivam)
IDADES = {"jovem": (1.35, 0.12, 0.25, 0.2, 0.08, 0), "adulta": (1.0, 0.2, 0.0, 0.35, 0.12, 0),
          "velha": (0.75, 0.24, 0.1, 0.5, 0.18, 3)}
FOLHAS = {"larga": ("copa_folhosa", "folhosa_funda"), "miuda": ("copa_folha", "folha_escura"),
          "agulha": ("copa_agulha", "agulha_escura"), "cinzenta": ("copa_cinzenta", "cinza_verde_fundo")}
LOBULO_PX = 11.0  # a largura de um lóbulo na tela: a copa tem tantos quantos cabem na largura dela (de 5 a 12)
COBRE = 1.1  # o tamanho do lóbulo é isto sobre a raiz do número deles: juntos cobrem a copa, sem abrir o miolo
ANDAR_M = 0.55  # a altura de um andar da conífera (mais juntos, um sombreia o outro e a árvore escurece toda)
PONTA_M = 0.5  # uma ponta de saia a cada meio metro da volta
# o galho, em diâmetros do tronco na altura do galho mais alto: o mais fino, o mais grosso e a ponta (o tronco
# engrossa e afina até 18 %: o galho mais grosso fica abaixo disso)
GALHO = (0.5, 0.75, 0.25)
GALHOS = {"jovem": 4, "adulta": 5, "velha": 6}  # os galhos pela idade
VENTO = (0.18, 0.05)  # com o vento em 1, o alto do tronco desvia 18 % da altura e a copa mais 5 % da largura
# a cortina: o ramo mais curto desce até 0,45 do que pede o ``pende`` da copa (``ramos`` em ``kit/pecas_copa.py``);
# os outros descem mais e param perto do chão, a alturas desiguais
RAMO_MAIS_CURTO = 0.45
# até onde descem os lóbulos da copa em massa, em meias alturas abaixo do centro dela (eles recuam da borda): com
# o perfil negativo ficam só na metade de cima. A copa derivada desce o elipsoide até o fundo deles cair no fuste
FUNDO_DA_MASSA = 0.74
# a moita de 1, 2 e 3 massas: de cada uma, a meia largura e o desvio (em meias larguras da moita), o avanço para a
# frente e a altura (em alturas da moita), os lóbulos e o tamanho deles. As massas se sobrepõem: é uma moita só
MOITAS = {1: ((1.0, 0.0, 0.0, 1.0, 6, 0.45),),
          2: ((0.66, -0.3, 0.0, 1.0, 6, 0.46), (0.52, 0.42, 0.08, 0.72, 6, 0.46)),
          3: ((0.6, -0.4, 0.0, 1.0, 6, 0.46), (0.46, 0.46, -0.08, 0.76, 6, 0.46), (0.38, 0.06, 0.12, 0.6, 5, 0.5))}
MOITA_DE_DUAS, MOITA_DE_TRES = 1.6, 2.6  # a largura sobre a altura a partir da qual a moita tem duas e três massas
NUVEM = 0.15  # a meia largura da nuvem de folhas do hábito aberto, em larguras da copa
# o vento no hábito aberto, com o vento em 1: os galhos em volta alcançam 50 % menos (o lado do vento fica curto) e
# um galho a mais, bifurcado, sai para o lado de lá, 40 % mais longe e mais baixo (a copa em bandeira)
BANDEIRA = (0.5, 0.4)
# a touceira: as lâminas finas pela largura na tela (de 7 a 18, uma a cada 1,6 px) e o comprimento da mais curta;
# a folha larga em pena: a largura dela em comprimentos e o arco que a ponta cai
LAMINAS = (1.6, 0.6)
PE_DA_TOUCEIRA = 0.3  # o raio do pé das lâminas finas, em larguras da touceira: cada lâmina no seu pé
ABRE_DA_TOUCEIRA = 0.43  # o alcance das pontas que leva a touceira até a largura pedida (o pé e a abertura o somam)
# a lâmina fina abre no máximo isto e cai no máximo isto: a flor (o ``salpico`` nas pontas) pede a lâmina quase em
# pé e reta; a largura que a abertura não dá vem do pé, mais largo
LAMINA_EM_PE = (0.35, 0.08)
FRONDE = (0.2, 0.5)
# a lâmina fina pela folha: o material, o do lado da luz e o do lado de lá (a miúda é a do capim)
LAMINAS_DA_FOLHA = {"miuda": ("capim", "capim_claro", "capim_escuro"),
                    "agulha": ("agulha", "agulha_clara", "agulha_escura"),
                    "cinzenta": ("cinza_verde", "cinza_verde_claro", "cinza_verde_escuro")}
LIMITES = {"fuste": (0.05, 0.8), "esbeltez": (4.0, 40.0), "vento": (-1.0, 1.0), "cortina": (0.0, 1.0)}


def _px(v: float) -> str:
    return f"{v:.1f}px"


def _no(ident: str, peca: str, grupo: str, **args: Any) -> No:
    return No(id=ident, peca=peca, grupo=grupo, args=args)


@dataclass(frozen=True)
class _Medidas:
    """A planta medida (px): a altura, a largura, o diâmetro do pé, a base e a meia altura da copa, e os traços."""

    h: float
    w: float
    d: float
    z0: float
    vento: float
    cortina: float
    habito: _Habito
    planta: Planta

    @property
    def c(self) -> float:
        """A meia altura do elipsoide da copa em massa: o alto dele na altura da planta e o fundo dos lóbulos (que
        recuam da borda) no fuste."""
        return (self.h - self.z0) / (1 + FUNDO_DA_MASSA + 0.5 * min(0.0, self.habito.perfil))

    @property
    def idade(self) -> tuple[float, float, float, float, float, int]:
        return IDADES[self.planta.idade]

    @property
    def folha(self) -> str:
        """A folha dita ou a do hábito: a larga; na touceira, a lâmina fina."""
        return self.planta.folha or ("miuda" if self.planta.habito == "touceira" else "larga")

    def lobulos(self, largura: float, mais: int = 0) -> tuple[str, str]:
        """Os lóbulos de uma massa com a ``largura`` (px) na tela e o tamanho de cada um."""
        n = max(5, min(12, round(largura / LOBULO_PX))) + mais
        return str(n), f"{max(0.26, min(0.48, COBRE / math.sqrt(n))):.2f}"


def _traco(p: Planta, nome: str, env: dict[str, float], padrao: float) -> float:
    """O traço que a composição diz ou o do hábito, dentro da faixa dele."""
    texto = getattr(p, nome)
    v = padrao if texto is None else valor(texto, env, f"/planta/{nome}")
    lo, hi = LIMITES[nome]
    if not lo <= v <= hi:
        raise Recusa("PLANTA", f"O traço '{nome}' da planta vale {v:g}; vai de {lo:g} a {hi:g}.",
                     "O fuste é a parte da altura sem copa; a esbeltez, a altura sobre o diâmetro do pé; o vento, "
                     "de -1 (para a esquerda da tela) a 1; a cortina, a parte do fuste que os ramos que caem cobrem "
                     "(0 = nenhum ramo; 1 = até o chão).", f"/planta/{nome}")
    return v


def _medir(p: Planta, env: dict[str, float]) -> _Medidas:
    hab = HABITOS[p.habito]
    h, w = valor(p.altura, env, "/planta/altura"), valor(p.largura, env, "/planta/largura")
    if h <= 0 or w <= 0:
        raise Recusa("PLANTA", "A altura e a largura da planta são maiores que zero.",
                     "Escreva as medidas reais com a unidade (`4.5m`, `80cm`).", "/planta")
    esbeltez = _traco(p, "esbeltez", env, hab.esbeltez * IDADES[p.idade][0])
    return _Medidas(h, w, max(2.0, h / esbeltez), _traco(p, "fuste", env, hab.fuste) * h,
                    _traco(p, "vento", env, 0.0), _traco(p, "cortina", env, hab.cortina), hab, p)


def _tronco(m: _Medidas, altura: float, inclina: bool = True) -> No:
    """O tronco até ``altura``: a grossura pela esbeltez, o afinamento pelo hábito e o resto pela idade."""
    _, _, curva, pe, irregular, raizes = m.idade
    args: dict[str, Any] = {"altura": _px(altura), "base": _px(m.d), "topo": _px(max(1.0, m.d * m.habito.topo)),
                            "casca": m.planta.casca, "pe": f"{pe:g}", "irregular": f"{irregular:g}"}
    if curva:
        args["curva"] = _px(curva * m.d)
    if raizes:
        args["raizes"] = str(raizes + (2 if m.d >= 0.6 * PPM else 0))
    if inclina and m.vento:
        args["inclinacao"] = _px(m.vento * VENTO[0] * m.h)
    return _no("tronco", "tronco_em_pe", "lenho", **args)


def _massa(m: _Medidas) -> list[No]:
    """O tronco até dentro da copa e a copa em massa (o decurrente, o pendente, o guarda-sol e o excurrente de
    folha larga), com os lóbulos pela largura dela na tela. Com a cortina, os ramos que caem descem pelo fuste: o
    mais curto cobre a parte pedida dele, e os outros param perto do chão."""
    material, miolo = FOLHAS[m.folha]
    cz, alto = m.h - m.c, m.z0 + (m.h - m.z0) * m.habito.entra
    # a copa alta e estreita tem os lóbulos pela altura dela: pela largura sobrariam poucos, e o miolo apareceria
    tufos, tamanho = m.lobulos(max(m.w, m.h - m.z0), m.habito.mais)
    copa: dict[str, Any] = {"copa": [_px(m.w / 2), _px(m.c), _px(cz)], "tufos": tufos, "tamanho": tamanho,
                            "irregular": f"{m.idade[1]:g}", "material": material, "miolo": miolo}
    if m.habito.perfil:
        copa["perfil"] = f"{m.habito.perfil:g}"
    if m.cortina:
        copa["pende"] = f"{(cz - m.z0 * (1 - m.cortina)) / (RAMO_MAIS_CURTO * m.c):.2f}"
    if m.vento:  # a copa segue o alto do tronco e ainda cede ao vento
        copa["desvio"] = [_px(m.vento * (VENTO[0] * m.h * min(1.0, cz / alto) ** 2 + VENTO[1] * m.w)), "0"]
    return [_tronco(m, alto), _no("copa", "copa", "copa", **copa)]


def _conifera(m: _Medidas) -> list[No]:
    """O excurrente de agulha: o tronco a prumo até o meio da copa e os andares em saia."""
    andares = max(4, min(10, round((m.h - m.z0) / (ANDAR_M * PPM))))
    pontas = max(6, min(11, round(math.pi * m.w / (PONTA_M * PPM))))
    return [_tronco(m, (m.z0 + m.h) / 2, inclina=False),
            _no("copa", "copa_conica", "copa", base=_px(m.z0), altura=_px(m.h), raio=_px(m.w / 2),
                andares=str(andares), pontas=str(pontas), irregular=f"{m.idade[1] * 0.6:g}",
                material=FOLHAS[m.folha][0])]


def _galhos(m: _Medidas, de: float, ate: float, copa: list[str], extra: dict[str, Any]) -> No:
    """Os galhos escalonados de ``de`` a ``ate`` de um tronco que acaba em ``alto``: mais finos que ele onde sai
    o mais alto; ``n`` pela idade e o id ``galhos``, se não vierem."""
    alto, ident = extra.pop("alto"), extra.pop("id", "galhos")
    n = extra.pop("n", GALHOS[m.planta.idade])
    no_alto = m.d * (1 - (1 - m.habito.topo) * ate / alto)
    return _no(ident, "galhos", "lenho", base=_px(de), sobe=_px(ate - de), copa=copa, n=str(n),
               largura=[_px(no_alto * GALHO[0]), _px(no_alto * GALHO[1])], ponta=_px(max(1.0, no_alto * GALHO[2])),
               material=m.planta.casca, **extra)


def _bandeira(m: _Medidas, alto: float, copa: list[str]) -> tuple[float, list[No]]:
    """Com o vento, a copa aberta vai em bandeira: quanto os galhos em volta alcançam (o lado do vento fica curto)
    e o galho a mais, bifurcado, que sai para o lado de lá, mais longe e mais baixo (``galhos_b``). Um galho só
    (``n`` 1) cai na fatia da ``fase``: a direita da tela é 0,25 da volta."""
    forca = abs(m.vento)
    if not forca:
        return 1.0, []
    return 1 - BANDEIRA[0] * forca, [_galhos(m, alto * 0.8, alto * 0.8, copa, {
        "alto": alto, "n": 1, "fase": "0.25" if m.vento > 0 else "0.75",
        "alcance": f"{0.95 * (1 + BANDEIRA[1] * forca):.2f}", "ponta_v": ["-0.6", "-0.2"], "bifurca": "1",
        "id": "galhos_b"})]


def _aberta(m: _Medidas) -> list[No]:
    """O hábito aberto: o tronco, os galhos escalonados à mostra e uma nuvem de folhas em cada ponta (com o vento,
    também nas do galho a sotavento: ``copa_b``)."""
    alto = m.z0 + (m.h - m.z0) * m.habito.entra
    copa = [_px(m.w / 2), _px((m.h - m.z0) * 0.35), _px((m.z0 + m.h) / 2)]
    alcance, sotavento = _bandeira(m, alto, copa)
    galhos = [_galhos(m, m.z0 * 0.85, alto * 0.95, copa, {
        "alto": alto, "n": GALHOS[m.planta.idade] - len(sotavento),
        "alcance": f"{0.95 * alcance:.2f}", "ponta_v": ["-0.5", "0.5"],
        "bifurca": "0.3" if m.planta.idade == "velha" else "0"}), *sotavento]
    nuvem = {"raio": _px(m.w * NUVEM), "achata": "0.4" if m.planta.idade == "velha" else "0.5",
             "irregular": f"{m.idade[1]:g}", "material": FOLHAS[m.folha][0]}
    return [_tronco(m, alto), *galhos, *(_no(g.id.replace("galhos", "copa"), "copa_aberta", "copa",
                                             pontas=f"{g.id}.pontas", **nuvem) for g in galhos)]


def _seca(m: _Medidas) -> list[No]:
    """A árvore sem folha: o tronco até pouco mais da metade e os galhos que sobem e bifurcam até o alto."""
    alto = 0.62 * m.h
    copa = [_px(m.w / 2), _px(0.22 * m.h), _px(0.78 * m.h)]
    return [_tronco(m, alto), _galhos(m, 0.42 * m.h, 0.6 * m.h, copa, {
        "alto": alto, "alcance": "0.85", "ponta_v": ["0", "0.9"], "bifurca": "1"})]


def _moita(m: _Medidas) -> list[No]:
    """A moita, sem tronco: uma massa ou, a mais larga, duas ou três encostadas e desencontradas (o mesmo grupo: uma
    luz só), cada uma assentada no chão."""
    material, miolo = FOLHAS[m.folha]
    massas = MOITAS[1 if m.w < MOITA_DE_DUAS * m.h else 2 if m.w < MOITA_DE_TRES * m.h else 3]
    nos = []
    for ident, (largo, lado, frente, alta, tufos, tamanho) in zip(("copa", "copa_b", "copa_c"), massas, strict=False):
        meia = m.h * alta / 2
        nos.append(_no(ident, "copa", "copa", copa=[_px(m.w / 2 * largo), _px(meia), _px(meia)],
                       desvio=[_px(m.w / 2 * lado), _px(m.w / 2 * frente)], tufos=str(tufos), tamanho=f"{tamanho:g}",
                       irregular=f"{m.idade[1]:g}", material=material, miolo=miolo))
    return nos


def _touceira(m: _Medidas) -> list[No]:
    """A touceira: de folha larga, a roseta de folhas em pena que abrem em arco até a largura dela; senão, as
    lâminas finas, cada uma no seu pé (espalhadas pela largura da touceira: o capim não nasce de um ponto só, e as
    lâminas ficam separadas), quase em pé e quase retas, de ponta para cima (a flor nas pontas se lê): na touceira
    baixa e larga, o pé leva as lâminas até a largura que a abertura não dá."""
    if m.folha == "larga":
        longa = math.hypot(m.h, m.w / 2)
        n = {"jovem": 7, "adulta": 9, "velha": 11}[m.planta.idade]
        return [_no("folhas", "touceira", "folhas", altura=[_px(0.8 * longa), _px(longa)], n=str(n),
                    abre=f"{min(0.95, m.w / 2 / longa):.2f}", cai=f"{FRONDE[1]:g}",
                    largura=_px(max(3.0, longa * FRONDE[0])), pena=True, material="folha", claro="folha_clara",
                    escuro="folha_escura")]
    comum, claro, escuro = LAMINAS_DA_FOLHA[m.folha]
    alcance = ABRE_DA_TOUCEIRA * m.w
    abre = min(LAMINA_EM_PE[0], alcance / m.h)
    return [_no("folhas", "touceira", "folhas", altura=[_px(LAMINAS[1] * m.h), _px(m.h)],
                n=str(max(7, min(18, round(m.w / LAMINAS[0])))), abre=f"{abre:.2f}",
                cai="0.05" if m.h >= 1.4 * m.w else f"{LAMINA_EM_PE[1]:g}",
                raio=_px(PE_DA_TOUCEIRA * m.w + alcance - abre * m.h), material=comum, claro=claro, escuro=escuro)]


def _construcao(p: Planta) -> Callable[[_Medidas], list[No]]:
    """A construção do hábito: a conífera é o excurrente de agulha, e a copa em massa, o resto das árvores."""
    if p.habito in CONSTRUCOES:
        return CONSTRUCOES[p.habito]
    return _conifera if p.habito == "excurrente" and p.folha == "agulha" else _massa


CONSTRUCOES = {"moita": _moita, "touceira": _touceira, "seco": _seca, "aberto": _aberta}


def _alto(comp: Composicao, nos: list[No]) -> float:
    """O ponto mais alto (px) dos nós derivados, montados sozinhos, fora o tronco (ele não sobe com as pontas, e o
    alto dele fica abaixo delas)."""
    prova = comp.model_copy(update={"nos": nos, "planta": None, "landmarks": {},
                                    "vistas": {v: Vista() for v in comp.vistas}})
    d = ir_do_prop(prova)
    return max(topo(p["geometry"]) for p in no_mundo(d["parts"], d["bones"]) if not p["id"].startswith("tronco"))


def _assentada(comp: Composicao, m: _Medidas, nos: list[No]) -> list[No]:
    """Os nós com o alto na altura pedida. Onde o alto é o da ponta mais alta sorteada na peça (a nuvem do galho
    mais alto, a ponta do galho seco, a lâmina mais alta), a engine mede o que derivou e acerta: os galhos sobem
    ou descem as pontas (a nuvem e a bifurcação vão com elas), e as lâminas crescem ou encolhem (a altura delas é
    proporcional ao comprimento). Nos outros hábitos o alto já é o pedido (o raminho do alto encosta na copa)."""
    if _construcao(m.planta) not in (_aberta, _seca, _touceira):
        return nos
    alto = _alto(comp, nos)
    out = []
    for no in nos:
        args = dict(no.args)
        if no.peca == "galhos":
            meia_l, meia_a, cz = cast(list[str], args["copa"])
            args["copa"] = [meia_l, meia_a, _px(_valor_px(cz) + m.h - alto)]
        elif no.peca == "touceira":
            args["altura"] = [_px(_valor_px(v) * m.h / alto) for v in cast(list[str], args["altura"])]
        out.append(no.model_copy(update={"args": args}))
    return out


def _valor_px(v: str) -> float:
    return float(v.removesuffix("px"))


def nos_da_planta(comp: Composicao, p: Planta) -> list[No]:
    """Os nós que o hábito deriva dos traços da planta, com o alto na altura pedida."""
    m = _medir(p, medidas(comp))
    construcao = _construcao(p)
    if p.cortina is not None and construcao is not _massa:
        raise Recusa("PLANTA", f"A cortina é da copa em massa, e o hábito '{p.habito}' não tem.",
                     "Os ramos que caem vêm da copa fechada (`pendente`, `decurrente`, `guarda_sol`, `excurrente` "
                     "de folha larga): apague `cortina` ou troque o hábito.", "/planta/cortina")
    return _assentada(comp, m, construcao(m))


def expandida(comp: Composicao) -> Composicao:
    """A composição com os nós da planta à frente dos que ela declara (sem ``planta``: é a que se monta)."""
    if comp.planta is None:
        return comp
    if comp.tipo != "prop":
        raise Recusa("PLANTA", f"Composição '{comp.id}': `planta` é do prop, não do {comp.tipo}.",
                     "A planta é um prop (`tipo: prop`).", "/planta")
    return comp.model_copy(update={"nos": [*nos_da_planta(comp, comp.planta), *comp.nos], "planta": None})
