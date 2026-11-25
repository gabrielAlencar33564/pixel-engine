"""As vistas e os ossos da composição do prop.

- **Vistas:** o prop declara 1, 2 ou 4 vistas cardinais (S, E, N, W). A IR é uma só, no mundo; cada vista é a câmera
  girada. A regra de oclusão das pilhas (medida na S) vale na outra vista só se a parte da frente continua mais perto
  da câmera dela.
- **Ossos:** as peças desenham na raiz. O nó com ``osso: giro`` vai para o osso ``spin`` (os pontos descontam o centro
  do giro); o nó ``tronco``, para o osso do tronco do balanço; o nó ``cadeia``, para o elo da altura do centro de cada
  parte (a peça que já escolheu o osso de cada massa fica como está).
"""

from __future__ import annotations

import copy
import math
from collections.abc import Sequence
from typing import Any

from .construtor import Vec, q
from .kit.movimento import Elo, bone_for

VISTAS = ("S", "E", "N", "W")
N_VISTAS = (1, 2, 4)
AZIMUTE = {"S": 0, "W": 90_000, "N": 180_000, "E": 270_000}


def _plano(g: dict[str, Any]) -> list[Vec]:
    ox, oy, oz = (c / 256 for c in g["origin_q8"])
    out = []
    for a, b in g["vertices_q8"]:
        a, b = a / 256, b / 256
        out.append((ox + a, oy, oz + b) if g["plane"] == "xz" else (ox, oy + a, oz + b) if g["plane"] == "yz"
                   else (ox + a, oy + b, oz))
    return out


def pontos(g: dict[str, Any]) -> list[Vec]:
    """Os pontos de uma geometria (px, no espaço do osso)."""
    t = g["type"]
    if t == "bound_polygon":
        return [(v["point_q8"][0] / 256, v["point_q8"][1] / 256, v["point_q8"][2] / 256) for v in g["vertices"]]
    if "points_q8" in g:
        return [(p[0] / 256, p[1] / 256, p[2] / 256) for p in g["points_q8"]]
    if t in ("polygon", "stipple"):
        return _plano(g)
    c = g["center_q8"] if t == "ellipse" else g.get("origin_q8")
    return [(c[0] / 256, c[1] / 256, c[2] / 256)] if c is not None else []


def centro(part: dict[str, Any]) -> Vec:
    pts = pontos(part["geometry"]) or [(0.0, 0.0, 0.0)]
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts), sum(p[2] for p in pts) / len(pts))


def _desloca(g: dict[str, Any], d: list[int], bone: str) -> None:
    """Soma ``d`` (q8) aos pontos da geometria e troca o osso dos vértices presos."""
    def soma(p: list[int]) -> list[int]:
        return [p[0] + d[0], p[1] + d[1], p[2] + d[2]]

    if g["type"] == "bound_polygon":
        for v in g["vertices"]:
            v["point_q8"], v["bone_id"] = soma(v["point_q8"]), bone
    elif "points_q8" in g:
        g["points_q8"] = [soma(p) for p in g["points_q8"]]
    elif g["type"] == "ellipse":
        g["center_q8"] = soma(g["center_q8"])
    elif "origin_q8" in g:
        g["origin_q8"] = soma(g["origin_q8"])


def reparentar(parts: Sequence[dict[str, Any]], modo: str, cadeia: Sequence[Elo], centro_giro: Vec | None) -> None:
    """As partes do nó que ficaram na raiz vão para o osso do modo dele (o giro, o tronco ou o elo da cadeia)."""
    for p in parts:
        if p["bone_id"] != "root":
            continue
        if modo == "giro" and centro_giro is not None:
            bone, d = "spin", [-q(c) for c in centro_giro]
        elif modo == "tronco" and cadeia:
            bone, d = "trunk", [0, 0, 0]
        elif modo == "cadeia" and cadeia:
            z = centro(p)[2]
            bone, zl = bone_for(cadeia, z)
            d = [0, 0, -q(z - zl)]
        else:
            continue
        p["bone_id"] = bone
        _desloca(p["geometry"], d, bone)


def regras_da_vista(parts: Sequence[dict[str, Any]], regras: list[dict[str, Any]], az_mdeg: int
                    ) -> list[dict[str, Any]]:
    """As regras da S que valem na vista: a parte da frente não pode estar atrás da de trás (com 1/4 px de folga)."""
    if az_mdeg == 0:
        return regras
    a = math.radians(az_mdeg / 1000)
    cs = {p["id"]: centro(p) for p in parts}

    def perto(c: Vec) -> float:
        return c[0] * math.sin(a) + c[1] * math.cos(a)

    return [r for r in regras if (f := cs.get(r["front"])) is None or (t := cs.get(r["back"])) is None
            or perto(f) >= perto(t) - 0.25]


def no_mundo(parts: Sequence[dict[str, Any]], bones: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cópia das partes com os pontos no mundo (o osso em repouso, só translação), para a caixa do canvas."""
    by = {b["id"]: b for b in bones}

    def origem(bid: str) -> list[int]:
        o = [0, 0, 0]
        while bid in by:
            o = [o[i] + by[bid]["rest_translation_q8"][i] for i in range(3)]
            bid = by[bid]["parent_id"] or ""
        return o

    out = []
    for p in parts:
        p2 = copy.deepcopy(p)
        if p["bone_id"] != "root":
            _desloca(p2["geometry"], origem(p["bone_id"]), "root")
        out.append(p2)
    return out

