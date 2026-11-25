"""As medidas do corpo humano tiradas do próprio modelo: a máscara inteira de cada parte (sem a oclusão), de frente e
de perfil, na elevação da radiografia. Cada medida vem com a faixa de um corpo real (o cânone de desenho e a
antropometria, com folga): fora dela, a forma lê errada antes de qualquer pixel, e não há roupa nem pose que a conserte.

As partes são as do ``corpo_humano`` do kit (o crânio, a face, o queixo, o nariz, o pescoço, o peito, a cintura, o
quadril, a linha e as esferas dos ombros, as esferas do quadril e dos tornozelos) e, quando a composição as tem, as
dos olhos e do cabelo preso.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np

from ..raster.grade import Mascara

Mascaras = Mapping[str, Mascara]
CABECA = ("skull", "jaw", "chin", "nose")  # com o nariz, quando o corpo o tem
TRONCO = ("chest", "waist", "neck", "trap_l", "trap_r")  # com a linha do ombro, quando o corpo a tem


@dataclass(frozen=True)
class Medida:
    id: str
    valor: float
    faixa: tuple[float, float]
    leitura: str

    def dado(self) -> dict[str, Any]:
        valor = round(float(self.valor), 3)
        return {"medida": self.id, "valor": valor, "faixa": list(self.faixa),
                "ok": self.faixa[0] <= valor <= self.faixa[1], "leitura": self.leitura}


def _uniao(ms: Mascaras, *nomes: str) -> Mascara:
    """A união das partes de ``nomes`` que o corpo tem."""
    out: Mascara = np.logical_or.reduce([ms[n] for n in nomes if n in ms])
    return out


def _fileiras(m: Mascara) -> tuple[int, int]:
    ys = np.nonzero(m.any(axis=1))[0]
    return int(ys.min()), int(ys.max())


def _colunas(m: Mascara, y: int) -> tuple[int, int]:
    xs = np.nonzero(m[y])[0]
    return (int(xs.min()), int(xs.max())) if len(xs) else (0, -1)


def _largura(m: Mascara, y: int) -> int:
    a, b = _colunas(m, y)
    return b - a + 1


@dataclass(frozen=True)
class _Corpo:
    """O corpo de frente: as máscaras, as fileiras do alto da cabeça e do queixo e a estatura em px."""

    ms: Mascaras
    topo: int
    queixo: int
    estatura: int

    @property
    def cabeca(self) -> int:
        return self.queixo - self.topo + 1

    def na_cabeca(self, y: float) -> float:
        """A altura da fileira na cabeça: 0 no queixo, 1 no alto."""
        return (self.queixo - y) / self.cabeca


def _rosto(c: _Corpo) -> list[Medida]:
    cab = _uniao(c.ms, *CABECA)
    larguras = [_largura(cab, y) for y in range(c.topo, c.queixo + 1)]
    faixa = [_largura(cab, round(c.queixo - f * c.cabeca)) for f in (0.35, 0.40, 0.45, 0.50, 0.55, 0.60)]
    out = [Medida("rosto_sobre_o_cranio", min(faixa) / max(larguras), (0.78, 1.0),
                  "a largura mais estreita do rosto (de 35 % a 60 % da altura da cabeça) sobre a mais larga do "
                  "crânio; abaixo da faixa, a cabeça lê como uma lâmpada")]
    if "eye_l" in c.ms and "eye_r" in c.ms:
        ys = np.nonzero(_uniao(c.ms, "eye_l", "eye_r").any(axis=1))[0]
        out.append(Medida("olhos_na_cabeca", c.na_cabeca(float(ys.mean())), (0.40, 0.60),
                          "a altura dos olhos na cabeça (0 = o queixo, 1 = o alto); acima da faixa, os olhos ficam "
                          "na testa, onde o chapéu e o cabelo assentam"))
    return out


def _tronco(c: _Corpo) -> list[Medida]:
    larguras = _uniao(c.ms, "chest", "waist", "pelvis_block").sum(axis=1)
    peito, quadril = (int(np.argmax(c.ms[p].sum(axis=1))) for p in ("chest", "pelvis_block"))
    alto, baixo = _fileiras(c.ms["chest"])
    caixa = (baixo - alto + 1) * max(_largura(c.ms["chest"], y) for y in range(alto, baixo + 1))
    return [Medida("cintura_sobre_o_peito", larguras[peito:quadril + 1].min() / larguras[peito], (0.70, 1.0),
                   "a largura mais estreita do tronco, do mais largo do peito ao mais largo do quadril, sobre a do "
                   "peito; abaixo da faixa, o tronco lê como duas bolas, uma sobre a outra"),
            Medida("peito_na_caixa", c.ms["chest"].sum() / caixa, (0.83, 1.0),
                   "a área do peito sobre a da caixa que o contém; abaixo da faixa, o peito é uma bola (a elipse "
                   "enche 0,79 da caixa) e lê como busto")]


def _centro(m: Mascara) -> float:
    xs = np.nonzero(m.any(axis=0))[0]
    return (int(xs.min()) + int(xs.max())) / 2


def _pernas(c: _Corpo) -> list[Medida]:
    pes, quadril = (abs(_centro(c.ms[f"{j}_l"]) - _centro(c.ms[f"{j}_r"])) for j in ("j_ankle", "j_hip"))
    return [Medida("pes_sobre_o_quadril", pes / quadril, (0.6, 1.15),
                   "a distância entre os tornozelos sobre a distância entre as juntas do quadril; acima da faixa, as "
                   "pernas abrem para fora: de frente passam da largura do tronco, e de perfil o pé de lá sobe na "
                   "tela e parece flutuar")]


def _ombros(c: _Corpo) -> list[Medida]:
    esfera = _uniao(c.ms, "j_shoulder_l", "j_shoulder_r")
    alto, baixo = _fileiras(esfera)
    meio = (alto + baixo) // 2
    a, b = _colunas(_uniao(c.ms, *TRONCO), meio)
    centro, meia = (a + b) / 2, (b - a + 1) / 2
    fora = [abs(x - centro) for x in np.nonzero(esfera[meio])[0] if abs(x - centro) > meia]
    return [Medida("vao_no_ombro", (min(fora, default=meia) - meia) / c.estatura, (0.0, 0.01),
                   "o vão entre o tronco e a esfera do ombro, na altura do centro dela, sobre a estatura; acima da "
                   "faixa, não há a linha do ombro e a esfera lê como uma bola solta"),
            Medida("ombro_sobre_o_queixo", (c.queixo - alto) / c.estatura, (-0.08, -0.02),
                   "o quanto o alto do ombro fica acima do queixo, sobre a estatura (negativo = abaixo); acima da "
                   "faixa, os ombros lêem encolhidos, na altura do rosto"),
            Medida("pescoco", max(_largura(c.ms["neck"], y) for y in range(*_fileiras(c.ms["neck"]))) / c.estatura,
                   (0.06, 0.08), "a largura do pescoço sobre a estatura")]


def _perfil(ms: Mascaras) -> list[Medida]:
    """De perfil na vista W: a frente do rosto é a esquerda da tela."""
    cab = _uniao(ms, *CABECA)
    topo, queixo = _fileiras(cab)
    alt = queixo - topo + 1
    frente = {y: _colunas(cab, y)[0] for y in range(topo, queixo + 1)}
    ponta = min(frente.values())
    alturas = [(queixo - y) / alt for y, x in frente.items() if x == ponta]
    out = [Medida("ponta_do_perfil", sum(alturas) / len(alturas), (0.30, 0.55),
                  "a altura, na cabeça, do ponto mais à frente do perfil (num rosto é o nariz); abaixo da faixa, é a "
                  "mandíbula que avança, como um focinho")]
    if "hair_cap" in ms:
        fundo = max(_colunas(cab, y)[1] for y in frente) - ponta + 1
        com = _uniao(ms, *CABECA, "hair_cap", "topknot")
        t, q = _fileiras(com)
        colunas = [_colunas(com, y) for y in range(t, q + 1)]
        fundo_com = max(b for _, b in colunas) - min(a for a, _ in colunas) + 1
        out.append(Medida("cabelo_sobre_o_cranio", fundo_com / fundo, (1.0, 1.15),
                          "a profundidade da cabeça com o cabelo sobre a do crânio; acima da faixa, o cabelo alonga "
                          "a cabeça para trás"))
    return out


def medidas_do_humano(frente: Mascaras, perfil: Mascaras) -> list[dict[str, Any]]:
    """As medidas do corpo, cada uma com o valor, a faixa do corpo real, se cabe nela e o que ela quer dizer."""
    topo, queixo = _fileiras(_uniao(frente, *CABECA))
    chao = _fileiras(_uniao(frente, "foot_l", "foot_r"))[1]
    corpo = _Corpo(frente, topo, queixo, chao - topo + 1)
    return [m.dado() for m in (*_rosto(corpo), *_perfil(perfil), *_tronco(corpo), *_ombros(corpo), *_pernas(corpo))]
