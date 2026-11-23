"""A rasterização inteira das formas em q8, pela amostra no centro do pixel (sem antialiasing).

- Um pixel (x, y) é coberto se o centro dele (256x+128, 256y+128) pertence à forma.
- Elipse: (dx·hv)² + (dy·hu)² <= (hu·hv)², a fronteira inclusiva.
- Polígono: scanline par-ímpar; a aresta entra em y0 <= yc < y1 e o intervalo horizontal é [x_esq, x_dir): a borda
  compartilhada tem um dono só.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import cmp_to_key

import numpy as np
import numpy.typing as npt

from .grade import Mascara

Inteiros = npt.NDArray[np.int64]
Pontos = tuple[tuple[int, int], ...]


def _windowed(w: int, h: int, o: int, limites: tuple[int, int, int, int],
              fn: Callable[[int, int, int, int], Mascara]) -> Mascara:
    """Rasteriza só na janela dos pixels cujos centros caem nos ``limites`` (q8: u mín, u máx, v mín, v máx, com 1 px
    de folga) e devolve a máscara do quadro inteiro. Os centros da janela são os do quadro (o deslocamento entra na
    origem), então o resultado é o mesmo; muda só o tamanho dos arrays temporários."""
    lo_u, hi_u, lo_v, hi_v = limites
    x0 = max(0, (lo_u - 128) // 256 + o - 1)
    x1 = min(w, -((128 - hi_u) // 256) + o + 2)
    y0 = max(0, (lo_v - 128) // 256 + o - 1)
    y1 = min(h, -((128 - hi_v) // 256) + o + 2)
    out = np.zeros((h, w), dtype=bool)
    if x1 > x0 and y1 > y0:
        out[y0:y1, x0:x1] = fn(x1 - x0, y1 - y0, o - x0, o - y0)
    return out


def _centers(w: int, h: int, ox: int, oy: int) -> tuple[Inteiros, Inteiros]:
    xs = (np.arange(w, dtype=np.int64) - ox) * 256 + 128
    ys = (np.arange(h, dtype=np.int64) - oy) * 256 + 128
    return xs, ys


def raster_ellipse(w: int, h: int, o: int, centro: tuple[int, int], semi: tuple[int, int]) -> Mascara:
    cu, cv = centro
    hu, hv = max(semi[0], 1), max(semi[1], 1)

    def cheia(ww: int, hh: int, ux: int, uy: int) -> Mascara:
        xs, ys = _centers(ww, hh, ux, uy)
        dx = (xs - cu)[None, :]
        dy = (ys - cv)[:, None]
        res: Mascara = (dx * dx) * (hv * hv) + (dy * dy) * (hu * hu) <= (hu * hu) * (hv * hv)
        return res

    return _windowed(w, h, o, (cu - hu, cu + hu, cv - hv, cv + hv), cheia)


def raster_polygon(w: int, h: int, o: int, points: Pontos) -> Mascara:
    if not points:
        return np.zeros((h, w), dtype=bool)
    us = [x for x, _ in points]
    vs = [y for _, y in points]
    return _windowed(w, h, o, (min(us), max(us), min(vs), max(vs)),
                     lambda ww, hh, ux, uy: _polygon_full(ww, hh, ux, uy, points))


def _cmp_fraction(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Compara num/den exatamente (den > 0)."""
    return (a[0] * b[1] > b[0] * a[1]) - (a[0] * b[1] < b[0] * a[1])


def _crossings(points: Pontos, yc: int) -> list[tuple[int, int]]:
    """Os x (frações num/den, den > 0) onde as arestas cortam a fileira de centro ``yc``, em ordem."""
    out = []
    n = len(points)
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        if y0 == y1:
            continue
        if y0 > y1:
            x0, y0, x1, y1 = x1, y1, x0, y0
        if y0 <= yc < y1:
            out.append((x0 * (y1 - y0) + (yc - y0) * (x1 - x0), y1 - y0))
    out.sort(key=cmp_to_key(_cmp_fraction))
    return out


def _polygon_full(w: int, h: int, ox: int, oy: int, points: Pontos) -> Mascara:
    out = np.zeros((h, w), dtype=bool)
    xs, ys = _centers(w, h, ox, oy)
    for row in range(h):
        crossings = _crossings(points, int(ys[row]))
        for k in range(0, len(crossings) - 1, 2):
            ln, ld = crossings[k]
            rn, rd = crossings[k + 1]
            out[row] |= (xs * ld >= ln) & (xs * rd < rn)
    return out


def raster_bresenham(x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
    """A linha inteira de Bresenham (todas as octantes, com as pontas)."""
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            return pts
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
