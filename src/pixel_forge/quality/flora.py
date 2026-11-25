"""A leitura da flora no sprite: o que se mede na folhagem e no lenho de um quadro, e os achados que as medidas
acusam. Cada medida responde a um defeito visto no jogo: a massa lisa (o ovo, o cone torneado), a copa espelhada, a
luz sem direção (cada tufo com a sua bola de luz: o brócolis), a árvore sem tronco à mostra, o pedaço solto e a
planta igual à irmã do cenário (a mesma silhueta em outro tamanho).

Tudo em máscaras e em luminância, na tela: mede-se o pixel que o jogo mostra, não a intenção da composição."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ..raster.grade import Mascara

Floats = npt.NDArray[np.float64]
LUZ = (-0.6, -0.8)  # de onde vem a luz na tela (esquerda e cima), unitário
PARTE_CLARA = 0.3  # a luz se mede entre os 30 % mais claros e os 30 % mais escuros da folhagem
LADO_DA_ASSINATURA = 32
MASSA_MINIMA = 200  # a folhagem menor que isto (px) é de lâminas ou de detalhe: não se mede como massa
# os limites dos achados (o controle de cada um está em tests/test_critica.py)
LISA = 0.985  # a folhagem enche tanto o fecho convexo dela: é um ovo ou um cone
ESPELHADA = 0.95  # a folhagem e o espelho dela coincidem tanto
# o claro fica a menos disto (em frações da copa) do escuro, para o lado da luz. Na conífera, em que cada saia
# sombreia a de baixo, a medida vai de 0,03 a 0,19; na folhagem chapada é zero
SEM_DIRECAO = 0.02
TRONCO_SUMIDO = 0.015  # o lenho à mostra é menos disto da figura
PARECIDA = 0.88  # a assinatura coincide tanto com a de uma irmã
IRMAS_NA_PRANCHA = 3


@dataclass(frozen=True)
class Leitura:
    """As medidas de um quadro: os pixels da folhagem, do lenho e da figura; a solidez (a folhagem sobre o fecho
    convexo dela), a simetria (a folhagem sobre o espelho dela), a luz (quanto o claro fica do lado da luz), as
    ilhas da figura e a assinatura (a silhueta na grade de 32, do pé para cima)."""

    folhagem_px: int
    lenho_px: int
    figura_px: int
    solidez: float
    simetria: float
    luz: float
    ilhas: int
    assinatura: Mascara

    def numeros(self) -> dict[str, Any]:
        return {"folhagem_px": self.folhagem_px, "lenho_px": self.lenho_px, "figura_px": self.figura_px,
                "solidez": round(self.solidez, 3), "simetria": round(self.simetria, 3), "luz": round(self.luz, 3),
                "ilhas": self.ilhas}


def _caixa(m: Mascara) -> Mascara:
    ys, xs = np.nonzero(m)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def _fecho(pontos: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """O fecho convexo (cadeia monótona)."""
    pts = sorted(set(pontos))

    def meia(seq: list[tuple[int, int]]) -> list[tuple[int, int]]:
        out: list[tuple[int, int]] = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out[:-1]

    return meia(pts) + meia(pts[::-1])


def solidez(m: Mascara) -> float:
    """Os pixels da máscara sobre os pixels do fecho convexo dela (os da grade dentro do fecho dos centros): 1 = sem
    reentrância nenhuma, em qualquer tamanho (o disco e o ovo dão 1)."""
    if not m.any():
        return 0.0
    pontas: list[tuple[int, int]] = []
    for linha in np.flatnonzero(m.any(axis=1)):
        xs = np.flatnonzero(m[linha])
        pontas += [(int(xs[0]), int(linha)), (int(xs[-1]), int(linha))]
    f = _fecho(pontas)
    if len(f) < 3:
        return 1.0
    dentro = 0
    for y in range(min(p[1] for p in f), max(p[1] for p in f) + 1):
        cortes = [a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) for a, b in zip(f, f[1:] + f[:1], strict=True)
                  if a[1] != b[1] and min(a[1], b[1]) <= y <= max(a[1], b[1])]
        cortes += [float(p[0]) for p in f if p[1] == y]
        dentro += math.floor(max(cortes) + 1e-9) - math.ceil(min(cortes) - 1e-9) + 1
    return float(m.sum()) / dentro


def simetria(m: Mascara) -> float:
    """O quanto a máscara coincide com o espelho dela (esquerda e direita), no melhor encaixe de até 2 px."""
    if not m.any():
        return 0.0
    c = np.pad(_caixa(m), ((0, 0), (2, 2)))
    melhor = 0.0
    for d in range(-2, 3):
        e = np.roll(c[:, ::-1], d, axis=1)
        melhor = max(melhor, float((c & e).sum()) / float((c | e).sum()))
    return melhor


def luz(luminancia: Floats, m: Mascara) -> float:
    """Quanto o centro dos pixels mais claros fica do lado da luz em relação ao dos mais escuros, em frações da
    caixa da máscara: perto de zero, a luz não tem direção (cada volume tem a dele, ou o tom é chapado)."""
    ys, xs = np.nonzero(m)
    if ys.size < 8:
        return 0.0
    v = luminancia[ys, xs]
    claro, escuro = v >= np.quantile(v, 1 - PARTE_CLARA), v <= np.quantile(v, PARTE_CLARA)
    if claro.all() or escuro.all():
        return 0.0
    w, h = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
    dx = (xs[claro].mean() - xs[escuro].mean()) / w
    dy = (ys[claro].mean() - ys[escuro].mean()) / h
    return float(dx * LUZ[0] + dy * LUZ[1])


def ilhas(m: Mascara) -> int:
    """Os pedaços da máscara (vizinhança de 8)."""
    falta = m.copy()
    n = 0
    while falta.any():
        y, x = (int(v) for v in np.argwhere(falta)[0])
        pilha = [(y, x)]
        falta[y, x] = False
        n += 1
        while pilha:
            a, b = pilha.pop()
            y0, x0 = max(0, a - 1), max(0, b - 1)
            viz = np.argwhere(falta[y0:a + 2, x0:b + 2])
            for c, d in viz:
                falta[y0 + c, x0 + d] = False
                pilha.append((y0 + int(c), x0 + int(d)))
    return n


def assinatura(m: Mascara) -> Mascara:
    """A silhueta na grade de 32: a caixa da máscara reduzida pelo lado maior (a proporção fica) e assentada
    embaixo, no meio. Duas plantas de tamanhos diferentes e a mesma forma dão a mesma assinatura."""
    out = np.zeros((LADO_DA_ASSINATURA, LADO_DA_ASSINATURA), dtype=bool)
    if not m.any():
        return out
    c = _caixa(m)
    h, w = c.shape
    k = LADO_DA_ASSINATURA / max(h, w)
    nh, nw = max(1, round(h * k)), max(1, round(w * k))
    ys = np.minimum(h - 1, ((np.arange(nh) + 0.5) / k).astype(int))
    xs = np.minimum(w - 1, ((np.arange(nw) + 0.5) / k).astype(int))
    x0 = (LADO_DA_ASSINATURA - nw) // 2
    out[LADO_DA_ASSINATURA - nh:, x0:x0 + nw] = c[np.ix_(ys, xs)]
    return out


def semelhanca(a: Mascara, b: Mascara) -> float:
    """O quanto duas assinaturas coincidem (a interseção sobre a união)."""
    uniao = float((a | b).sum())
    return float((a & b).sum()) / uniao if uniao else 0.0


def ler(folhagem: Mascara, lenho: Mascara, figura: Mascara, luminancia: Floats) -> Leitura:
    return Leitura(int(folhagem.sum()), int(lenho.sum()), int(figura.sum()), solidez(folhagem), simetria(folhagem),
                   luz(luminancia, folhagem), ilhas(figura), assinatura(figura))


def _achado(codigo: str, gravidade: str, medida: str, dica: str) -> dict[str, str]:
    return {"codigo": codigo, "gravidade": gravidade, "medida": medida, "dica": dica}


def achados(m: Leitura, arvore: bool, irmas: dict[str, float]) -> list[dict[str, str]]:
    """O que as medidas acusam. ``defeito`` impede a crítica de passar; ``aviso`` pede o olho de quem revisa.
    ``arvore``: o porte pede o tronco à mostra; ``irmas``: a semelhança com cada outra planta do acervo."""
    out = []
    massa = m.folhagem_px >= MASSA_MINIMA
    if massa and m.solidez >= LISA:
        out.append(_achado("FOLHAGEM_LISA", "defeito", f"a folhagem enche {m.solidez:.0%} do fecho convexo dela "
                           f"(o limite é {LISA:.0%})", "A silhueta não tem reentrância: lê como ovo, bola ou cone. "
                           "Na `copa`, diminua o `tamanho` dos lóbulos e suba o `irregular` (mais lóbulos grandes "
                           "alisam); ou troque a construção (a copa aberta, a saia recortada). A planta não se faz "
                           "de elipsoide nem de polígono."))
    if massa and m.simetria >= ESPELHADA:
        out.append(_achado("FOLHAGEM_ESPELHADA", "defeito", f"a folhagem coincide {m.simetria:.0%} com o espelho "
                           f"dela (o limite é {ESPELHADA:.0%})", "Planta nenhuma é simétrica: suba o `irregular`, "
                           "troque a semente, ou incline o tronco."))
    if massa and m.luz < SEM_DIRECAO:
        out.append(_achado("LUZ_SEM_DIRECAO", "defeito", f"o claro fica a {m.luz:.2f} da copa do lado da luz (o "
                           f"mínimo é {SEM_DIRECAO})", "A folhagem não lê como uma massa com um lado claro: cada "
                           "volume tem a luz dele, ou o tom é chapado. Use a peça de copa (a luz é da massa), não "
                           "elipsoides soltos."))
    if arvore and m.lenho_px < TRONCO_SUMIDO * m.figura_px:
        out.append(_achado("TRONCO_SUMIDO", "aviso", f"o lenho à mostra é {m.lenho_px} px de {m.figura_px} da figura",
                           "A árvore lê como moita no chão. Suba a copa ou diminua o fundo dela; se a espécie tem a "
                           "saia até o chão, diga na ficha."))
    if m.ilhas > 1:
        out.append(_achado("PEDACO_SOLTO", "aviso", f"a figura tem {m.ilhas} pedaços", "Um pedaço não toca o "
                           "resto: confira se é um detalhe querido (a lâmina, a flor) ou uma parte fora do lugar."))
    for irma, s in sorted(irmas.items(), key=lambda kv: -kv[1]):
        if s >= PARECIDA:
            out.append(_achado("PARECIDA_COM_A_IRMA", "defeito", f"a silhueta coincide {s:.0%} com a de '{irma}' (o "
                               f"limite é {PARECIDA:.0%})", "É a mesma planta em outro tamanho ou cor. Mude a "
                               "construção (outra peça de copa, outro perfil, os galhos à mostra, o tronco curvo "
                               "ou bifurcado, o porte), não só a semente ou as medidas."))
    return out
