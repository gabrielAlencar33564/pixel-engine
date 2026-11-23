"""A caminhada por poses-chave das folhas de referência: contato, descida, passagem e subida; 16 quadros em 960 ms,
meia passada de 0,28 m.

O pé rola (calcanhar no contato, chapado no apoio, sobe na ponta com o pivô na bola do pé até sair do chão); no
balanço a trajetória sobe rápido, passa alta sob o quadril e desce longa até o calcanhar. A altura do quadril vem das
poses e nunca passa do que a perna alcança; o corpo chega com atraso (os braços depois do contato, a cabeça com o
sobe-e-desce). O pé de apoio anda para trás no corpo na velocidade da raiz: sem escorregar. A saia segue a coxa com
``skirt_lag_ms`` de atraso. Os números das folhas estão na receita (``andar_poses.json``); aqui fica o algoritmo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from ..core.q8 import pos_to_q8
from ..rig.fk import Skeleton, Vec3i
from ..rig.modelo import Papeis
from .canais import Channels, ClipWriter, bend_guess, chain_world_mdeg, q_, rest_ankles, solve_feet
from .receita import Instante, canais, chaves, skirt_follow


def _smooth(u: float) -> float:
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def _pchip(keys: list[Any], u: float) -> float:
    """A curva por chaves em Hermite monótono (Fritsch–Carlson): passa pelas chaves sem parar nelas e sem passar
    delas; os extremos e as pontas têm inclinação 0."""
    ts, vs = [float(k[0]) for k in keys], [float(k[1]) for k in keys]
    n = len(ts)
    h = [ts[i + 1] - ts[i] for i in range(n - 1)]
    dl = [(vs[i + 1] - vs[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    for i in range(1, n - 1):
        if dl[i - 1] * dl[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / dl[i - 1] + w2 / dl[i])
    t = min(1.0, max(0.0, u))
    for i in range(n - 1):
        if ts[i] <= t <= ts[i + 1]:
            hh = ts[i + 1] - ts[i]
            s = (t - ts[i]) / hh
            h00, h10, h01, h11 = 2 * s**3 - 3 * s**2 + 1, s**3 - 2 * s**2 + s, -2 * s**3 + 3 * s**2, s**3 - s**2
            return h00 * vs[i] + h10 * hh * m[i] + h01 * vs[i + 1] + h11 * hh * m[i + 1]
    return vs[-1]


def _apoio(ph: float, a: float, c: dict[str, Any]) -> tuple[float, float, float]:
    """O pé no chão: pousando (gira do calcanhar até chapar), chapado, e o calcanhar subindo com o pivô na bola."""
    y_lin = a - 4 * a * ph  # o pé de apoio recua 4A por ciclo
    if ph < c["chapa"]:
        th = c["pousa_mdeg"] / 1000 * (1 - _smooth(ph / c["chapa"]))
        return y_lin, c["calcanhar_m"] * math.sin(math.radians(th)), th
    if ph < c["calcanhar_sobe"]:
        return y_lin, 0.0, 0.0
    th = c["empurra_mdeg"] / 1000 * _smooth((ph - c["calcanhar_sobe"]) / (c["sai"] - c["calcanhar_sobe"]))
    r = math.radians(-th)
    return y_lin + c["bola_m"] * (1 - math.cos(r)), c["bola_m"] * math.sin(r), th


def foot_path(ph: float, a: float, c: dict[str, Any]) -> tuple[float, float, float]:
    """(y, z, inclinação do pé em graus) do tornozelo em metros, relativo ao repouso, na fase ``ph`` (0 = contato);
    ``a`` = meia passada (m); ``c`` = o pé da receita."""
    if ph < c["sai"]:
        return _apoio(ph, a, c)
    u = (ph - c["sai"]) / (1 - c["sai"])
    y0, z0, th0 = _apoio(c["sai"] - 1e-9, a, c)
    strike = c["pousa_mdeg"] / 1000
    y1, z1 = a, c["calcanhar_m"] * math.sin(math.radians(strike))
    curva = _pchip if c.get("interpolacao") == "pchip" else chaves
    y = y0 + (y1 - y0) * curva(c["avanco"], u)
    z = z0 + (z1 - z0) * u + c["sobe_m"] * curva(c["altura"], u)
    th = chaves([(0.0, th0), *c["inclina_meio"], (c["inclina_pouso_em"], strike), (1.0, strike)], u)
    return y, z, th


@dataclass(frozen=True)
class _Pernas:
    """As pernas da caminhada: (pé, joelho, coxa, início do apoio em ms), o repouso dos tornozelos e, por pé, o
    quadril (q8) e o comprimento da perna."""

    lista: list[tuple[str, str, str, int]]
    rest: dict[str, Vec3i]
    quadril: dict[str, tuple[tuple[int, int, int], float]]


def _pernas(rec: dict[str, Any], r: Papeis, skel: Skeleton) -> _Pernas:
    lista = [(r.exige(p, "pe"), r.exige(p, "joelho"), r.exige(p, "frente"), ms) for p, ms in rec["pernas"]]
    world = skel.solve(skel.rest_local())
    quadril = {}
    for f, shin, thigh, _ in lista:
        length = math.dist((0, 0, 0), skel.bones[shin].rest_translation_q8) + \
            math.dist((0, 0, 0), skel.bones[f].rest_translation_q8)
        p = world[thigh].pos
        quadril[f] = ((pos_to_q8(p[0]), pos_to_q8(p[1]), pos_to_q8(p[2])), length)
    return _Pernas(lista, rest_ankles(skel, [f for f, _, _, _ in lista]), quadril)


@dataclass(frozen=True)
class _Escala:
    a: float  # a meia passada (m)
    ppm: float  # px por metro na escala do corpo

    def q8(self, metros: float) -> float:
        return metros * self.ppm * 256


def _alvos(rec: dict[str, Any], pn: _Pernas, p: float, e: _Escala) -> tuple[dict[str, Vec3i], dict[str, float], float]:
    """Os alvos dos pés, a inclinação de cada um e a queda do quadril (a das poses ou a que a perna de apoio pede)."""
    quadril = rec["quadril"]
    need = 0.0
    targets: dict[str, Vec3i] = {}
    angles: dict[str, float] = {}
    for f, _, _, start_ms in pn.lista:
        y, z, th = foot_path((p - start_ms / rec["duracao_ms"]) % 1.0, e.a, rec["pe"])
        x0, y0, z0 = pn.rest[f]
        tgt = (x0, round(y0 + e.q8(y)), round(z0 + e.q8(z)))
        targets[f], angles[f] = tgt, th
        (hx, hy, hz), length = pn.quadril[f]
        reach = quadril["alcance"] * length
        d2 = (tgt[0] - hx) ** 2 + (tgt[1] - hy) ** 2
        need = max(need, (hz - tgt[2]) - math.sqrt(max(0.0, reach * reach - d2)))
    return targets, angles, max(e.q8(chaves(quadril["chaves_m"], (2 * p) % 1.0)), need)


def _quadro(rec: dict[str, Any], ctx: tuple[Papeis, Skeleton, _Pernas], t: int, mp_e: tuple[dict[str, int], _Escala]
            ) -> Channels:
    """Os canais de um quadro: as curvas do corpo, o IK dos pés e o pé na inclinação da trajetória."""
    r, skel, pn = ctx
    mp, e = mp_e
    p = t / rec["duracao_ms"]
    targets, angles, drop = _alvos(rec, pn, p, e)
    ch: Channels = dict(bend_guess(skel, [f for f, _, _, _ in pn.lista]))
    ch.update(canais(rec, r, Instante(t, rec["duracao_ms"], mp, mp.get("scale_pm", 1000) / 1000, drop, e.q8,
                                      rec.get("curvas", {}))))
    ch = solve_feet(skel, ch, targets)
    for f, shin, _, _ in pn.lista:
        ch[f] = ([0, 0, 0], q_(angles[f] * 1000) - chain_world_mdeg(skel, ch, shin) - skel.bones[f].rest_rotation_mdeg)
    return ch


def passada_poses(rec: dict[str, Any], r: Papeis, skel: Skeleton, mp: dict[str, int]) -> dict[str, Any]:
    """A caminhada por poses-chave da receita ``rec`` nos ossos dos papéis ``r``."""
    duracao, step = rec["duracao_ms"], rec["passo_ms"]
    e = _Escala(mp.get("half_stride_mm", 280) / 1000, 54.0 * (mp.get("scale_pm", 1000) / 1000) / 1.65)
    pn = _pernas(rec, r, skel)
    frames = []
    for t in range(0, duracao + 1, step):
        root = [0, round(e.q8(4 * e.a) * (t / duracao)), 0]
        marks = [f"contact_{f}" for f, _, _, s0 in pn.lista if t % duracao == s0]
        frames.append((t, _quadro(rec, (r, skel, pn), t, (mp, e)), root, marks))
    skirt = skirt_follow(r, mp)
    n = len(frames) - 1  # o último quadro repete o primeiro (t = T)
    if skirt is not None:
        lag = round(mp.get("skirt_lag_ms", 90) / step)
        saias = [r.exige(f"saia_{s}", "frente") for s in ("l", "r")]
        delayed = [skirt({**frames[(i - lag) % n][1]}) for i in range(n)]
        frames = [(t, {**ch, **{b: delayed[i % n][b] for b in saias}}, root, mk)
                  for i, (t, ch, root, mk) in enumerate(frames)]
    w = ClipWriter(skel)
    for t, ch, root, mk in frames:
        w.key(t, "linear", ch, (root, mk))
    contacts = [{"bone_id": f, "start_ms": s0, "end_ms": s0 + duracao // 2,
                 "target_q8": [pn.rest[f][0], round(pn.rest[f][1] + e.q8(e.a) + e.q8(4 * e.a) * s0 / duracao),
                               pn.rest[f][2]]} for f, _, _, s0 in pn.lista]
    contacts.sort(key=lambda c: (c["start_ms"], c["bone_id"]))
    return w.clip(rec["clip"], duracao, list(range(0, duracao, step)), contacts)
