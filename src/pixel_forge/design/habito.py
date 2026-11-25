"""O hábito: a planta descrita pelos traços dela (``planta`` na composição), e não peça por peça. A engine deriva os
nós (o tronco, os galhos, a copa) por regras gerais da forma das plantas, as mesmas para qualquer espécie:

- **a esbeltez** (a altura sobre o diâmetro do pé): a árvore nova é esguia, a velha engrossa, a que se abre em
  galhos é mais atarracada que a de eixo único;
- **o fuste** (a parte da altura sem copa): onde a copa começa;
- **o hábito**: decurrente (o tronco se desfaz em galhos e a copa arredonda), excurrente (um eixo só até a ponta, e
  a copa afina no alto: de folha larga é a gota; de agulha, a conífera em andares), aberto (os galhos à mostra, com
  a folhagem nas pontas), pendente, guarda-sol, seco (sem folha), moita (sem tronco, em uma a três massas pela
  proporção dela) e touceira (lâminas a partir de um pé: finas ou, de folha larga, em pena);
- **o galho é mais fino que o eixo de onde sai** e nasce dele (a soma das seções dos galhos é a do tronco);
- **o lóbulo tem o tamanho da folhagem**, não o da copa: a copa pequena tem poucos lóbulos grandes;
- **o tronco entra na copa**: nada fica no ar.

Os nós derivados chamam-se ``tronco``, ``galhos`` (no aberto e no seco) e ``copa`` (a moita: ``copa``, ``copa_b``,
``copa_c``; a touceira: ``folhas``); os nós que a composição declara vêm depois e podem citar as âncoras deles
(``copa.superficie``, ``folhas.pontas``)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from ..contracts.composicao import Composicao, No, Planta
from ..core.recusa import Recusa
from .composicao import medidas
from .escala import PPM
from .expressao import valor


@dataclass(frozen=True)
class _Habito:
    """Os traços de um hábito: o fuste e a esbeltez de partida, o diâmetro do alto do tronco (em fração do pé), até
    onde o tronco entra na copa (em fração da altura dela), e o perfil e os ramos que caem da copa em massa."""

    fuste: float
    esbeltez: float
    topo: float
    entra: float
    perfil: float = 0.0
    pende: float = 0.0


HABITOS = {
    "decurrente": _Habito(0.38, 10, 0.6, 0.5), "excurrente": _Habito(0.22, 15, 0.3, 0.7, perfil=0.7),
    "aberto": _Habito(0.42, 12, 0.55, 0.65), "pendente": _Habito(0.45, 10, 0.6, 0.5, perfil=-0.5, pende=2.2),
    "guarda_sol": _Habito(0.55, 11, 0.6, 0.5, perfil=-1.0), "seco": _Habito(0.40, 11, 0.4, 0.37),
    # sem tronco: o fuste e a esbeltez não contam
    "moita": _Habito(0.05, 10, 1.0, 0.0), "touceira": _Habito(0.05, 10, 1.0, 0.0),
}
# a idade: quanto muda a esbeltez, a irregularidade da copa e, do tronco, a curva (em diâmetros), o pé, a
# irregularidade e as raízes (os nós da casca ficariam quase todos sob a copa: não se derivam)
IDADES = {"jovem": (1.35, 0.12, 0.25, 0.2, 0.08, 0), "adulta": (1.0, 0.2, 0.0, 0.35, 0.12, 0),
          "velha": (0.75, 0.24, 0.1, 0.5, 0.18, 3)}
FOLHAS = {"larga": ("copa_folhosa", "folhosa_funda"), "miuda": ("copa_folha", "folha_escura"),
          "agulha": ("copa_agulha", "agulha_escura")}
LOBULO_PX = 11.0  # a largura de um lóbulo na tela: a copa tem tantos quantos cabem na largura dela (de 5 a 12)
COBRE = 1.1  # o tamanho do lóbulo é isto sobre a raiz do número deles: juntos cobrem a copa, sem abrir o miolo
ANDAR_M = 0.55  # a altura de um andar da conífera (mais juntos, um sombreia o outro e a árvore escurece toda)
PONTA_M = 0.5  # uma ponta de saia a cada meio metro da volta
# o galho, em diâmetros do tronco na altura do galho mais alto: o mais fino, o mais grosso e a ponta (o tronco
# engrossa e afina até 18 %: o galho mais grosso fica abaixo disso)
GALHO = (0.5, 0.75, 0.25)
VENTO = (0.18, 0.05)  # com o vento em 1, o alto do tronco desvia 18 % da altura e a copa mais 5 % da largura
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
# a touceira: as lâminas finas pela largura na tela (de 7 a 18, uma a cada 1,6 px) e o comprimento da mais curta;
# a folha larga em pena: a largura dela em comprimentos e o arco que a ponta cai
LAMINAS = (1.6, 0.6)
FRONDE = (0.2, 0.5)
LAMINA, LAMINA_ESCURA = ("capim", "capim_claro", "capim_escuro"), ("agulha", "agulha_clara", "agulha_escura")
LIMITES = {"fuste": (0.05, 0.8), "esbeltez": (4.0, 40.0), "vento": (-1.0, 1.0)}


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
                     "de -1 (para a esquerda da tela) a 1.", f"/planta/{nome}")
    return v


def _medir(p: Planta, env: dict[str, float]) -> _Medidas:
    hab = HABITOS[p.habito]
    h, w = valor(p.altura, env, "/planta/altura"), valor(p.largura, env, "/planta/largura")
    if h <= 0 or w <= 0:
        raise Recusa("PLANTA", "A altura e a largura da planta são maiores que zero.",
                     "Escreva as medidas reais com a unidade (`4.5m`, `80cm`).", "/planta")
    esbeltez = _traco(p, "esbeltez", env, hab.esbeltez * IDADES[p.idade][0])
    return _Medidas(h, w, max(2.0, h / esbeltez), _traco(p, "fuste", env, hab.fuste) * h,
                    _traco(p, "vento", env, 0.0), hab, p)


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
    folha larga), com os lóbulos pela largura dela na tela."""
    material, miolo = FOLHAS[m.planta.folha]
    cz, alto = m.h - m.c, m.z0 + (m.h - m.z0) * m.habito.entra
    # a copa alta e estreita tem os lóbulos pela altura dela: pela largura sobrariam poucos, e o miolo apareceria
    tufos, tamanho = m.lobulos(max(m.w, m.h - m.z0), 3 if m.planta.habito == "excurrente" else 0)
    copa: dict[str, Any] = {"copa": [_px(m.w / 2), _px(m.c), _px(cz)], "tufos": tufos, "tamanho": tamanho,
                            "irregular": f"{m.idade[1]:g}", "material": material, "miolo": miolo}
    if m.habito.perfil:
        copa["perfil"] = f"{m.habito.perfil:g}"
    if m.habito.pende:
        copa["pende"] = f"{m.habito.pende:g}"
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
                material=FOLHAS[m.planta.folha][0])]


def _galhos(m: _Medidas, de: float, ate: float, copa: list[str], extra: dict[str, Any]) -> No:
    """Os galhos escalonados de ``de`` a ``ate`` de um tronco que acaba em ``alto``: mais finos que ele onde sai
    o mais alto."""
    alto = extra.pop("alto")
    n = {"jovem": 4, "adulta": 5, "velha": 6}[m.planta.idade]
    no_alto = m.d * (1 - (1 - m.habito.topo) * ate / alto)
    return _no("galhos", "galhos", "lenho", base=_px(de), sobe=_px(ate - de), copa=copa, n=str(n),
               largura=[_px(no_alto * GALHO[0]), _px(no_alto * GALHO[1])], ponta=_px(max(1.0, no_alto * GALHO[2])),
               material=m.planta.casca, **extra)


def _aberta(m: _Medidas) -> list[No]:
    """O hábito aberto: o tronco, os galhos escalonados à mostra e uma nuvem de folhas em cada ponta."""
    alto = m.z0 + (m.h - m.z0) * m.habito.entra
    copa = [_px(m.w / 2), _px((m.h - m.z0) * 0.35), _px((m.z0 + m.h) / 2)]
    galhos = _galhos(m, m.z0 * 0.85, alto * 0.95, copa, {
        "alto": alto, "alcance": "0.95", "ponta_v": ["-0.5", "0.5"],
        "bifurca": "0.3" if m.planta.idade == "velha" else "0"})
    return [_tronco(m, alto), galhos,
            _no("copa", "copa_aberta", "copa", pontas="galhos.pontas", raio=_px(m.w * NUVEM),
                achata="0.4" if m.planta.idade == "velha" else "0.5", irregular=f"{m.idade[1]:g}",
                material=FOLHAS[m.planta.folha][0])]


def _seca(m: _Medidas) -> list[No]:
    """A árvore sem folha: o tronco até pouco mais da metade e os galhos que sobem e bifurcam até o alto."""
    alto = 0.62 * m.h
    copa = [_px(m.w / 2), _px(0.22 * m.h), _px(0.78 * m.h)]
    return [_tronco(m, alto), _galhos(m, 0.42 * m.h, 0.6 * m.h, copa, {
        "alto": alto, "alcance": "0.85", "ponta_v": ["0", "0.9"], "bifurca": "1"})]


def _moita(m: _Medidas) -> list[No]:
    """A moita, sem tronco: uma massa ou, a mais larga, duas ou três encostadas e desencontradas (o mesmo grupo: uma
    luz só), cada uma assentada no chão."""
    material, miolo = FOLHAS[m.planta.folha]
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
    lâminas finas (em pé na touceira alta e estreita, abertas na baixa e larga)."""
    if m.planta.folha == "larga":
        longa = math.hypot(m.h, m.w / 2)
        n = {"jovem": 7, "adulta": 9, "velha": 11}[m.planta.idade]
        return [_no("folhas", "touceira", "folhas", altura=[_px(0.8 * longa), _px(longa)], n=str(n),
                    abre=f"{min(0.95, m.w / 2 / longa):.2f}", cai=f"{FRONDE[1]:g}",
                    largura=_px(max(3.0, longa * FRONDE[0])), pena=True, material="folha", claro="folha_clara",
                    escuro="folha_escura")]
    comum, claro, escuro = LAMINA_ESCURA if m.planta.folha == "agulha" else LAMINA
    return [_no("folhas", "touceira", "folhas", altura=[_px(LAMINAS[1] * m.h), _px(1.05 * m.h)],
                n=str(max(7, min(18, round(m.w / LAMINAS[0])))), abre=f"{min(0.9, m.w / 2 / m.h):.2f}",
                cai="0.05" if m.h >= 1.4 * m.w else "0.25", raio=_px(0.15 * m.w), material=comum, claro=claro,
                escuro=escuro)]


def nos_da_planta(p: Planta, env: dict[str, float]) -> list[No]:
    """Os nós que o hábito deriva dos traços da planta."""
    m = _medir(p, env)
    if p.habito == "moita":
        return _moita(m)
    if p.habito == "touceira":
        return _touceira(m)
    if p.habito == "seco":
        return _seca(m)
    if p.habito == "aberto":
        return _aberta(m)
    if p.habito == "excurrente" and p.folha == "agulha":
        return _conifera(m)
    return _massa(m)


def expandida(comp: Composicao) -> Composicao:
    """A composição com os nós da planta à frente dos que ela declara (sem ``planta``: é a que se monta)."""
    if comp.planta is None:
        return comp
    if comp.tipo != "prop":
        raise Recusa("PLANTA", f"Composição '{comp.id}': `planta` é do prop, não do {comp.tipo}.",
                     "A planta é um prop (`tipo: prop`).", "/planta")
    return comp.model_copy(update={"nos": [*nos_da_planta(comp.planta, medidas(comp)), *comp.nos], "planta": None})
