"""A máscara de cada primitiva projetada no quadro com margem."""

from __future__ import annotations

import numpy as np

from ..views.primitivas import EllipsePrim, FanPrim, Prim, RevolutionPrim
from .formas import Pontos, raster_bresenham, raster_ellipse, raster_polygon
from .grade import MARGIN, Mascara
from .revolucao import surface


def _draw_path(mask: Mascara, points: Pontos, closed: bool) -> Mascara:
    """Une à máscara a linha de Bresenham pelo perímetro: a forma fina não se fragmenta em pixels soltos."""
    h, w = mask.shape
    pts = [((x >> 8) + MARGIN, (y >> 8) + MARGIN) for x, y in points]
    segs = list(zip(pts, pts[1:], strict=False)) + ([(pts[-1], pts[0])] if closed else [])
    out = mask.copy()
    for (x0, y0), (x1, y1) in segs:
        for x, y in raster_bresenham(x0, y0, x1, y1):
            if 0 <= x < w and 0 <= y < h:
                out[y, x] = True
    return out


def _leque(prim: FanPrim, w: int, h: int) -> Mascara:
    out = np.zeros((h, w), dtype=bool)
    p0 = prim.points[0]
    for a, b in zip(prim.points[1:], prim.points[2:], strict=False):
        out |= raster_polygon(w, h, MARGIN, (p0, a, b))
    return _draw_path(out, prim.points, closed=True)


def rasterize(prim: Prim, w: int, h: int) -> Mascara:
    if isinstance(prim, EllipsePrim):
        return raster_ellipse(w, h, MARGIN, (prim.cu, prim.cv), (prim.hu, prim.hv))
    if isinstance(prim, RevolutionPrim):
        return surface(prim.stations, prim.sd, prim.ce, w, h).mask.copy()
    return _leque(prim, w, h)


def prim_center(prim: Prim) -> tuple[int, int]:
    if isinstance(prim, EllipsePrim):
        return prim.cu, prim.cv
    pts = prim.points
    return sum(p[0] for p in pts) // len(pts), sum(p[1] for p in pts) // len(pts)
