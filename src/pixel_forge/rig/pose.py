"""A pose: o repouso, ou o instante de um clipe (as chaves amostradas, os limites e o IK dos contatos)."""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts.clipe import Chave, Clipe
from ..core.q8 import normalize_mdeg, q8_to_pos, round_half_up_div, shortest_arc_mdeg
from .fk import BoneWorld, LocalPose, Skeleton, Vec3i
from .ik import solve_two_bone


@dataclass(frozen=True)
class Pose:
    root_q8: Vec3i
    world: dict[str, BoneWorld]

    def render_offset_pos(self) -> Vec3i:
        """O deslocamento do render: só o z da raiz (o x e o y são o movimento da raiz, exportado à parte)."""
        return (0, 0, q8_to_pos(self.root_q8[2]))


def rest_pose(skel: Skeleton) -> Pose:
    return Pose((0, 0, 0), skel.solve(skel.rest_local()))


def _ease(easing: str, num: int, den: int) -> tuple[int, int]:
    """O fator de interpolação como fração (n, d): segura, linear ou smoothstep 3u² − 2u³."""
    if easing == "hold":
        return 0, 1
    if easing == "linear":
        return num, den
    return 3 * num * num * den - 2 * num * num * num, den * den * den


def _lerp(a: int, b: int, n: int, d: int) -> int:
    return a + round_half_up_div((b - a) * n, d)


def _segmento(clip: Clipe, t: int) -> tuple[Chave, Chave, int, int]:
    kfs = clip.keyframes
    if t >= kfs[-1].time_ms:
        return kfs[-1], kfs[-1], 0, 1
    lo = next((i for i in range(len(kfs) - 1) if kfs[i].time_ms <= t < kfs[i + 1].time_ms), 0)
    k0, k1 = kfs[lo], kfs[lo + 1]
    return k0, k1, t - k0.time_ms, k1.time_ms - k0.time_ms


def sample_channels(clip: Clipe, t: int) -> tuple[Vec3i, dict[str, tuple[Vec3i, int]]]:
    """A raiz e o desvio de cada osso no instante, pela suavização da chave de antes."""
    k0, k1, num, den = _segmento(clip, t)
    n, d = _ease(k0.easing, num, den)
    root = (_lerp(k0.root_q8[0], k1.root_q8[0], n, d), _lerp(k0.root_q8[1], k1.root_q8[1], n, d),
            _lerp(k0.root_q8[2], k1.root_q8[2], n, d))
    bones = {}
    for bid, c0 in k0.bones.items():
        c1 = k1.bones[bid]
        tr = (_lerp(c0.translation_q8[0], c1.translation_q8[0], n, d),
              _lerp(c0.translation_q8[1], c1.translation_q8[1], n, d),
              _lerp(c0.translation_q8[2], c1.translation_q8[2], n, d))
        rot = c0.rotation_mdeg + round_half_up_div(shortest_arc_mdeg(c0.rotation_mdeg, c1.rotation_mdeg) * n, d)
        bones[bid] = (tr, normalize_mdeg(rot))
    return root, bones


def avaliar(skel: Skeleton, clip: Clipe, t: int) -> Pose:
    """A pose no instante: as chaves amostradas, os limites dos ossos e o IK dos contatos ativos (o alvo no mundo,
    descontada a raiz)."""
    root, canais = sample_channels(clip, t)
    local: dict[str, LocalPose] = {}
    for bid, bone in skel.bones.items():
        tr, rot = canais.get(bid, ((0, 0, 0), 0))
        lo, hi = bone.angle_limits_mdeg
        r = bone.rest_translation_q8
        local[bid] = LocalPose(max(lo, min(hi, normalize_mdeg(bone.rest_rotation_mdeg + rot))),
                               (r[0] + tr[0], r[1] + tr[1], r[2] + tr[2]))
    world = skel.solve(local)
    for c in clip.contacts:
        if c.start_ms <= t < c.end_ms:
            alvo = (q8_to_pos(c.target_q8[0] - root[0]), q8_to_pos(c.target_q8[1] - root[1]),
                    q8_to_pos(c.target_q8[2] - root[2]))
            local, _ = solve_two_bone(skel, local, world, c.bone_id, alvo)
            world = skel.solve(local)
    return Pose(root, world)
