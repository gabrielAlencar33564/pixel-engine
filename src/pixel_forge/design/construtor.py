"""O construtor da IR: os ossos e as partes que as peças acrescentam, em dicionários que viram ``AssetIR``."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

Vec = tuple[float, float, float]
FLAT = ("flat", "no_inner_outline")
LINE = ("flat", "detail", "no_outline")
LIT = "lit_by_normal"  # a face tira o tom da normal e da luz do estilo
UNLIT = "unlit"  # a face que não recebe luz (a boca escura, a sombra do beiral, o vidro aceso)


def q(px: float) -> int:
    """Pixels (float de autoria) → q8 inteiro com floor(v·256 + 0.5)."""
    return math.floor(px * 256 + 0.5)


def qv(x: float, y: float, z: float) -> list[int]:
    return [q(x), q(y), q(z)]


@dataclass(frozen=True)
class Parte:
    """Como a peça acrescenta uma parte: o osso, o grupo de contorno, as marcas e a prioridade de desenho."""

    bone: str = "root"
    group: str | None = None
    tags: tuple[str, ...] = ()
    priority: int = 0


@dataclass(frozen=True)
class Junta:
    """Como o osso gira: o eixo, o comprimento (q8), os limites do ângulo e o ângulo de repouso (miligraus)."""

    eixo: str = "x"
    comprimento: int = 0
    limites: tuple[int, int] = (-180_000, 180_000)
    repouso: int = 0


JUNTA = Junta()
PARTE = Parte()


@dataclass
class AssetBuilder:
    bones: list[dict[str, Any]] = field(default_factory=list)
    parts: list[dict[str, Any]] = field(default_factory=list)

    def bone(self, id: str, parent: str | None, t: list[int], junta: Junta = JUNTA) -> None:
        """Um osso de translação ``t`` (q8) a partir do pai."""
        self.bones.append({"id": id, "parent_id": parent, "rest_translation_q8": t, "rest_rotation_mdeg": junta.repouso,
                           "rotation_axis": junta.eixo, "length_q8": junta.comprimento,
                           "angle_limits_mdeg": list(junta.limites)})

    def part(self, id: str, material: str, geometry: dict[str, Any], como: Parte = PARTE) -> None:
        self.parts.append({"id": id, "bone_id": como.bone, "material": material, "geometry": geometry,
                           "tags": sorted(como.tags), "draw_priority": como.priority,
                           "outline_group": como.group or id})


def ellipse(c: list[int], r: list[int]) -> dict[str, Any]:
    return {"type": "ellipse", "center_q8": c, "radii_q8": [max(1, v) for v in r]}


def polyline(points: list[list[int]], thickness: int) -> dict[str, Any]:
    return {"type": "polyline", "points_q8": points, "thickness_px": thickness}


def polygon(origin: list[int], verts: list[list[int]]) -> dict[str, Any]:
    """Um polígono no plano xz a partir de ``origin`` (q8)."""
    return {"type": "polygon", "plane": "xz", "origin_q8": origin, "vertices_q8": verts}


def bound_polygon(pts: list[Vec], bone: str = "root") -> dict[str, Any]:
    return {"type": "bound_polygon", "vertices": [{"bone_id": bone, "point_q8": qv(*p)} for p in pts]}
