"""Cinemática direta inteira: matrizes Q30 e posições em unidades POS (1/2^20 px).

Cada osso tem um grau angular sobre o eixo local declarado e uma translação 3D. A composição segue: rotação local →
translação → ancestrais. Nada é arredondado para pixel antes da projeção.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts.ir import BoneDef
from ..core.q8 import ONE_Q30, Q30_SHIFT, q8_to_pos, sin_cos_q30
from ..core.recusa import Recusa

Mat3 = tuple[int, int, int, int, int, int, int, int, int]
Vec3i = tuple[int, int, int]
_HALF = 1 << (Q30_SHIFT - 1)


def rot_axis(axis: str, mdeg: int) -> Mat3:
    s, c = sin_cos_q30(mdeg)
    o = ONE_Q30
    if axis == "x":
        return (o, 0, 0, 0, c, -s, 0, s, c)
    if axis == "y":
        return (c, 0, s, 0, o, 0, -s, 0, c)
    return (c, -s, 0, s, c, 0, 0, 0, o)


def mat_mul(a: Mat3, b: Mat3) -> Mat3:
    r = [(a[i * 3] * b[j] + a[i * 3 + 1] * b[3 + j] + a[i * 3 + 2] * b[6 + j] + _HALF) >> Q30_SHIFT
         for i in range(3) for j in range(3)]
    return (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8])


def mat_vec(m: Mat3, v: Vec3i) -> Vec3i:
    return ((m[0] * v[0] + m[1] * v[1] + m[2] * v[2] + _HALF) >> Q30_SHIFT,
            (m[3] * v[0] + m[4] * v[1] + m[5] * v[2] + _HALF) >> Q30_SHIFT,
            (m[6] * v[0] + m[7] * v[1] + m[8] * v[2] + _HALF) >> Q30_SHIFT)


def mat_t_vec(m: Mat3, v: Vec3i) -> Vec3i:
    """A transposta (a rotação inversa) vezes o vetor."""
    return ((m[0] * v[0] + m[3] * v[1] + m[6] * v[2] + _HALF) >> Q30_SHIFT,
            (m[1] * v[0] + m[4] * v[1] + m[7] * v[2] + _HALF) >> Q30_SHIFT,
            (m[2] * v[0] + m[5] * v[1] + m[8] * v[2] + _HALF) >> Q30_SHIFT)


def vadd(a: Vec3i, b: Vec3i) -> Vec3i:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


@dataclass(frozen=True)
class BoneWorld:
    rot: Mat3
    pos: Vec3i  # unidades POS, no espaço do corpo


@dataclass(frozen=True)
class LocalPose:
    """A transformação local efetiva de um osso: a rotação total e a translação total (q8)."""

    rotation_mdeg: int
    translation_q8: Vec3i


def topo_order(bones: list[BoneDef]) -> list[BoneDef]:
    """Os ossos de pai para filho (desempate pelo id); recusa ciclo e pai que não existe."""
    by_id = {b.id: b for b in bones}
    order: list[BoneDef] = []
    state: dict[str, int] = {}

    def visit(b: BoneDef) -> None:
        if state.get(b.id) == 2:
            return
        if state.get(b.id) == 1:
            raise Recusa("RIG_CICLO", f"Ciclo de parentesco no osso '{b.id}'.", "Cada osso tem um pai acima dele.")
        state[b.id] = 1
        if b.parent_id is not None:
            if b.parent_id not in by_id:
                raise Recusa("RIG_PAI", f"O osso '{b.id}' cita o pai '{b.parent_id}', que não existe.",
                             "Declare o pai antes ou corrija o id.")
            visit(by_id[b.parent_id])
        state[b.id] = 2
        order.append(b)

    for b in sorted(bones, key=lambda x: x.id):
        visit(b)
    return order


class Skeleton:
    def __init__(self, bones: list[BoneDef]) -> None:
        self.bones = {b.id: b for b in bones}
        self.order = topo_order(bones)

    def rest_local(self) -> dict[str, LocalPose]:
        return {b.id: LocalPose(b.rest_rotation_mdeg, (b.rest_translation_q8[0], b.rest_translation_q8[1],
                                                       b.rest_translation_q8[2])) for b in self.bones.values()}

    def solve(self, local: dict[str, LocalPose]) -> dict[str, BoneWorld]:
        world: dict[str, BoneWorld] = {}
        for b in self.order:
            lp = local[b.id]
            r = rot_axis(b.rotation_axis, lp.rotation_mdeg)
            t = (q8_to_pos(lp.translation_q8[0]), q8_to_pos(lp.translation_q8[1]), q8_to_pos(lp.translation_q8[2]))
            if b.parent_id is None:
                world[b.id] = BoneWorld(r, t)
            else:
                p = world[b.parent_id]
                world[b.id] = BoneWorld(mat_mul(p.rot, r), vadd(p.pos, mat_vec(p.rot, t)))
        return world
