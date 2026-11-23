"""O movimento do prop.

- **Balanço por deslocamento** (``sway``): cada elo da cadeia ``sway_*`` translada em x por px inteiros, numa onda de
  dois harmônicos do período (fecha o laço sem emenda); a fase vem da posição do elo (a onda anda ``onda`` px por
  período) e de um atraso por profundidade (a ponta segue a base). As massas andam inteiras e saem idênticas a si
  mesmas: sem fervura de borda em pixel art.
- **Giro** (``spin``): os ossos ``spin`` dão voltas inteiras, uma chave por amostra, gravadas normalizadas e a menos de
  180° uma da outra: a avaliação vai pelo menor arco, passa por 180° sem salto e o laço fecha pixel a pixel.
"""

from __future__ import annotations

from typing import Any

from ..core.q8 import normalize_mdeg, sin_cos_q30
from ..rig.fk import Skeleton
from .canais import Channels, ClipWriter


def _onda(ph: int) -> int:
    """Os dois harmônicos (q30)."""
    return (7 * sin_cos_q30(ph)[0] + 3 * sin_cos_q30(2 * ph + 40_000)[0]) // 10


def _elo(skel: Skeleton, bid: str) -> tuple[int, int]:
    """A posição x do elo no repouso (q8) e a profundidade dele na cadeia."""
    x, depth = 0, 0
    b = skel.bones.get(bid)
    while b is not None:
        x += b.rest_translation_q8[0]
        depth += 1 if b.id.startswith("sway_") else 0
        b = skel.bones.get(b.parent_id) if b.parent_id else None
    return x, depth


def balanco(skel: Skeleton, mp: dict[str, int]) -> dict[str, Any]:
    duracao, passo, desloca = mp["sway_period_ms"], mp["sway_sample_ms"], mp["sway_shift_px"]
    onda, atraso = max(1, mp["sway_wave_px"]) * 256, mp["sway_lag_mdeg"]
    cadeia = sorted(b for b in skel.bones if b.startswith("sway_"))
    meta = {b: _elo(skel, b) for b in cadeia}
    niveis = max(d for _, d in meta.values())
    w = ClipWriter(skel)
    amostras = list(range(0, duracao, passo))
    for t in [*amostras, duracao]:
        ch: Channels = {}
        acc = {0: 0}
        for bid in sorted(cadeia, key=lambda b: meta[b][1]):
            x, depth = meta[bid]
            ph = 360_000 * t // duracao - 360_000 * x // onda - atraso * (depth - 1)
            acc[depth] = (desloca * _onda(ph) * depth // niveis + (1 << 29)) >> 30  # px da ponta × d/níveis
            ch[bid] = ([(acc[depth] - acc.get(depth - 1, 0)) * 256, 0, 0], 0)
        w.key(t, "hold", ch, ([0, 0, 0], []))
    return w.clip("sway", duracao, amostras, [])


def giro(skel: Skeleton, mp: dict[str, int]) -> dict[str, Any]:
    duracao, n, voltas, sentido = mp["spin_period_ms"], mp["spin_frames"], mp["spin_turns"], mp["spin_dir"]
    ossos = sorted(b for b in skel.bones if b.startswith("spin"))
    w = ClipWriter(skel)
    passo = duracao // n
    for i in range(n + 1):
        rot = normalize_mdeg(sentido * 360_000 * voltas * i // n)
        w.key(i * passo, "linear", {b: ([0, 0, 0], rot) for b in ossos}, ([0, 0, 0], []))
    return w.clip("spin", duracao, [i * passo for i in range(n)], [])
