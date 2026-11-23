"""O canvas pelo tamanho do asset: a caixa da geometria na tela de cada vista, na câmera física de 45° do kit (uma
folga sobre o 0,35 do oblíquo), mais a margem. O pivô (a origem do mundo) cai onde a geometria manda e fica sempre
dentro do canvas."""

from __future__ import annotations

import math
from typing import Any

from .vistas import pontos

_S, _C = math.sin(math.radians(45)), math.cos(math.radians(45))


class _Caixa:
    def __init__(self) -> None:
        self.us: list[float] = []
        self.vs: list[float] = []

    def ponto(self, p: tuple[float, float, float], r: float, rot: tuple[int, int]) -> None:
        ca, sa = rot
        x, y = p[0] * ca - p[1] * sa, p[0] * sa + p[1] * ca
        self.us.extend((x - r, x + r))
        self.vs.extend((y * _S - p[2] * _C - r, y * _S - p[2] * _C + r))

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

    def geometria(self, g: dict[str, Any], rot: tuple[int, int]) -> None:
        t = g["type"]
        if t == "ellipse":
            self.elipse(g, rot)
            return
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
            caixa.geometria(p["geometry"], rot)
    u0, u1 = math.floor(min(caixa.us)) - margem, math.ceil(max(caixa.us)) + margem
    v0, v1 = math.floor(min(caixa.vs)) - margem, math.ceil(max(caixa.vs)) + margem
    return {"width": u1 - u0, "height": v1 - v0, "pivot_px": [-u0, -v0]}
