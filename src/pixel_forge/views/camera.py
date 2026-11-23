"""A câmera do sprite: o 3/4 oblíquo em ponto fixo, a única do motor.

A altura aparece a cos(45°) e a profundidade a 0,35 na tela. Para o azimute ``a`` da direção::

    x' = x cos a - y sin a          y' = x sin a + y cos a
    u  = pivô_u + x'                v  = pivô_v + y'·0,35 - z cos 45°
    profundidade = y' cos 45° + z sin 45°      (maior = mais perto da câmera)

A origem do corpo cai no centro do pixel do pivô; a tela sai em q8 do canvas.
"""

from __future__ import annotations

from math import isqrt

from ..core.q8 import Q30_SHIFT, pos_to_q8, sin_cos_q30
from ..rig.fk import Mat3, Vec3i, mat_t_vec

ELEVACAO_MDEG = 45_000
PROFUNDIDADE_PERMILLE = 350
_HALF = 1 << (Q30_SHIFT - 1)


class Camera:
    def __init__(self, azimuth_mdeg: int, pivot_px: list[int]) -> None:
        self.sa, self.ca = sin_cos_q30(azimuth_mdeg)
        self.se, self.ce = sin_cos_q30(ELEVACAO_MDEG)
        self.sd = (PROFUNDIDADE_PERMILLE << Q30_SHIFT) // 1000
        self.pu = pivot_px[0] * 256 + 128
        self.pv = pivot_px[1] * 256 + 128
        self.eu: Vec3i = (self.ca, -self.sa, 0)
        self.ev: Vec3i = ((self.sa * self.sd + _HALF) >> Q30_SHIFT, (self.ca * self.sd + _HALF) >> Q30_SHIFT, -self.ce)
        self.ed: Vec3i = ((self.sa * self.ce + _HALF) >> Q30_SHIFT, (self.ca * self.ce + _HALF) >> Q30_SHIFT, self.se)

    def project(self, p: Vec3i) -> Vec3i:
        """(u, v) em q8 de tela e a profundidade em POS."""
        x, y, z = p
        xp = (x * self.ca - y * self.sa + _HALF) >> Q30_SHIFT
        yp = (x * self.sa + y * self.ca + _HALF) >> Q30_SHIFT
        v = (yp * self.sd - z * self.ce + _HALF) >> Q30_SHIFT
        depth = (yp * self.ce + z * self.se + _HALF) >> Q30_SHIFT
        return self.pu + pos_to_q8(xp), self.pv + pos_to_q8(v), depth

    def facing_permille(self, pts: list[Vec3i]) -> Vec3i | None:
        """A normal de Newell do polígono (no espaço do corpo) nos eixos de câmera, ×1000 e virada para a câmera (a
        face tem dois lados: o verso visível segue a mesma regra que a frente)."""
        nx = ny = nz = 0
        for (x0, y0, z0), (x1, y1, z1) in zip(pts, pts[1:] + pts[:1], strict=True):
            nx += (y0 - y1) * (z0 + z1)
            ny += (z0 - z1) * (x0 + x1)
            nz += (x0 - x1) * (y0 + y1)
        cu = nx * self.eu[0] + ny * self.eu[1] + nz * self.eu[2]
        cv = nx * self.ev[0] + ny * self.ev[1] + nz * self.ev[2]
        cd = nx * self.ed[0] + ny * self.ed[1] + nz * self.ed[2]
        norm = isqrt(cu * cu + cv * cv + cd * cd)
        if norm == 0:
            return None
        sign = -1 if cd < 0 else 1
        return (sign * cu * 1000 // norm, sign * cv * 1000 // norm, sign * cd * 1000 // norm)

    def extent_q8(self, rot: Mat3, radii_q8: list[int], axis: Vec3i) -> int:
        """A meia-largura na tela (no eixo ``axis``) do elipsoide de raios ``radii_q8`` no espaço da peça."""
        w = mat_t_vec(rot, axis)
        s = sum((r * wi) ** 2 for r, wi in zip(radii_q8, w, strict=True))
        return max(1, (isqrt(s) + _HALF) >> Q30_SHIFT)
