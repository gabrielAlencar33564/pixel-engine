"""O atlas: os quadros empacotados em prateleiras, na ordem canônica, sem rotação, com 1 px de folga transparente."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ..core.direcoes import DIRECOES
from ..core.recusa import Recusa

MAX_PAGE = 4096
GAP = 1
Rgba = npt.NDArray[np.uint8]


@dataclass(frozen=True)
class QuadroDoAtlas:
    clip: str
    direction: str
    index: int
    rgba: Rgba
    pivot_px: list[int]
    landmarks: dict[str, list[int]]
    duration_ms: int
    events: list[str]


def nome_do_quadro(asset: str, clip: str, direction: str, index: int) -> str:
    return f"{asset}/{clip}/{direction.lower()}/{index:03d}"


def _posicoes(quadros: list[QuadroDoAtlas]) -> tuple[list[tuple[int, int, int]], list[tuple[int, int]]]:
    """A prateleira de cada quadro (página, x, y) e o tamanho de cada página, com a largura perto da raiz da área."""
    total = sum((q.rgba.shape[1] + GAP) * (q.rgba.shape[0] + GAP) for q in quadros)
    alvo = min(MAX_PAGE, max(max(q.rgba.shape[1] for q in quadros) + GAP, math.isqrt(total) + 1))
    pos: list[tuple[int, int, int]] = []
    sizes: list[tuple[int, int]] = []
    page, x, y, shelf, pw, ph = 0, GAP, GAP, 0, 0, 0
    for q in quadros:
        w, h = q.rgba.shape[1], q.rgba.shape[0]
        if x + w + GAP > alvo:
            x, y, shelf = GAP, y + shelf + GAP, 0
        if y + h + GAP > MAX_PAGE:
            sizes.append((pw, ph))
            page, x, y, shelf, pw, ph = page + 1, GAP, GAP, 0, 0, 0
        pos.append((page, x, y))
        x += w + GAP
        shelf = max(shelf, h)
        pw, ph = max(pw, x), max(ph, y + shelf + GAP)
    sizes.append((pw, ph))
    return pos, sizes


def empacotar(asset: str, quadros: list[QuadroDoAtlas]) -> tuple[list[Rgba], list[dict[str, Any]]]:
    """As páginas e a entrada de cada quadro (página, retângulo, canvas de origem, pivô, pontos, duração, eventos)."""
    ordem = {d: i for i, d in enumerate(DIRECOES)}
    quadros = sorted(quadros, key=lambda q: (q.clip, ordem[q.direction], q.index))
    pos, sizes = _posicoes(quadros)
    if any(w > MAX_PAGE or h > MAX_PAGE for w, h in sizes):
        raise Recusa("ATLAS_GRANDE", "Um quadro passa de 4096 px.", "Reduza o canvas do asset.")
    pages = [np.zeros((h, w, 4), dtype=np.uint8) for w, h in sizes]
    entradas = []
    for q, (p, x, y) in zip(quadros, pos, strict=True):
        h, w = q.rgba.shape[:2]
        pages[p][y:y + h, x:x + w] = q.rgba
        entradas.append({"name": nome_do_quadro(asset, q.clip, q.direction, q.index), "page": p, "rect": [x, y, w, h],
                         "source_size": {"width": w, "height": h}, "source_rect": [0, 0, w, h],
                         "pivot_px": q.pivot_px, "landmarks": q.landmarks, "duration_ms": q.duration_ms,
                         "events": q.events})
    return pages, entradas
