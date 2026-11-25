"""O render indexado: a cena 2D vira o quadro (índices de paleta, alfa, dono de cada pixel e os pontos do jogo).

Passes: a luz pela normal na face chapada → as máscaras e o z-buffer → o tom de cada peça → a sombra entre peças →
o contorno interno → o contorno externo por dentro → a sombra no chão → o recorte (medindo o que passa do canvas) →
a limpeza de cor isolada.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from functools import partial

import numpy as np
import numpy.typing as npt

from ..views.camera import LUZ
from ..views.primitivas import Scene2D
from .contorno import contorno_externo, contorno_interno
from .estilo import EstiloRender
from .grade import MARGIN, Mascara, shift
from .limpeza import MANTER, limpar_isolados
from .luz import lambert_permille, pela_normal
from .montagem import Buf16, Camadas, compor, sombra_de_cima, tabelas
from .sombra import sombra_entre_pecas, sombra_no_chao
from .tons import sombrear


@dataclass
class Quadro:
    width: int
    height: int
    index: Buf16
    alpha: npt.NDArray[np.uint8]
    landmarks: dict[str, tuple[int, int]]  # q8 de tela
    clipping_px: int = 0
    overflow_px: tuple[int, int, int, int] = (0, 0, 0, 0)  # quanto passa de cada borda (esq, cima, dir, baixo)
    part_table: list[str] = field(default_factory=list)
    visiveis: dict[str, int] = field(default_factory=dict)  # os pixels de que cada parte é dona, já com a oclusão
    na_silhueta: dict[str, int] = field(default_factory=dict)  # deles, os que tocam o vazio (a borda da figura)

    def to_rgba(self, palette: dict[int, tuple[int, int, int, int]]) -> npt.NDArray[np.uint8]:
        lut = np.zeros((65536, 4), dtype=np.uint8)
        for i, c in palette.items():
            lut[i] = c
        rgba: npt.NDArray[np.uint8] = lut[self.index]
        rgba[..., 3] = np.where(self.alpha == 255, rgba[..., 3], 0)
        return rgba


def mascaras(scene: Scene2D, est: EstiloRender, width: int, height: int) -> dict[str, Mascara]:
    """A máscara inteira de cada parte no canvas, sem a oclusão: a forma de cada uma, para medir."""
    cam = compor(scene, est.materials, width, height)
    return {p: m[MARGIN:MARGIN + height, MARGIN:MARGIN + width] for p, m in cam.full.items()}


def _contar(cam: Camadas, onde: Mascara) -> dict[str, int]:
    """Os pixels de ``onde`` de que cada parte é dona (só as que têm algum)."""
    n = np.bincount(cam.part[onde], minlength=len(cam.num) + 1)
    return {p: int(n[k]) for p, k in cam.num.items() if n[k]}


def _borda(figura: Mascara) -> Mascara:
    """Os pixels da figura com um vizinho vazio (em cima, embaixo ou dos lados)."""
    cheio: Mascara = shift(figura, 1, 0) & shift(figura, -1, 0) & shift(figura, 0, 1) & shift(figura, 0, -1)
    return figura & ~cheio


def _recorte(est: EstiloRender, cam: Camadas, scene: Scene2D,
             bufs: tuple[Buf16, npt.NDArray[np.uint8], Mascara], material: Buf16) -> Quadro:
    """O quadro recortado do canvas, limpo das cores isoladas (``bufs``: os índices, o alfa e a sombra no chão)."""
    index, alpha, chao = bufs
    width, height = cam.width, cam.height
    inside = np.zeros(alpha.shape, dtype=bool)
    inside[MARGIN:MARGIN + height, MARGIN:MARGIN + width] = True
    outside = (alpha == 255) & ~inside
    crop = (slice(MARGIN, MARGIN + height), slice(MARGIN, MARGIN + width))
    landmarks = {k: (u, v) for k, (u, v, _d) in scene.landmarks.items()}
    q = Quadro(width, height, index[crop].copy(), alpha[crop].copy(), landmarks, int(outside.sum()),
               part_table=cam.part_ids)
    if q.clipping_px:
        ys, xs = np.nonzero(alpha == 255)
        q.overflow_px = (max(0, MARGIN - int(xs.min())), max(0, MARGIN - int(ys.min())),
                         max(0, int(xs.max()) - (MARGIN + width - 1)), max(0, int(ys.max()) - (MARGIN + height - 1)))
    lut = np.zeros(len(cam.cmds) + 1, dtype=bool)
    for p, c in cam.cmds.items():
        lut[cam.num[p]] = bool(MANTER & set(c.tags))
    # a sombra no chão não é da figura: para a limpeza ela é vazio (o pixel da borda não fica "dentro da massa")
    limpar_isolados(est, q.index, np.where(chao[crop], 0, q.alpha), material[crop], lut[cam.part[crop]])
    figura = cam.part != 0
    q.visiveis, q.na_silhueta = _contar(cam, inside & figura), _contar(cam, inside & _borda(figura))
    return q


def render(scene: Scene2D, est: EstiloRender, width: int, height: int) -> Quadro:
    scene = replace(scene, commands=pela_normal(scene.commands, est.doc.materials,
                                                partial(lambert_permille, LUZ)))
    cam = compor(scene, est.materials, width, height)
    t = tabelas(cam, est.materials)
    index = np.zeros(cam.part.shape, dtype=np.uint16)
    sombrear(est, cam, index, sombra_de_cima(cam, t, est.sx, est.sy))
    sombra_entre_pecas(est, cam, t, index)
    fill = index.copy()  # o tom de cada pixel antes das linhas (a limpeza pixel-perfect volta a ele)
    inner = contorno_interno(cam, t, index)
    alpha = np.where(cam.part != 0, 255, 0).astype(np.uint8)
    contorno_externo(est, cam, t, (index, alpha, fill), inner)
    chao = sombra_no_chao(est, cam, scene, index, alpha) if scene.chao else np.zeros(alpha.shape, dtype=bool)
    return _recorte(est, cam, scene, (index, alpha, chao), t.material[cam.part])
