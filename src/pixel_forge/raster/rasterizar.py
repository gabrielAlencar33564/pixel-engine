"""A máscara de cada primitiva projetada no quadro com margem."""

from __future__ import annotations

import numpy as np

from ..views.primitivas import (
    CapsulePrim,
    EllipsePrim,
    FanPrim,
    OrientedEllipsePrim,
    Prim,
    RevolutionPrim,
    TaperedPrim,
)
from .formas import (
    Pontos,
    raster_bresenham,
    raster_capsule,
    raster_ellipse,
    raster_oriented_ellipse,
    raster_polygon,
    raster_tapered,
)
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
    if isinstance(prim, OrientedEllipsePrim):
        return raster_oriented_ellipse(w, h, MARGIN, (prim.cu, prim.cv), (prim.muu, prim.muv, prim.mvv))
    if isinstance(prim, RevolutionPrim):
        return surface(prim.stations, prim.sd, prim.ce, w, h).mask.copy()
    if isinstance(prim, CapsulePrim):
        return _draw_path(raster_capsule(w, h, MARGIN, prim.points, prim.radius), prim.points, closed=False)
    if isinstance(prim, TaperedPrim):
        return _draw_path(raster_tapered(w, h, MARGIN, prim.points, prim.radii), prim.points, closed=False)
    return _leque(prim, w, h)


def prim_center(prim: Prim) -> tuple[int, int]:
    if isinstance(prim, EllipsePrim | OrientedEllipsePrim):
        return prim.cu, prim.cv
    pts = prim.points
    return sum(p[0] for p in pts) // len(pts), sum(p[1] for p in pts) // len(pts)
