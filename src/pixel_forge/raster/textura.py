"""A textura do material (``dashes``): sulcos curtos e desencontrados um tom abaixo, às vezes um pixel claro logo
acima, e uma variação fina que quebra a fronteira entre os tons. Tudo em inteiros e hash, contado a partir do canto
da peça: o mesmo dado dá o mesmo pixel, e a peça deslocada leva o padrão junto (sem fervura)."""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

from ..contracts.estilo import MaterialTexture
from .grade import Mascara

Floats = npt.NDArray[np.float64]
Indices = npt.NDArray[np.uint16]
HIGHLIGHT = 0.97  # o limiar do tom mais claro (a luz vai de 0 a 1)


def h32(*arrays: npt.ArrayLike) -> npt.NDArray[np.int64]:
    """Hash inteiro de 32 bits, elemento a elemento."""
    m32 = 0xFFFFFFFF
    primes = (73856093, 19349663, 83492791, 2654435761)
    v: Any = 0
    for a, p in zip(arrays, primes, strict=False):
        v = v ^ ((np.asarray(a, dtype=np.int64) * p) & m32)
    v = np.asarray(v, dtype=np.int64) & m32
    v ^= v >> 16
    v = (v * 0x7FEB352D) & m32
    v ^= v >> 15
    v = (v * 0x846CA68B) & m32
    v ^= v >> 16
    res: npt.NDArray[np.int64] = v
    return res


def _sulco(x: npt.NDArray[np.int64], y: npt.NDArray[np.int64], tex: MaterialTexture) -> npt.NDArray[np.bool_]:
    """Onde a fileira ``y`` tem o traço do sulco (as fileiras a cada ``period_px``, os traços desencontrados)."""
    band = np.floor_divide(y, tex.period_px)
    cell = tex.length_px[1] + 1
    cx = np.floor_divide(x + band * 5, cell)
    on = (h32(band, cx, tex.seed) % 1000) < tex.density_permille
    ln = tex.length_px[0] + (h32(band, cx, tex.seed + 1) % (tex.length_px[1] - tex.length_px[0] + 1))
    res: npt.NDArray[np.bool_] = on & (np.mod(x + band * 5, cell) < ln)
    return res


def texture_at(x: npt.ArrayLike, y: npt.ArrayLike, tex: MaterialTexture | None) -> Floats:
    """O deslocamento de luz (em unidades de 0..1) nas coordenadas inteiras ``x`` (ao longo) e ``y``."""
    off = np.zeros(np.shape(x), dtype=np.float64)
    if tex is None:
        return off
    xi = np.asarray(x, dtype=np.int64)
    yi = np.asarray(y, dtype=np.int64)
    groove = (np.mod(yi, tex.period_px) == 0) & _sulco(xi, yi, tex)
    off -= groove * (tex.depth_permille / 1000)
    lift = (np.mod(yi + 1, tex.period_px) == 0) & _sulco(xi, yi + 1, tex) & (h32(xi, yi, tex.seed + 2) % 3 == 0)
    off += lift * (tex.lift_permille / 1000)
    off += ((h32(xi, yi, tex.seed + 3) % 1000) / 1000 - 0.5) * (tex.jitter_permille / 1000)
    return off


def quantize(s: Floats, ramp: list[int], cast: Mascara | None) -> Indices:
    """A luz (0..1) em ``len(ramp)`` faixas (o primeiro tom é o mais escuro): o mais claro só acima de
    ``HIGHLIGHT``; o pixel na sombra projetada (``cast``) desce um tom."""
    n = len(ramp)
    cuts = [HIGHLIGHT * i / (n - 1) for i in range(1, n)]
    k = np.digitize(s, cuts).astype(np.int64)
    if cast is not None:
        k = np.where(cast, np.maximum(0, k - 1), k)
    lut = np.asarray(ramp, dtype=np.uint16)
    res: Indices = lut[k]
    return res


def flat_texture_indices(mask: Mascara, origem: tuple[int, int], tex: MaterialTexture, mid: int,
                         degraus: tuple[int | None, int | None]) -> Indices:
    """A textura na peça chapada, que não tem rampa: o sulco desce ao degrau de baixo da família do material e a borda
    clara sobe ao de cima; sem o degrau, o pixel fica no tom da peça. O veio corre ao longo do lado comprido da peça,
    contado do canto ``origem`` (x, y) da máscara."""
    h, w = mask.shape
    dark, light = degraus
    ox, oy = origem
    out = np.full((h, w), mid, dtype=np.uint16)
    ys, xs = np.nonzero(mask)
    if ys.size == 0:
        return out
    yy, xx = np.mgrid[0:h, 0:w]
    if (ys.max() - ys.min()) > (xs.max() - xs.min()):  # em pé: o veio ao longo de y
        off = texture_at(yy - oy, xx - ox, tex)
    else:
        off = texture_at(xx - ox, yy - oy, tex)
    if dark is not None and tex.depth_permille:
        out[off <= -tex.depth_permille / 2000] = dark
    if light is not None and tex.lift_permille:
        out[off >= tex.lift_permille / 2000] = light
    res: Indices = np.where(mask, out, mid).astype(np.uint16)
    return res
