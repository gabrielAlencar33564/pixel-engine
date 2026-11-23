"""A conferência de cada quadro do build: nada cortado pelo canvas e as cores dentro do limite do estilo."""

from __future__ import annotations

import numpy as np

from ..contracts.estilo import StyleDoc
from ..core.recusa import Recusa
from ..raster.renderer import Quadro


def conferir_quadro(q: Quadro, style: StyleDoc, nome: str) -> None:
    if q.clipping_px:
        e, c, d, b = q.overflow_px
        raise Recusa("QUADRO_CORTADO", f"{nome}: {q.clipping_px} px do desenho saem do canvas (esquerda {e}, cima {c}, "
                     f"direita {d}, baixo {b}).", "Aumente o canvas ou mova o pivô para o desenho caber.")
    cores = len(np.unique(q.index[q.alpha == 255]))
    if cores > style.max_opaque_colors:
        raise Recusa("CORES_DEMAIS", f"{nome}: {cores} cores opacas, o estilo permite {style.max_opaque_colors}.",
                     "Use menos materiais ou materiais com rampas menores.")
