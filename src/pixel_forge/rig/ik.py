"""O IK analítico de dois segmentos no plano perpendicular ao eixo comum da cadeia.

O alvo fora do alcance é projetado no alcance e gera resíduo: o osso nunca é esticado em silêncio. A direção da dobra
sai da continuidade com a pose das chaves (o mesmo sinal do ângulo interno atual).
"""

from __future__ import annotations

from math import isqrt

from ..contracts.ir import BoneDef
from ..core.q8 import acos_mdeg, atan2_mdeg, normalize_mdeg, q8_to_pos, sin_cos_q30
from .fk import BoneWorld, LocalPose, Skeleton, Vec3i, mat_t_vec

_PLANO = {"x": (1, 2), "y": (2, 0), "z": (0, 1)}
Local = dict[str, LocalPose]


def _rot2(a: tuple[int, int], mdeg: int) -> tuple[int, int]:
    s, c = sin_cos_q30(mdeg)
    return ((a[0] * c - a[1] * s) >> 30, (a[0] * s + a[1] * c) >> 30)


def _no_plano(local: Local, bone: str, plano: tuple[int, int]) -> tuple[int, int]:
    t = tuple(q8_to_pos(v) for v in local[bone].translation_q8)
    return t[plano[0]], t[plano[1]]


def _limita(theta: int, b: BoneDef) -> int:
    lo, hi = b.angle_limits_mdeg
    return max(lo, min(hi, theta))


def _angulos(local: Local, cadeia: tuple[BoneDef, BoneDef, BoneDef], d: tuple[int, int]
             ) -> tuple[int, int]:
    """(θ do segmento de cima, θ do de baixo) que põem a ponta a ``d`` da origem, no plano da cadeia."""
    a, b, e = cadeia
    plano = _PLANO[a.rotation_axis]
    tb, te = _no_plano(local, b.id, plano), _no_plano(local, e.id, plano)
    l1, l2 = isqrt(tb[0] ** 2 + tb[1] ** 2), isqrt(te[0] ** 2 + te[1] ** 2)
    dist = isqrt(d[0] ** 2 + d[1] ** 2)
    dist_c = max(abs(l1 - l2), min(l1 + l2, dist))
    phi_b0, phi_e0 = atan2_mdeg(tb[1], tb[0]), atan2_mdeg(te[1], te[0])
    gamma = acos_mdeg(dist_c * dist_c - l1 * l1 - l2 * l2, 2 * l1 * l2)
    cur = normalize_mdeg(phi_e0 + local[b.id].rotation_mdeg - phi_b0)
    sign = -1 if cur < 0 else 1
    if cur == 0:
        lo, hi = b.angle_limits_mdeg
        sign = 1 if hi >= -lo else -1
    theta_b = normalize_mdeg(gamma * sign - phi_e0 + phi_b0)
    te_rot = _rot2(te, theta_b)
    v = (tb[0] + te_rot[0], tb[1] + te_rot[1])
    alvo = atan2_mdeg(v[1], v[0]) if dist == 0 else atan2_mdeg(d[1], d[0])
    return normalize_mdeg(alvo - atan2_mdeg(v[1], v[0])), theta_b


def solve_two_bone(skel: Skeleton, local: Local, world: dict[str, BoneWorld], end_bone: str,
                   target_body_pos: Vec3i) -> tuple[Local, int]:
    """A pose com a ponta da cadeia de ``end_bone`` no alvo (espaço do corpo) e o resíduo (POS)."""
    e = skel.bones[end_bone]
    b = skel.bones[e.parent_id] if e.parent_id else None
    a = skel.bones[b.parent_id] if b and b.parent_id else None
    if a is None or b is None or a.parent_id is None or a.rotation_axis != b.rotation_axis:
        return local, 0
    plano = _PLANO[a.rotation_axis]
    parent = world[a.parent_id]
    t_local = mat_t_vec(parent.rot, (target_body_pos[0] - parent.pos[0], target_body_pos[1] - parent.pos[1],
                                     target_body_pos[2] - parent.pos[2]))
    a0 = _no_plano(local, a.id, plano)
    theta_a, theta_b = _angulos(local, (a, b, e), (t_local[plano[0]] - a0[0], t_local[plano[1]] - a0[1]))
    theta_a, theta_b = _limita(theta_a, a), _limita(theta_b, b)
    old_sum = local[a.id].rotation_mdeg + local[b.id].rotation_mdeg
    out = dict(local)
    out[a.id] = LocalPose(theta_a, local[a.id].translation_q8)
    out[b.id] = LocalPose(theta_b, local[b.id].translation_q8)
    if e.rotation_axis == a.rotation_axis:  # preserva a orientação do efetuador
        out[e.id] = LocalPose(normalize_mdeg(local[e.id].rotation_mdeg + old_sum - theta_a - theta_b),
                              local[e.id].translation_q8)
    w2 = skel.solve(out)[e.id].pos
    diff = (w2[0] - target_body_pos[0], w2[1] - target_body_pos[1], w2[2] - target_body_pos[2])
    return out, isqrt(diff[0] ** 2 + diff[1] ** 2 + diff[2] ** 2)


def _x_acima(skel: Skeleton, local: Local, bone: str | None) -> int:
    """A inclinação em x acumulada (o ângulo local de cada osso de eixo x) do ``bone`` até a raiz, inclusive."""
    total = 0
    while bone is not None:
        b = skel.bones[bone]
        if b.rotation_axis == "x":
            total += local[bone].rotation_mdeg
        bone = b.parent_id
    return total


def orienta_no_mundo(skel: Skeleton, local: Local, ossos: tuple[str, ...], angulos: tuple[int, ...]) -> Local:
    """Os segmentos distais da cadeia na inclinação de mundo pedida (mdeg, um por osso, na ordem): cada um desconta a
    cadeia acima dele. É a metade de cima do IK de N segmentos: a pata plana no apoio, o punho que dobra no balanço."""
    out = dict(local)
    for bone, ang in zip(ossos, angulos, strict=True):
        out[bone] = LocalPose(ang - _x_acima(skel, out, skel.bones[bone].parent_id), out[bone].translation_q8)
    return out
