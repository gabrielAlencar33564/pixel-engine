"""O núcleo do movimento: os canais (o desvio de cada osso sobre o repouso), o escritor do clipe e a solução das
pernas por IK, com a junta do quadril (o plano da perna gira até conter o alvo do pé) e o agachamento de até 1 px
quando o alvo passa do alcance."""

from __future__ import annotations

import math
from typing import Any

from ..core.q8 import atan2_mdeg, normalize_mdeg, pos_to_q8, q8_to_pos
from ..rig.fk import BoneWorld, LocalPose, Skeleton, Vec3i, mat_t_vec
from ..rig.ik import orienta_no_mundo, solve_two_bone
from ..rig.modelo import Papeis

Channels = dict[str, tuple[list[int], int]]
Local = dict[str, LocalPose]


def q_(v: float) -> int:
    return math.floor(v + 0.5)


class ClipWriter:
    def __init__(self, skel: Skeleton) -> None:
        self.bone_ids = sorted(skel.bones)
        self.keyframes: list[dict[str, Any]] = []

    def key(self, t: int, easing: str, channels: Channels, extra: tuple[list[int], list[str]]) -> None:
        """A chave no instante ``t``; ``extra`` = a raiz (q8) e as marcas."""
        bones = {}
        for bid in self.bone_ids:
            tr, rot = channels.get(bid, ([0, 0, 0], 0))
            bones[bid] = {"translation_q8": [int(v) for v in tr], "rotation_mdeg": int(rot)}
        self.keyframes.append({"time_ms": t, "easing": easing, "root_q8": extra[0], "bones": bones,
                               "markers": sorted(extra[1])})

    def clip(self, clip_id: str, duration: int, samples: list[int], contacts: list[dict[str, Any]],
             loop: bool = True) -> dict[str, Any]:
        return {"id": clip_id, "duration_ms": duration, "loop": loop, "keyframes": self.keyframes,
                "sample_times_ms": samples, "contacts": contacts}


def hip_joint(skel: Skeleton, thigh: str) -> str | None:
    """A junta de abertura do quadril: o pai da coxa, se for um osso de comprimento 0 que gira em y enquanto a coxa
    gira em x."""
    b = skel.bones[thigh]
    j = skel.bones.get(b.parent_id) if b.parent_id else None
    if j is None or j.parent_id is None or j.length_q8 != 0 or j.rotation_axis != "y" or b.rotation_axis != "x":
        return None
    return j.id


def leg_hub(skel: Skeleton, thigh: str | None) -> str | None:
    """O osso que o agachamento baixa: o pai da coxa, subindo pelas juntas de comprimento 0."""
    if thigh is None:
        return None
    hub = skel.bones[thigh].parent_id
    if hub is None or hip_joint(skel, thigh) is None:
        return hub
    while hub is not None and skel.bones[hub].length_q8 == 0 and skel.bones[hub].parent_id is not None:
        hub = skel.bones[hub].parent_id
    return hub


def aim_leg_plane(skel: Skeleton, local: Local, foot: str, tgt: Vec3i) -> tuple[Local, dict[str, BoneWorld]]:
    """A junta do quadril girada até o plano da perna conter o alvo do pé, antes do IK planar."""
    shin = skel.bones[foot].parent_id
    thigh = skel.bones[shin].parent_id if shin else None
    joint = hip_joint(skel, thigh) if thigh else None
    world = skel.solve(local)
    if joint is None:
        return local, world
    j = skel.bones[joint]
    parent = world[j.parent_id or ""]
    p = world[joint].pos
    rel = mat_t_vec(parent.rot, (tgt[0] - p[0], tgt[1] - p[1], tgt[2] - p[2]))
    lo, hi = j.angle_limits_mdeg
    out = dict(local)
    out[joint] = LocalPose(max(lo, min(hi, atan2_mdeg(-rel[0], -rel[2]))), local[joint].translation_q8)
    return out, skel.solve(out)


def _locais(skel: Skeleton, channels: Channels) -> Local:
    out = {}
    for bid, b in skel.bones.items():
        tr, rot = channels.get(bid, ([0, 0, 0], 0))
        r = b.rest_translation_q8
        out[bid] = LocalPose(b.rest_rotation_mdeg + rot, (r[0] + tr[0], r[1] + tr[1], r[2] + tr[2]))
    return out


def _tentativa(skel: Skeleton, local: Local, targets: dict[str, Vec3i]) -> tuple[Local, int]:
    worst = 0
    for foot in sorted(targets):
        tgt = (q8_to_pos(targets[foot][0]), q8_to_pos(targets[foot][1]), q8_to_pos(targets[foot][2]))
        local, world = aim_leg_plane(skel, local, foot, tgt)
        local, residual = solve_two_bone(skel, local, world, foot, tgt)
        worst = max(worst, residual)
    return local, worst


def solve_feet(skel: Skeleton, channels: Channels, targets: dict[str, Vec3i]) -> Channels:
    """O IK dos pés (alvos em q8 no espaço do corpo); o quadril desce de 1/8 em 1/8 de px, até 1 px, se o alvo não
    alcança. Devolve os canais com as rotações resolvidas."""
    base = _locais(skel, channels)
    first = skel.bones[sorted(targets)[0]].parent_id
    hub = leg_hub(skel, skel.bones[first].parent_id if first else None)
    local = base
    for step in range(0, 9):
        local = dict(base)
        if step and hub is not None:
            lp = local[hub]
            local[hub] = LocalPose(lp.rotation_mdeg, (lp.translation_q8[0], lp.translation_q8[1],
                                                      lp.translation_q8[2] - 32 * step))
        local, worst = _tentativa(skel, local, targets)
        if worst <= q8_to_pos(16):
            break
    out = dict(channels)
    for bid, b in skel.bones.items():
        tr, _ = channels.get(bid, ([0, 0, 0], 0))
        if bid == hub:
            tr = [local[bid].translation_q8[i] - b.rest_translation_q8[i] for i in range(3)]
        out[bid] = (tr, local[bid].rotation_mdeg - b.rest_rotation_mdeg)
    return out


def chain_world_mdeg(skel: Skeleton, ch: Channels, bone_id: str) -> int:
    """A inclinação em x acumulada (repouso + desvio) do corpo até ``bone_id``, inclusive."""
    total = 0
    bid: str | None = bone_id
    while bid is not None:
        b = skel.bones[bid]
        if b.rotation_axis == "x":
            total += b.rest_rotation_mdeg + ch.get(bid, ([0, 0, 0], 0))[1]
        bid = b.parent_id
    return total


def rest_ankles(skel: Skeleton, feet: list[str]) -> dict[str, Vec3i]:
    world = skel.solve(skel.rest_local())
    return {f: (pos_to_q8(world[f].pos[0]), pos_to_q8(world[f].pos[1]), pos_to_q8(world[f].pos[2])) for f in feet}


def bend_guess(skel: Skeleton, feet: list[str]) -> Channels:
    """Uma flexão pequena do joelho para fixar o sentido de dobra por continuidade."""
    ch: Channels = {}
    for f in feet:
        knee = skel.bones[f].parent_id
        if knee:
            lo, hi = skel.bones[knee].angle_limits_mdeg
            ch[knee] = ([0, 0, 0], -10_000 if -lo >= hi else 10_000)
    return ch


def inclinacoes_de_repouso(skel: Skeleton, r: Papeis) -> dict[str, tuple[int, ...]]:
    """As inclinações de mundo dos distais de cada cadeia no repouso (a pata plana), pelo osso do pé."""
    return {pe: tuple(chain_world_mdeg(skel, {}, b) for b in distais) for pe, (_, distais) in r.cadeias.items()
            if distais}


def orienta_distais(skel: Skeleton, ch: Channels, r: Papeis, angulos: dict[str, tuple[int, ...]]) -> Channels:
    """Os distais de cada cadeia na inclinação de mundo pedida (``angulos[pé]``, mdeg; 0 = vertical, + = a ponta para
    a frente), depois do IK do triângulo."""
    local = {b: LocalPose(normalize_mdeg(lp.rotation_mdeg), lp.translation_q8) for b, lp in _locais(skel, ch).items()}
    out = dict(ch)
    for pe, angs in angulos.items():
        distais = r.cadeias[pe][1]
        local = orienta_no_mundo(skel, local, distais, angs)
        for bid in distais:
            out[bid] = (out.get(bid, ([0, 0, 0], 0))[0], local[bid].rotation_mdeg - skel.bones[bid].rest_rotation_mdeg)
    return out
