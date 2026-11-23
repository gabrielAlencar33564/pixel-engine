"""A grade do render: a margem em volta do canvas, os deslocamentos de buffer e as janelas de máscara."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

MARGIN = 8
Mascara = npt.NDArray[np.bool_]
Janela = tuple[slice, slice]


@dataclass(frozen=True)
class NaJanela:
    """A peça recortada na janela dela: a janela, a máscara completa e o pixel com a sombra de cima."""

    win: Janela
    mask: Mascara
    cast: Mascara


def part_window(mask: Mascara, pad: int) -> Janela | None:
    """A janela (linhas, colunas) da máscara com ``pad`` px de folga, recortada no buffer; ``None`` se vazia. Os
    deslocamentos de até ``pad`` px a partir dela ficam dentro dela ou fora do buffer, então processar só a janela dá o
    mesmo resultado que o quadro inteiro."""
    rows = np.flatnonzero(mask.any(axis=1))
    if rows.size == 0:
        return None
    cols = np.flatnonzero(mask.any(axis=0))
    h, w = mask.shape
    return (slice(max(0, int(rows[0]) - pad), min(h, int(rows[-1]) + pad + 1)),
            slice(max(0, int(cols[0]) - pad), min(w, int(cols[-1]) + pad + 1)))


def shift(a: npt.NDArray[Any], dx: int, dy: int) -> npt.NDArray[Any]:
    """out[y, x] = a[y+dy, x+dx], com zero (ou falso) fora do buffer."""
    out = np.zeros_like(a)
    h, w = a.shape[:2]
    ys = slice(max(0, -dy), min(h, h - dy))
    xs = slice(max(0, -dx), min(w, w - dx))
    yd = slice(max(0, dy), min(h, h + dy))
    xd = slice(max(0, dx), min(w, w + dx))
    out[ys, xs] = a[yd, xd]
    return out


def pixel_perfect(line: Mascara) -> Mascara:
    """Os cantos em L da linha: o pixel com um vizinho de linha na fileira e outro na coluna, e nenhum do lado oposto,
    sobra (os dois já se tocam na diagonal). Em duas passadas de paridade, para não tirar os dois pixels de um
    degrau."""
    line = line.copy()
    drop = np.zeros_like(line)
    yy, xx = np.indices(line.shape)
    for parity in (0, 1):
        le, ri = shift(line, -1, 0), shift(line, 1, 0)
        up, dn = shift(line, 0, -1), shift(line, 0, 1)
        corner = line & ((le ^ ri) & (up ^ dn)) & ((xx + yy) % 2 == parity)
        diag = (le & up & shift(line, -1, -1)) | (le & dn & shift(line, -1, 1)) \
            | (ri & up & shift(line, 1, -1)) | (ri & dn & shift(line, 1, 1))
        corner &= ~diag  # o canto cheio (bloco 2×2) não é degrau
        drop |= corner
        line &= ~corner
    return drop
