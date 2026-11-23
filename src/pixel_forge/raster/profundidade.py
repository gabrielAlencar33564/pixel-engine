"""A profundidade por pixel de cada superfície (maior = mais perto da câmera), para o z-buffer.

- plana: profundidade constante;
- elipsoide: a superfície frontal de ``[x y d]·A·[x y d]ᵀ = 1`` (o maior ``d``);
- leque: os triângulos a partir do vértice 0, cada um plano pelos três vértices; o pixel da borda fora deles fica com
  o vértice mais perto.

Só operações IEEE corretamente arredondadas (+ − × ÷ √), quantizadas a 1/16 px antes de qualquer comparação.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from ..views.primitivas import SupElipsoide, Superficie, SupLeque, SupPlana, SupTubo
from .grade import MARGIN, Mascara
from .textura import Floats

DEPTH_QUANT = 16  # unidades por pixel


def _grid(w: int, h: int) -> tuple[Floats, Floats]:
    xs = ((np.arange(w, dtype=np.int64) - MARGIN) * 256 + 128).astype(np.float64)
    ys = ((np.arange(h, dtype=np.int64) - MARGIN) * 256 + 128).astype(np.float64)
    return np.broadcast_to(xs[None, :], (h, w)), np.broadcast_to(ys[:, None], (h, w))


def _elipsoide(s: SupElipsoide, px: Floats, py: Floats) -> Floats:
    a11, a12, a13, a22, a23, a33 = s.inv
    x, y = px - s.cu, py - s.cv
    b = a13 * x + a23 * y
    c = a11 * x * x + 2.0 * a12 * x * y + a22 * y * y - 1.0
    disc = np.maximum(b * b - a33 * c, 0.0)
    res: Floats = s.dc + (-b + np.sqrt(disc)) / a33
    return res


def _tubo(s: SupTubo, px: Floats, py: Floats) -> Floats:
    best = np.full(px.shape, np.inf)
    d = np.full(px.shape, float(s.pts[0][2]))
    for (ax, ay, ad), (bx, by, bd), ra, rb in zip(s.pts, s.pts[1:], s.radii, s.radii[1:], strict=False):
        ex, ey = float(bx - ax), float(by - ay)
        len2 = ex * ex + ey * ey
        t = np.zeros(px.shape) if len2 == 0 else np.clip(((px - ax) * ex + (py - ay) * ey) / len2, 0.0, 1.0)
        qx, qy = px - (ax + t * ex), py - (ay + t * ey)
        perp2 = qx * qx + qy * qy
        r = ra + (rb - ra) * t
        seg = ad + (bd - ad) * t + np.sqrt(np.maximum(r * r - perp2, 0.0))
        take = perp2 < best
        best = np.where(take, perp2, best)
        d = np.where(take, seg, d)
    return d


def _leque(s: SupLeque, mask: Mascara, px: Floats, py: Floats) -> Floats:
    pts = s.pts
    d = np.full(mask.shape, float(sum(p[2] for p in pts)) / len(pts))
    done = np.zeros(mask.shape, dtype=bool)
    x0, y0, z0 = (float(v) for v in pts[0])
    for p1, p2 in zip(pts[1:], pts[2:], strict=False):
        x1, y1, z1 = (float(v) for v in p1)
        x2, y2, z2 = (float(v) for v in p2)
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if den == 0:
            continue
        l0 = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / den
        l1 = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / den
        l2 = 1.0 - l0 - l1
        inside = (l0 >= 0) & (l1 >= 0) & (l2 >= 0) & ~done
        d = np.where(inside, l0 * z0 + l1 * z1 + l2 * z2, d)
        done |= inside
    if (mask & ~done).any():
        near = np.full(mask.shape, np.inf)
        for x, y, z in pts:
            dist = (px - x) ** 2 + (py - y) ** 2
            upd = mask & ~done & (dist < near)
            near = np.where(upd, dist, near)
            d = np.where(upd, float(z), d)
    return d


def depth_map(surface: Superficie, mask: Mascara) -> npt.NDArray[np.int64]:
    """A profundidade quantizada (1/16 px) nos pixels de ``mask``; fora dela, um valor qualquer."""
    h, w = mask.shape
    if isinstance(surface, SupPlana):
        d = np.full((h, w), float(surface.d))
    elif isinstance(surface, SupElipsoide):
        d = _elipsoide(surface, *_grid(w, h))
    elif isinstance(surface, SupTubo):
        d = _tubo(surface, *_grid(w, h))
    else:
        d = _leque(surface, mask, *_grid(w, h))
    res: npt.NDArray[np.int64] = np.floor(d * (DEPTH_QUANT / 256.0) + 0.5).astype(np.int64)
    return res
