"""A ligação da planta: nenhuma parte fica no ar. Cada nó de planta (o lenho, a folhagem, a lâmina) tem de tocar o
chão, uma peça que não é de planta (o vaso, o muro) ou outro nó de planta já ligado: o tronco nasce no chão, o galho
nasce do tronco, a copa envolve o alto do tronco ou a ponta de um galho, a touceira nasce no chão ou no alto de um
tronco. É conferido na geometria do mundo, antes de desenhar: o vão que uma vista esconde aparece em outra.

Cada parte vira bolas (o ponto e o raio dela nesse ponto) ou, o elipsoide e a face, um corpo; dois nós se tocam
quando uma bola de um entra no corpo ou encosta numa bola do outro."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from ..core.recusa import Recusa
from .escala import PPM

CHAO = 1.5  # a parte que chega a esta altura do chão (px) toca o chão
FOLGA = 1.0  # duas partes a menos disto uma da outra (px) se tocam
PASSO = 2.0  # as bolas ao longo de um traço ficam a no máximo isto uma da outra (px)
Bola = tuple[float, float, float, float]  # x, y, z e o raio
Caixa = tuple[tuple[float, float, float], tuple[float, float, float]]  # o centro e os meios lados
DICAS = {
    "lenho": "O tronco nasce no chão, e os galhos, do tronco: ponha o `tronco_em_pe` antes dos `galhos`.",
    "folhagem": "Leve o tronco (ou a ponta de um galho) até dentro da copa, ou desça a copa até ele.",
    "lamina": "O `pe` da touceira fica no chão ou no alto de um tronco.",
}


@dataclass
class _No:
    """Um nó da composição no mundo: o papel dele na planta, as bolas, os elipsoides e as caixas das faces."""

    id: str
    papel: str
    bolas: list[Bola] = field(default_factory=list)
    elipsoides: list[Caixa] = field(default_factory=list)
    faces: list[Caixa] = field(default_factory=list)

    def soma(self, g: dict[str, Any]) -> None:
        if g["type"] == "ellipse":
            c, r = [v / 256 for v in g["center_q8"]], [v / 256 for v in g["radii_q8"]]
            self.elipsoides.append(((c[0], c[1], c[2]), (r[0], r[1], r[2])))
        elif g["type"] == "revolution":
            o = g["origin_q8"]
            self.bolas += _ao_longo([((o[0] + dx) / 256, o[1] / 256, (o[2] + z) / 256, r / 256)
                                     for z, r, dx in g["stations"]])
        elif g["type"] == "bound_polygon":
            pts = [[c / 256 for c in v["point_q8"]] for v in g["vertices"]]
            lo, hi = [min(p[k] for p in pts) for k in range(3)], [max(p[k] for p in pts) for k in range(3)]
            self.faces.append((((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2),
                               ((hi[0] - lo[0]) / 2, (hi[1] - lo[1]) / 2, (hi[2] - lo[2]) / 2)))
        else:
            pontos = g["points_q8"]
            raios = [r / 256 for r in g["radii_q8"]] if "radii_q8" in g else [g["thickness_px"] / 2] * len(pontos)
            self.bolas += _ao_longo([(p[0] / 256, p[1] / 256, p[2] / 256, r)
                                     for p, r in zip(pontos, raios, strict=True)])

    def fundo(self) -> float:
        """A altura do ponto mais baixo do nó."""
        return min([b[2] - b[3] for b in self.bolas] + [c[2] - r[2] for c, r in self.elipsoides + self.faces])

    def como_bolas(self) -> list[Bola]:
        """O nó inteiro em bolas: as dele e o centro de cada elipsoide e de cada face, com o menor meio lado."""
        return self.bolas + [(*c, min(r)) for c, r in self.elipsoides + self.faces]


def _ao_longo(pts: list[Bola]) -> list[Bola]:
    """As bolas pelos pontos de um traço, com as do meio de cada trecho a no máximo ``PASSO`` uma da outra."""
    out = [pts[0]]
    for a, b in zip(pts, pts[1:], strict=False):
        n = max(1, math.ceil(math.dist(a[:3], b[:3]) / PASSO))
        out += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, a[2] + (b[2] - a[2]) * i / n,
                 a[3] + (b[3] - a[3]) * i / n) for i in range(1, n + 1)]
    return out


def _vao(a: _No, b: _No) -> float:
    """O vão entre dois nós (px; zero ou menos = se tocam): a menor distância de uma bola de um à superfície de um
    corpo ou de uma bola do outro."""
    menor = math.inf
    for um, outro in ((a, b), (b, a)):
        for x, y, z, r in um.como_bolas():
            for c, e in outro.elipsoides:  # dentro do elipsoide (inchado do raio da bola): toca
                d = math.sqrt(sum(((p - o) / (s + r + FOLGA)) ** 2 for p, o, s in zip((x, y, z), c, e, strict=True)))
                menor = min(menor, (d - 1) * min(e))
            for c, e in outro.faces:  # dentro da caixa da face (a saia da conífera sobre o tronco)
                fora = [max(0.0, abs(p - o) - s - r) for p, o, s in zip((x, y, z), c, e, strict=True)]
                menor = min(menor, math.hypot(*fora) - FOLGA)
            for bx, by, bz, br in outro.bolas:
                menor = min(menor, math.dist((x, y, z), (bx, by, bz)) - r - br - FOLGA)
    return menor


def conferir_ligacao(parts: Sequence[dict[str, Any]], donos: dict[str, tuple[str, str]]) -> None:
    """Recusa a composição com um nó de planta no ar. ``parts``: as partes no mundo; ``donos``: de cada parte, o nó
    e o papel dele na planta (vazio = não é de planta: conta como apoio)."""
    nos: dict[str, _No] = {}
    for p in parts:
        no, papel = donos[p["id"]]
        nos.setdefault(no, _No(no, papel)).soma(p["geometry"])
    plantas = [n for n in nos.values() if n.papel]
    ligados = [n for n in nos.values() if not n.papel] + [n for n in plantas if n.fundo() <= CHAO]
    soltos = [n for n in plantas if n.fundo() > CHAO]
    while True:
        achados = [n for n in soltos if any(_vao(n, outro) <= 0 for outro in ligados)]
        if not achados:
            break
        ligados += achados
        soltos = [n for n in soltos if n not in achados]
    if soltos:
        solto = soltos[0]
        perto = min(((_vao(solto, outro), outro.id) for outro in ligados), default=(solto.fundo(), "chão"))
        vao, de = (solto.fundo(), "chão") if solto.fundo() < perto[0] else perto
        raise Recusa("LIGACAO", f"O nó '{solto.id}' fica no ar: não toca o chão nem outra parte ligada da planta (o "
                     f"mais perto é '{de}', a {vao / PPM * 100:.0f} cm).", DICAS[solto.papel], "/nos")
