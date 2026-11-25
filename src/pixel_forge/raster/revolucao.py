"""O sólido de revolução na tela: a silhueta, a normal e as coordenadas da superfície por pixel, e o tom de cada pixel.

Cada estação chega projetada: o centro (u, v) e a profundidade em px de tela, o raio ``r`` e a altura ``z`` no mundo.
A seção de raio ``r`` aparece como elipse ``r`` em x e ``r·sd`` em y, e avança ``r·ce`` para a câmera. A superfície é
amostrada (os anéis da metade da frente e o disco da tampa) e cada pixel fica com a amostra mais perto da câmera:
a base sai em arco, o topo em tampa oval, e a textura posta no arco e na altura segue a curva.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import numpy.typing as npt

from ..contracts.estilo import MaterialDef
from .grade import MARGIN, Mascara, NaJanela
from .textura import Floats, Indices, quantize, texture_at

STEP_PX = 0.35  # o espaço máximo entre as amostras na tela: menos de meio pixel, sem furos
CYL_LIGHT = (-0.42, 0.91)  # a luz em (lado, frente); o sinal do lado vem do estilo
CAP_LIGHT = 0.88  # a tampa (normal para cima) recebe luz forte, abaixo do destaque do lado
Estacao = tuple[float, float, float, float, float]


@dataclass(frozen=True)
class RevolutionSurface:
    mask: Mascara
    z: Floats  # a altura no mundo (px)
    arc: Floats  # o arco desde a borda esquerda (px)
    nx: Floats  # a normal no plano: lado (direita +)
    nf: Floats  # a normal no plano: frente (para a câmera +)
    cap: Mascara  # o pixel da tampa


def _aneis(stations: tuple[Estacao, ...]) -> list[Estacao]:
    us, vs, ds, rs, zs = (np.array(c, dtype=np.float64) for c in zip(*stations, strict=True))
    rings: list[Estacao] = []
    for i in range(len(stations) - 1):
        n = max(1, math.ceil(max(abs(vs[i + 1] - vs[i]), abs(us[i + 1] - us[i]), abs(rs[i + 1] - rs[i])) / STEP_PX))
        for k in range(n):
            t = k / n
            a = [float(c[i] + (c[i + 1] - c[i]) * t) for c in (us, vs, ds, rs, zs)]
            rings.append((a[0], a[1], a[2], a[3], a[4]))
    rings.append((float(us[-1]), float(vs[-1]), float(ds[-1]), float(rs[-1]), float(zs[-1])))
    return rings


def _amostras(rings: list[Estacao], sd: float, ce: float) -> list[list[npt.NDArray[np.float64]]]:
    """As amostras (u, v, d, z, arco, nx, nf, tampa) da metade da frente de cada anel e do disco da tampa."""
    cols: list[list[npt.NDArray[np.float64]]] = [[] for _ in range(8)]
    for u, v, d, r, z in rings:  # θ de 0 = direita a π = esquerda
        m = max(3, math.ceil(math.pi * max(r, 0.5) / STEP_PX))
        th = np.linspace(0.0, math.pi, m)
        c, s = np.cos(th), np.sin(th)
        for col, val in zip(cols, (u + r * c, v + r * s * sd, d + r * s * ce, np.full(m, z), r * (math.pi - th), c, s,
                                   np.zeros(m)), strict=True):
            col.append(val)
    u, v, d, r, z = rings[-1]  # a tampa, um fio acima para ganhar dos anéis
    g = np.arange(-r, r + STEP_PX, STEP_PX)
    gx, gy = np.meshgrid(g, g)
    inside = gx * gx + gy * gy <= r * r
    gx, gy = gx[inside], gy[inside]
    for col, val in zip(cols, (u + gx, v + gy * sd, d + gy * ce + 1e-3, np.full(gx.size, z),
                               r * (math.pi - np.arctan2(np.maximum(gy, 0.0), gx)), np.zeros(gx.size),
                               np.zeros(gx.size), np.ones(gx.size)), strict=True):
        col.append(val)
    return cols


@lru_cache(maxsize=64)
def surface(stations: tuple[Estacao, ...], sd: float, ce: float, w: int, h: int) -> RevolutionSurface:
    """``stations``: (u, v, profundidade, r, z) em px, de baixo para cima."""
    U, V, D, Z, A, NX, NF, C = (np.concatenate(c) for c in _amostras(_aneis(stations), sd, ce))
    px = np.floor(U).astype(np.int64) + MARGIN
    py = np.floor(V).astype(np.int64) + MARGIN
    ok = (px >= 0) & (px < w) & (py >= 0) & (py < h)
    order = np.lexsort((D[ok], py[ok], px[ok]))  # por pixel, a mais perto por último
    idx = np.flatnonzero(ok)[order]
    key = py[idx] * w + px[idx]
    sel = idx[np.r_[key[1:] != key[:-1], True]]
    yy, xx = py[sel], px[sel]
    mask = np.zeros((h, w), bool)
    mask[yy, xx] = True
    mapas = []
    for val in (Z, A, NX, NF):
        m = np.zeros((h, w))
        m[yy, xx] = val[sel]
        mapas.append(m)
    capm = np.zeros((h, w), bool)
    capm[yy, xx] = C[sel].astype(bool)
    return RevolutionSurface(mask, mapas[0], mapas[1], mapas[2], mapas[3], capm)


def revolution_indices(sf: RevolutionSurface, ce: float, pj: NaJanela, mat: MaterialDef, side: int) -> Indices:
    """O tom de cada pixel pela normal real (lado: o ângulo no anel; tampa: para cima), com a textura posta no arco e
    na altura como aparece na tela (z·cos), então o sulco segue a curva com o período em px do material."""
    win = pj.win
    cap = sf.cap[win]
    lx, lz = CYL_LIGHT
    s = np.where(cap, CAP_LIGHT, (abs(lx) * side) * sf.nx[win] + lz * sf.nf[win])
    arco, alto = np.floor(sf.arc[win]), -np.floor(sf.z[win] * ce)
    em_pe = mat.texture is not None and mat.texture.grain == "along"
    veio = texture_at(alto, arco, mat.texture) if em_pe else texture_at(arco, alto, mat.texture)
    s = s + veio * np.where(cap, 0.5, 1.0)
    res: Indices = np.where(pj.mask, quantize(s, list(mat.ramp), pj.cast), 0).astype(np.uint16)
    return res
