"""O canvas pelo tamanho do asset: a caixa da geometria na tela de cada vista, na câmera física de 45° do kit (o chão
a 0,71, mais fundo que o 0,6 do oblíquo; o quadro que ainda sair cortado é recusado na checagem), e a da sombra que
ela projeta no chão (à direita da base, pela luz da câmera), mais a margem. O pivô (a origem do mundo) cai onde a
geometria manda e fica sempre dentro do canvas."""

from __future__ import annotations

import math
from typing import Any

from ..views.camera import SOMBRA_POR_ALTURA
from .vistas import pontos

_S, _C = math.sin(math.radians(45)), math.cos(math.radians(45))


# o que projeta sombra no chão no render: as faces de vértices em ossos, os traços, as elipses alinhadas à tela, o
# tronco e o cacho pontilhado (o polígono plano e o detalhe não projetam)
PROJETAM = ("bound_polygon", "polyline", "tapered_polyline", "ellipse", "revolution", "stipple")
NAO_PROJETAM = frozenset({"detail", "no_cast", "oriented"})


def projeta(part: dict[str, Any]) -> bool:
    return part["geometry"]["type"] in PROJETAM and not NAO_PROJETAM & set(part["tags"])


class _Caixa:
    def __init__(self) -> None:
        self.us: list[float] = []
        self.vs: list[float] = []
        self.projeta = False  # a parte da vez projeta sombra no chão

    def ponto(self, p: tuple[float, float, float], r: float, rot: tuple[int, int]) -> None:
        ca, sa = rot
        x, y = p[0] * ca - p[1] * sa, p[0] * sa + p[1] * ca
        self.us.extend((x - r, x + r))
        self.vs.extend((y * _S - p[2] * _C - r, y * _S - p[2] * _C + r))
        self.sombra(x + r, y * _S + r, p[2] + r)

    def sombra(self, u: float, v_chao: float, z: float) -> None:
        """A sombra no chão do ponto a ``z`` px de altura: ``SOMBRA_POR_ALTURA``·z à direita da base dele."""
        if self.projeta and z > 0:
            self.us.append(u + SOMBRA_POR_ALTURA * z)
            self.vs.append(v_chao)

    def elipse(self, g: dict[str, Any], rot: tuple[int, int]) -> None:
        ca, sa = rot
        cx, cy, cz = g["center_q8"]
        rx, ry, rz = (v / 256 for v in g["radii_q8"])
        if sa:
            rx, ry = ry, rx
        self.ponto((cx / 256, cy / 256, cz / 256), 0.0, rot)
        x = (cx * ca - cy * sa) / 256
        self.us.extend((x - rx, x + rx))
        vv = ((cx * sa + cy * ca) / 256) * _S - (cz / 256) * _C
        dv = ry * _S + rz * _C
        self.vs.extend((vv - dv, vv + dv))
        self.sombra(x + rx, ((cx * sa + cy * ca) / 256 + ry) * _S, cz / 256 + rz)

    def almofada(self, g: dict[str, Any], rot: tuple[int, int]) -> None:
        """O cacho pontilhado: a sombra dele é a almofada redonda, que no chão desce meia largura para a frente."""
        ca, sa = rot
        ps = [(p[0] * ca - p[1] * sa, p[0] * sa + p[1] * ca, p[2]) for p in pontos(g)]
        meia = (max(p[0] for p in ps) - min(p[0] for p in ps)) / 2
        for x, y, z in ps:
            self.sombra(x, (y + meia) * _S, z)

    def geometria(self, g: dict[str, Any], rot: tuple[int, int]) -> None:
        t = g["type"]
        if t == "ellipse":
            self.elipse(g, rot)
            return
        if t == "stipple":
            self.almofada(g, rot)
        if t == "bound_polygon" or "points_q8" in g:
            raio = g.get("thickness_px", 1) / 2 if "points_q8" in g else 0.0
            for p in pontos(g):
                self.ponto(p, raio, rot)
            return
        estacoes = g.get("stations", [])
        raio = max((abs(e[1]) for e in estacoes), default=0) / 256
        for p in pontos(g):
            self.ponto(p, raio, rot)
        ox, oy, oz = g["origin_q8"]
        for e in estacoes:
            self.ponto(((ox + e[2]) / 256, oy / 256, (oz + e[0]) / 256), e[1] / 256, rot)


def canvas_do_prop(parts: list[dict[str, Any]], margem: int, azimutes: tuple[int, ...]) -> dict[str, Any]:
    caixa = _Caixa()
    for az in azimutes:
        rot = (round(math.cos(math.radians(az / 1000))), round(math.sin(math.radians(az / 1000))))
        caixa.ponto((0.0, 0.0, 0.0), 0.5, rot)  # o pixel do pivô (e o ponto logo acima dele) cabe no canvas
        caixa.ponto((0.0, 0.0, 0.01), 0.5, rot)
        for p in parts:
            caixa.projeta = projeta(p)
            caixa.geometria(p["geometry"], rot)
    u0, u1 = math.floor(min(caixa.us)) - margem, math.ceil(max(caixa.us)) + margem
    v0, v1 = math.floor(min(caixa.vs)) - margem, math.ceil(max(caixa.vs)) + margem
    return {"width": u1 - u0, "height": v1 - v0, "pivot_px": [-u0, -v0]}
