"""O volume por pixel da peça com ``volume_sphere``: o tom vem da luz sobre a forma (uma esfera, medida pela largura
de cada fileira e a altura de cada coluna da máscara), com a textura do material por cima. A luz mais forte cai a
~1/3 da largura do lado da luz e as bordas escurecem (a convenção do pixel art em 3/4)."""

from __future__ import annotations

import numpy as np

from ..contracts.estilo import MaterialDef
from .grade import Mascara, NaJanela
from .textura import Floats, Indices, quantize, texture_at

SPH_LIGHT = (-0.42, -0.45, 0.79)  # (lado, cima, frente); o sinal do lado vem do estilo
SMOOTH_ROWS = 2  # a largura de cada fileira é a média de ±2 fileiras: um degrau de 1 px no contorno não vira emenda


def _bordas(mask: Mascara, eixo: int) -> tuple[Floats, Floats]:
    """A primeira e a última célula cheia de cada fileira (``eixo`` 1) ou coluna (``eixo`` 0); nan onde vazia."""
    n = mask.shape[0] if eixo == 1 else mask.shape[1]
    a, b = np.full(n, np.nan), np.full(n, np.nan)
    for i in np.flatnonzero(mask.any(axis=eixo)):
        cheias = np.flatnonzero(mask[i] if eixo == 1 else mask[:, i])
        a[i], b[i] = cheias[0], cheias[-1]
    return a, b


def _u(mask: Mascara) -> Floats:
    """A posição de cada pixel na largura suavizada da fileira dele, de −1 a 1."""
    h, w = mask.shape
    left, right = _bordas(mask, 1)
    rows = np.flatnonzero(mask.any(axis=1))
    lo, hi = int(rows[0]), int(rows[-1])
    sl, sr = left.copy(), right.copy()
    for row in range(lo, hi + 1):
        a, b = max(lo, row - SMOOTH_ROWS), min(hi, row + SMOOTH_ROWS)
        sl[row], sr[row] = np.nanmean(left[a:b + 1]), np.nanmean(right[a:b + 1])
    c = ((sl + sr) / 2)[:, None]
    hw = np.maximum(1.0, (sr - sl) / 2)[:, None]
    res: Floats = np.nan_to_num(np.clip((np.arange(w, dtype=np.float64)[None, :] - c) / hw, -1.0, 1.0))
    return res


def lambert_esfera(mask: Mascara, side: int) -> Floats:
    """A luz (0..1) de cada pixel da máscara como esfera."""
    s = np.zeros(mask.shape, dtype=np.float64)
    if not mask.any():
        return s
    u = _u(mask)
    top, bot = _bordas(mask, 0)
    cy = ((top + bot) / 2)[None, :]
    hh = np.maximum(1.0, (bot - top) / 2)[None, :]
    v = np.nan_to_num(np.clip((np.arange(mask.shape[0], dtype=np.float64)[:, None] - cy) / hh, -1.0, 1.0))
    nz = np.sqrt(np.clip(1 - u * u - v * v, 0.0, 1.0))
    lx, ly, lz = SPH_LIGHT
    s = (abs(lx) * side) * u + ly * v + lz * nz
    res: Floats = np.where(mask, np.clip(s, 0.0, 1.0), 0.0)
    return res


def volume_indices(pj: NaJanela, origem: tuple[int, int], mat: MaterialDef, side: int) -> Indices:
    """A luz da esfera mais a textura contada do canto ``origem`` (x, y) da massa, cortadas na rampa; o pixel com a
    sombra de cima desce um tom."""
    h, w = pj.mask.shape
    yy, xx = np.mgrid[0:h, 0:w]
    s = lambert_esfera(pj.mask, side) + texture_at(xx - origem[0], yy - origem[1], mat.texture)
    return quantize(s, list(mat.ramp), pj.cast)
