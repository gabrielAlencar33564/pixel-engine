"""A passada com fator de apoio (o passo do quadrúpede): cada pé fica apoiado ``duty``/1000 do ciclo a partir da fase
dele. No apoio, o pé fica fixo no mundo e recua ``2·A`` no espaço do corpo, e a raiz avança ``2·A·1000/duty`` por ciclo
(a velocidade do pé apoiado é a da raiz). O apoio que atravessa o fim do ciclo vira dois contatos, com os alvos no
mundo coerentes através do laço. Na perna de N segmentos, o IK põe o jarrete no alvo e, no balanço, o punho e o
jarrete dobram (a dianteira 30°, a traseira 25°)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from math import isqrt
from typing import Any

from ..core.q8 import pos_to_q8
from ..rig.fk import Skeleton, Vec3i
from ..rig.modelo import Papeis
from .canais import Channels, ClipWriter, bend_guess, inclinacoes_de_repouso, leg_hub, orienta_distais, q_, rest_ankles
from .canais import solve_feet as resolver_pes
from .receita import Instante, canais


def _passada(skel: Skeleton, feet: list[str], rest: dict[str, Vec3i], bob_q8: int, stride_q8: int
             ) -> tuple[int, int, str | None]:
    """A meia-passada e o agachamento constante (os joelhos levemente dobrados): cada perna fica a no máximo 96 % da
    extensão no alto do sobe-e-desce; o agachamento vai até 12 % da perna e, se não basta, a passada encurta."""
    world = skel.solve(skel.rest_local())
    stride, drop, hub = stride_q8, 0, None
    for f in feet:
        shin = skel.bones[f].parent_id
        thigh = skel.bones[shin].parent_id if shin else None
        if thigh is None or shin is None:
            continue
        hub = leg_hub(skel, thigh)
        length = (isqrt(sum(v * v for v in skel.bones[shin].rest_translation_q8))
                  + isqrt(sum(v * v for v in skel.bones[f].rest_translation_q8)))
        vert = pos_to_q8(world[thigh].pos[2]) - rest[f][2] + bob_q8
        reach = (length * 96) // 100
        need = vert - isqrt(max(0, reach * reach - stride * stride))
        drop = max(drop, min(max(0, need), (length * 12) // 100))
        stride = min(stride, isqrt(max(0, reach * reach - (vert - drop) ** 2)))
    return stride, drop, hub


@dataclass(frozen=True)
class _Ciclo:
    duracao: int
    apoio: int  # ms
    meia: int  # a meia-passada (q8)
    lift: int
    inicio: dict[str, int]
    rest: dict[str, Vec3i]

    def fase(self, pe: str, t: int) -> int:
        return (t - self.inicio[pe]) % self.duracao

    def alvo(self, pe: str, t: int) -> Vec3i:
        """O pé no espaço do corpo: no apoio, recua em linha; no balanço, volta à frente suavizado e sobe."""
        x0, y0, z0 = self.rest[pe]
        ph, a = self.fase(pe, t), self.meia
        if ph < self.apoio:
            return x0, y0 + a - q_(2 * a * ph / self.apoio), z0
        s = (ph - self.apoio) / (self.duracao - self.apoio)
        return x0, y0 - a + q_(2 * a * s * s * (3 - 2 * s)), z0 + q_(self.lift * math.sin(math.pi * s))

    def distais(self, pe: str, t: int, repouso: tuple[int, ...]) -> tuple[int, ...]:
        """No balanço, o punho (a dianteira, à frente do centro) dobra 30° e o jarrete 25°, em seno."""
        ph = self.fase(pe, t)
        if ph < self.apoio:
            return repouso
        k = math.sin(math.pi * (ph - self.apoio) / (self.duracao - self.apoio))
        flex = -30_000.0 if self.rest[pe][1] > 0 else -25_000.0
        return tuple(a + q_(flex * k) for a in repouso)


def _contatos(c: _Ciclo, ciclo: int) -> list[dict[str, Any]]:
    out = []
    for pe in c.rest:
        x0, y0, z0 = c.rest[pe]
        s0 = c.inicio[pe]
        fim = s0 + c.apoio
        y = y0 + c.meia + q_(ciclo * s0 / c.duracao)
        out.append({"bone_id": pe, "start_ms": s0, "end_ms": min(fim, c.duracao), "target_q8": [x0, y, z0]})
        if fim > c.duracao:
            out.append({"bone_id": pe, "start_ms": 0, "end_ms": fim - c.duracao, "target_q8": [x0, y - ciclo, z0]})
    return sorted(out, key=lambda d: (d["start_ms"], d["bone_id"]))


def passada_apoio(rec: dict[str, Any], r: Papeis, skel: Skeleton, mp: dict[str, int]) -> dict[str, Any]:
    duracao, k, duty = rec["duracao_ms"], mp.get("scale_pm", 1000) / 1000, mp[rec["apoio"]["par"]]
    pe_de = {r.alvo(r.exige(p, "pe")): r.exige(p, "pe") for p, _ in rec["pernas_pm"]}
    fases = {r.alvo(r.exige(p, "pe")): pm for p, pm in rec["pernas_pm"]}
    feet = sorted(fases)
    rest = rest_ankles(skel, feet)
    meia, drop, hub = _passada(skel, feet, rest, mp[rec["sobe_desce"]["par"]], mp[rec["passada"]["par"]])
    c = _Ciclo(duracao, duracao * duty // 1000, meia, mp[rec["altura"]["par"]],
               {f: duracao * pm // 1000 for f, pm in fases.items()}, rest)
    ciclo = 2 * meia * 1000 // duty
    repouso = inclinacoes_de_repouso(skel, r)
    w = ClipWriter(skel)
    guess = bend_guess(skel, feet)
    for t in range(0, duracao + 1, rec["passo_ms"]):
        ch: Channels = dict(guess)
        ch.update(canais(rec, r, Instante(t, duracao, mp, k)))
        if hub is not None and drop:
            tr, rot = ch.get(hub, ([0, 0, 0], 0))
            ch[hub] = ([tr[0], tr[1], tr[2] - drop], rot)
        ch = resolver_pes(skel, ch, {f: c.alvo(f, t) for f in feet})
        if repouso:
            ch = orienta_distais(skel, ch, r, {pe_de[f]: c.distais(f, t, repouso[pe_de[f]]) for f in feet})
        marcas = [f"contact_{pe_de[f]}" for f in feet if t == c.inicio[f] or (t == duracao and c.inicio[f] == 0)]
        w.key(t, "linear", ch, ([0, q_(ciclo * t / duracao), 0], marcas))
    return w.clip(rec["clip"], duracao, rec["amostras_ms"], _contatos(c, ciclo))
