"""A limpeza de cor isolada: o pixel de uma cor sozinha dentro de uma massa assume a cor dominante dos 4 vizinhos do
mesmo material.

Candidato: pixel opaco, fora de peça intencional (detalhe, olho, sombra no chão), cujo índice não é tinta de
contorno, com os 4 vizinhos opacos e nenhum com o mesmo índice. Substituto: o índice mais frequente entre os vizinhos
do mesmo material que não são contorno (empate: o menor); sem vizinho elegível, o pixel fica. A decisão usa só o
buffer original: nenhuma troca influencia outra.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

from .estilo import EstiloRender
from .montagem import Buf16

MANTER = frozenset({"detail", "pixel_detail", "eye", "ground_shadow"})
VIZINHOS = ((1, 2), (1, 0), (2, 1), (0, 1))  # direita, esquerda, baixo, cima (no buffer com borda)


def _com_borda(a: npt.NDArray[Any], fill: Any) -> npt.NDArray[Any]:
    h, w = a.shape
    out = np.full((h + 2, w + 2), fill, dtype=a.dtype)
    out[1:-1, 1:-1] = a
    return out


class _Vizinhos:
    """Os índices e os materiais dos 4 vizinhos de cada pixel, lidos do buffer original."""

    def __init__(self, index: Buf16, material: Buf16, outline: list[int]) -> None:
        h, w = index.shape
        pi, pm = _com_borda(index, 0), _com_borda(material, 0)
        self.indices = [pi[a:a + h, b:b + w] for a, b in VIZINHOS]
        self.materiais = [pm[a:a + h, b:b + w] for a, b in VIZINHOS]
        self.outline = outline

    def voto(self, y: int, x: int, mat: int) -> int | None:
        votes: dict[int, int] = {}
        for ni, nm in zip(self.indices, self.materiais, strict=True):
            v = int(ni[y, x])
            if int(nm[y, x]) == mat and v not in self.outline:
                votes[v] = votes.get(v, 0) + 1
        return min(votes, key=lambda k: (-votes[k], k)) if votes else None


def limpar_isolados(est: EstiloRender, index: Buf16, alpha: npt.NDArray[np.uint8], material: Buf16,
                    manter: npt.NDArray[np.bool_]) -> None:
    """Aplica a limpeza em ``index`` (o quadro já recortado); ``manter`` marca os pixels das peças intencionais."""
    outline = sorted({m.outline_index for m in est.doc.materials})
    opaque = alpha == 255
    h, w = index.shape
    cand = opaque & ~manter & ~np.isin(index, outline)
    po = _com_borda(opaque, False)
    viz = _Vizinhos(index, material, outline)
    for a, b in VIZINHOS:
        cand &= po[a:a + h, b:b + w]
    for ni in viz.indices:
        cand &= ni != index
    trocas = []
    for y, x in zip(*np.nonzero(cand), strict=True):
        best = viz.voto(int(y), int(x), int(material[y, x]))
        if best is not None:
            trocas.append((int(y), int(x), best))
    for y, x, best in trocas:
        index[y, x] = best
