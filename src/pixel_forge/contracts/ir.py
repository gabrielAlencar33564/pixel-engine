"""A IR do asset: as geometrias em q8, o rig, as peças e as vistas. É o que a composição monta e o render desenha.

A câmera é uma só (o 3/4 oblíquo, ``views/camera.py``): a vista guarda só a direção e o que muda nela.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from .base import Direcao, Id, Mdeg, NonNegInt, Strict, Vec2, Vec3

Inteiro = Annotated[int, Field(strict=True)]


class RevolutionGeom(Strict):
    """Sólido de revolução em pé: cada estação ``[z, r, dx]`` (q8) dá a altura acima de ``origin_q8``, o raio e o
    desvio do eixo em x, com ``z`` crescente."""

    type: Literal["revolution"]
    origin_q8: Vec3
    stations: Annotated[list[Annotated[list[Inteiro], Field(min_length=3, max_length=3)]],
                        Field(min_length=2, max_length=64)]


class EllipseGeom(Strict):
    type: Literal["ellipse"]
    center_q8: Vec3
    radii_q8: Annotated[list[Annotated[int, Field(ge=1, le=1 << 20, strict=True)]], Field(min_length=3, max_length=3)]


class BoundVertex(Strict):
    bone_id: Id
    point_q8: Vec3


class BoundPolygonGeom(Strict):
    """Polígono cujos vértices pertencem a ossos diferentes, preenchido em leque a partir do vértice 0."""

    type: Literal["bound_polygon"]
    vertices: Annotated[list[BoundVertex], Field(min_length=3, max_length=32)]


Geometry = Annotated[RevolutionGeom | EllipseGeom | BoundPolygonGeom, Field(discriminator="type")]


class BoneDef(Strict):
    id: Id
    parent_id: Id | None
    rest_translation_q8: Vec3
    rest_rotation_mdeg: Mdeg
    rotation_axis: Literal["x", "y", "z"]
    length_q8: NonNegInt
    angle_limits_mdeg: Annotated[list[Mdeg], Field(min_length=2, max_length=2)]


class LandmarkDef(Strict):
    id: Id
    point_q8: Vec3


class PartDef(Strict):
    id: Id
    bone_id: Id
    material: Id
    geometry: Geometry
    landmarks: list[LandmarkDef] = Field(default_factory=list)
    tags: list[Id] = Field(default_factory=list)
    draw_priority: Annotated[int, Field(ge=-1000, le=1000, strict=True)] = 0
    outline_group: Id


class OcclusionRule(Strict):
    front: Id
    back: Id


class ViewSpec(Strict):
    visibility: dict[Id, Literal["hidden"]] = Field(default_factory=dict)
    depth_bias: dict[Id, Annotated[int, Field(ge=-65536, le=65536, strict=True)]] = Field(default_factory=dict)
    occlusion_rules: list[OcclusionRule] = Field(default_factory=list)


class CanvasDef(Strict):
    width: Annotated[int, Field(ge=8, le=256, strict=True)]
    height: Annotated[int, Field(ge=8, le=256, strict=True)]
    pivot_px: Vec2


class AssetIR(Strict):
    id: Id
    revision: Annotated[int, Field(ge=1, strict=True)]
    canvas: CanvasDef
    bones: list[BoneDef]
    parts: list[PartDef]
    views: dict[Direcao, ViewSpec]
