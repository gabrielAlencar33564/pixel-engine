"""A pose avaliada: a trajetória da raiz e o osso no mundo."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.q8 import q8_to_pos
from .fk import BoneWorld, Skeleton, Vec3i


@dataclass(frozen=True)
class Pose:
    root_q8: Vec3i
    world: dict[str, BoneWorld]

    def render_offset_pos(self) -> Vec3i:
        """O deslocamento do render: só o z da raiz (o x e o y são o movimento da raiz, exportado à parte)."""
        return (0, 0, q8_to_pos(self.root_q8[2]))


def rest_pose(skel: Skeleton) -> Pose:
    return Pose((0, 0, 0), skel.solve(skel.rest_local()))
