"""A rasterização inteira das formas em q8, pela amostra no centro do pixel (sem antialiasing).

- Um pixel (x, y) é coberto se o centro dele (256x+128, 256y+128) pertence à forma.
- Elipse: (dx·hv)² + (dy·hu)² <= (hu·hv)², a fronteira inclusiva.
- Cápsula: distância ao segmento <= raio, a fronteira inclusiva.
- Membro afunilado: por segmento, distância perpendicular <= o raio interpolado, mais os discos das pontas.
- Polígono: scanline par-ímpar; a aresta entra em y0 <= yc < y1 e o intervalo horizontal é [x_esq, x_dir): a borda
  compartilhada tem um dono só.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import cmp_to_key
from math import isqrt

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


def raster_oriented_ellipse(w: int, h: int, o: int, centro: tuple[int, int], forma: tuple[int, int, int]) -> Mascara:
    """A elipse girada: x dentro ⇔ xᵀ·adj(M)·x ≤ det(M), com M a forma 2×2 (q8²). Degenerada (det ≤ 0): vazia (o
    render cobre o pixel do centro, como em toda primitiva menor que a grade)."""
    cu, cv = centro
    muu, muv, mvv = forma
    det = muu * mvv - muv * muv
    if det <= 0:
        return np.zeros((h, w), dtype=bool)
    ru, rv = isqrt(max(muu, 0)) + 1, isqrt(max(mvv, 0)) + 1

    def cheia(ww: int, hh: int, ux: int, uy: int) -> Mascara:
        xs, ys = _centers(ww, hh, ux, uy)
        dx = (xs - cu)[None, :]
        dy = (ys - cv)[:, None]
        res: Mascara = dx * dx * mvv - 2 * dx * dy * muv + dy * dy * muu <= det
        return res

    return _windowed(w, h, o, (cu - ru, cu + ru, cv - rv, cv + rv), cheia)


def _span(points: Pontos, pad: int) -> tuple[int, int, int, int]:
    us = [x for x, _ in points]
    vs = [y for _, y in points]
    return min(us) - pad, max(us) + pad, min(vs) - pad, max(vs) + pad


def _capsula_cheia(w: int, h: int, o: tuple[int, int], points: Pontos, radius: int) -> Mascara:
    xs, ys = _centers(w, h, o[0], o[1])
    px = np.broadcast_to(xs[None, :], (h, w))
    py = np.broadcast_to(ys[:, None], (h, w))
    out = np.zeros((h, w), dtype=bool)
    r2 = radius * radius
    for (ax, ay), (bx, by) in zip(points, points[1:], strict=False):
        ex, ey = bx - ax, by - ay
        len2 = ex * ex + ey * ey
        qx, qy = px - ax, py - ay
        d_a = qx * qx + qy * qy
        if len2 == 0:
            out |= d_a <= r2
            continue
        dot = qx * ex + qy * ey
        rx, ry = px - bx, py - by
        cross = qx * ey - qy * ex
        mid = (dot > 0) & (dot < len2) & (cross * cross <= r2 * len2)  # cross² <= r²·len2 é dist² <= r² no meio
        out |= mid | ((dot <= 0) & (d_a <= r2)) | ((dot >= len2) & (rx * rx + ry * ry <= r2))
    return out


def raster_capsule(w: int, h: int, o: int, points: Pontos, radius: int) -> Mascara:
    return _windowed(w, h, o, _span(points, abs(radius)),
                     lambda ww, hh, ux, uy: _capsula_cheia(ww, hh, (ux, uy), points, radius))


def _afunilada_cheia(w: int, h: int, o: tuple[int, int], points: Pontos, radii: tuple[int, ...]) -> Mascara:
    """Em quartos de pixel (q2), para caber em int64 sem perder o centro do pixel (4x+2 exato):
    cross² · len2 <= (ra · len2 + (rb − ra) · dot)² com 0 < dot < len2; os pontos e raios arredondados para q2."""
    xs, ys = _centers(w, h, o[0], o[1])
    px = np.broadcast_to((xs // 64)[None, :], (h, w))
    py = np.broadcast_to((ys // 64)[:, None], (h, w))
    pts = [((x + 32) >> 6, (y + 32) >> 6) for x, y in points]
    rs = [(r + 32) >> 6 for r in radii]
    out = np.zeros((h, w), dtype=bool)
    for (ax, ay), (bx, by), ra, rb in zip(pts, pts[1:], rs, rs[1:], strict=False):
        qx, qy = px - ax, py - ay
        rx, ry = px - bx, py - by
        out |= (qx * qx + qy * qy <= ra * ra) | (rx * rx + ry * ry <= rb * rb)
        ex, ey = bx - ax, by - ay
        len2 = ex * ex + ey * ey
        if len2 == 0:
            continue
        dot = qx * ex + qy * ey
        cross = qx * ey - qy * ex
        lim = ra * len2 + (rb - ra) * dot
        out |= (dot > 0) & (dot < len2) & (lim > 0) & (cross * cross * len2 <= lim * lim)
    return out


def raster_tapered(w: int, h: int, o: int, points: Pontos, radii: tuple[int, ...]) -> Mascara:
    pad = max((abs(r) for r in radii), default=0) + 64  # um q2 de folga pelo arredondamento dos pontos e raios
    return _windowed(w, h, o, _span(points, pad), lambda ww, hh, ux, uy: _afunilada_cheia(ww, hh, (ux, uy), points,
                                                                                         radii))


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
