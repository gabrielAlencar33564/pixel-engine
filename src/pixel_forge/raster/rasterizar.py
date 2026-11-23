"""A máscara de cada primitiva projetada no quadro com margem."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from ..views.primitivas import (
    CapsulePrim,
    EllipsePrim,
    FanPrim,
    PolygonPrim,
    Prim,
    RevolutionPrim,
    StipplePrim,
    TaperedPrim,
)
from .formas import Pontos, raster_bresenham, raster_capsule, raster_ellipse, raster_polygon, raster_tapered
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


def stipple_mask(prim: StipplePrim, janela: tuple[int, int, int, int]) -> npt.NDArray[np.bool_]:
    """As células acesas do pontilhado na ``janela`` (x0, y0, w, h) do quadro: a célula de ``cell`` px, contada da
    origem projetada da peça, acende quando o hash inteiro de (cx, cy, seed) cai abaixo da densidade (‰). Só aritmética
    de 32 bits: o mesmo em qualquer máquina, e a peça deslocada leva o padrão junto."""
    x0, y0, w, h = janela
    ax, ay = (prim.ou >> 8) + MARGIN, (prim.ov >> 8) + MARGIN
    cx = (np.arange(x0, x0 + w, dtype=np.int64) - ax) // prim.cell
    cy = (np.arange(y0, y0 + h, dtype=np.int64) - ay) // prim.cell
    m32 = 0xFFFFFFFF
    x = (cx[None, :] * 73856093) & m32
    y = (cy[:, None] * 19349663) & m32
    v = (x ^ y ^ ((prim.seed * 83492791) & m32)) & m32
    v ^= v >> 16
    v = (v * 0x7FEB352D) & m32
    v ^= v >> 15
    v = (v * 0x846CA68B) & m32
    v ^= v >> 16
    res: npt.NDArray[np.bool_] = (v % 1000) < prim.density
    return res


def _pontilhado(prim: StipplePrim, w: int, h: int) -> Mascara:
    """O polígono ∩ o pontilhado, com o hash só no retângulo do polígono (fora dele o ``&`` dá falso)."""
    poly = raster_polygon(w, h, MARGIN, prim.points)
    rows = np.flatnonzero(poly.any(axis=1))
    if rows.size == 0:
        return poly
    cols = np.flatnonzero(poly.any(axis=0))
    y0, y1, x0, x1 = int(rows[0]), int(rows[-1]) + 1, int(cols[0]), int(cols[-1]) + 1
    out = np.zeros_like(poly)
    out[y0:y1, x0:x1] = poly[y0:y1, x0:x1] & stipple_mask(prim, (x0, y0, x1 - x0, y1 - y0))
    return out


def rasterize(prim: Prim, w: int, h: int) -> Mascara:
    if isinstance(prim, EllipsePrim):
        return raster_ellipse(w, h, MARGIN, (prim.cu, prim.cv), (prim.hu, prim.hv))
    if isinstance(prim, RevolutionPrim):
        return surface(prim.stations, prim.sd, prim.ce, w, h).mask.copy()
    if isinstance(prim, CapsulePrim):
        return _draw_path(raster_capsule(w, h, MARGIN, prim.points, prim.radius), prim.points, closed=False)
    if isinstance(prim, TaperedPrim):
        return _draw_path(raster_tapered(w, h, MARGIN, prim.points, prim.radii), prim.points, closed=False)
    if isinstance(prim, PolygonPrim):
        return raster_polygon(w, h, MARGIN, prim.points)
    if isinstance(prim, StipplePrim):
        return _pontilhado(prim, w, h)
    return _leque(prim, w, h)


def prim_center(prim: Prim) -> tuple[int, int]:
    if isinstance(prim, EllipsePrim):
        return prim.cu, prim.cv
    pts = prim.points
    return sum(p[0] for p in pts) // len(pts), sum(p[1] for p in pts) // len(pts)
