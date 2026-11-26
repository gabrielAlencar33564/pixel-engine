"""A montagem do quadro: a máscara de cada peça, o z-buffer por superfície, as regras frente/trás, a ordem por pixel
e as tabelas por número de peça que os passes leem."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import numpy.typing as npt

from ..contracts.estilo import MaterialDef
from ..core.recusa import Recusa
from ..views.primitivas import DrawCommand, Scene2D
from .grade import MARGIN, Mascara, shift
from .profundidade import DEPTH_QUANT, depth_map
from .rasterizar import prim_center, rasterize
from .textura import h32

DETAIL_DEPTH_MARGIN_PX = 2  # o detalhe e a face chapada vencem a superfície a até 2 px à frente deles
BORDA_DE_FOLHA = "borda_de_folha"  # a marca do volume de folhagem: a beira da máscara dele sai recortada em folhas
FOLHA_PARTE = 420  # as células da beira que saem na folhagem (‰)
FOLHA_GRANDE = 150  # a máscara com esta área (px) ou mais tem a folha de 2 px; a menor, de 1 px
FOLHA_AREA_MINIMA = 24  # a máscara menor que isto (px) não se recorta
Buf16 = npt.NDArray[np.uint16]
Buf32 = npt.NDArray[np.int32]
Buf64 = npt.NDArray[np.int64]


@dataclass
class Camadas:
    """O quadro com margem em montagem: as máscaras completas das peças, o dono de cada pixel (``part``), a
    profundidade e a ordem por pixel."""

    width: int
    height: int
    cmds: dict[str, DrawCommand]
    num: dict[str, int]
    full: dict[str, Mascara]
    part: Buf16
    zbuf: Buf64
    order: Buf32 = field(default_factory=lambda: np.zeros((0, 0), np.int32))
    massa: dict[str, Mascara] = field(default_factory=dict)  # a união das máscaras do grupo ``shade_group``

    @property
    def part_ids(self) -> list[str]:
        return sorted(self.cmds)


def sorteadas(m: Mascara, celula: int, parte: int) -> Mascara:
    """As células de ``celula`` px de lado sorteadas (``parte`` ‰), contadas do canto da máscara ``m``: a peça
    deslocada leva o sorteio junto."""
    ys, xs = np.nonzero(m)
    yy, xx = np.indices(m.shape)
    res: Mascara = h32((xx - int(xs.min())) // celula, (yy - int(ys.min())) // celula, 7) % 1000 < parte
    return res


def _recortada(m: Mascara, faixa: int, parte: int) -> Mascara:
    """A beira recortada: da faixa de ``faixa`` px junto à borda da máscara saem ``parte`` ‰ das células de
    ``faixa`` px de lado, sorteadas. O que está atrás (o miolo escuro, o lóbulo de baixo, o chão) aparece nos vãos."""
    dentro = m
    for _ in range(faixa):
        dentro = dentro & shift(dentro, 1, 0) & shift(dentro, -1, 0) & shift(dentro, 0, 1) & shift(dentro, 0, -1)
    res: Mascara = m & ~(~dentro & sorteadas(m, faixa, parte))
    return res


def _mascara(c: DrawCommand, w: int, h: int) -> Mascara:
    m = rasterize(c.prim, w, h)
    area = int(m.sum())
    if BORDA_DE_FOLHA in c.tags and area >= FOLHA_AREA_MINIMA:  # a folha da peça pequena é de 1 px; a da grande, de 2
        m = _recortada(m, 2 if area >= FOLHA_GRANDE else 1, FOLHA_PARTE)
    if not m.any():  # a primitiva menor que a grade cobre o pixel do centro projetado, em vez de sumir
        cu, cv = prim_center(c.prim)
        x, y = (cu >> 8) + MARGIN, (cv >> 8) + MARGIN
        if 0 <= x < w and 0 <= y < h:
            m[y, x] = True
    return m


def compor(scene: Scene2D, materials: dict[str, MaterialDef], width: int, height: int) -> Camadas:
    """As máscaras e o z-buffer: o comando posterior vence o empate, como na ordem de desenho."""
    W, H = width + 2 * MARGIN, height + 2 * MARGIN
    cmds = {c.part_id: c for c in scene.commands}
    num = {p: i + 1 for i, p in enumerate(sorted(cmds))}
    cam = Camadas(width, height, cmds, num, {}, np.zeros((H, W), np.uint16),
                  np.full((H, W), np.iinfo(np.int64).min, dtype=np.int64))
    dmaps: dict[str, Buf64] = {}
    for c in scene.commands:
        if c.material not in materials:
            raise Recusa("MATERIAL_AUSENTE", f"A peça '{c.part_id}' usa o material '{c.material}', que o estilo não "
                         "tem.", "Use um material do estilo (`pfe catalogo` lista os materiais).")
        m = _mascara(c, W, H)
        cam.full[c.part_id] = m
        dm = depth_map(c.surface, m) + scene.depth_bias_q8.get(c.part_id, 0) * DEPTH_QUANT // 256
        marca = DETAIL_DEPTH_MARGIN_PX * DEPTH_QUANT if "detail" in c.tags or "flat" in c.tags else 0
        dmaps[c.part_id] = dm + marca
        take = m & (dm + marca >= cam.zbuf)
        cam.part[take] = num[c.part_id]
        cam.zbuf[take] = np.maximum(dm[take], cam.zbuf[take]) if marca else dm[take]  # a real, nunca a margem
    for front, back in scene.front_back:  # as regras ativas valem por cima do z-buffer
        if front in dmaps and back in cam.full:
            sel = cam.full[front] & (cam.part == num[back])
            cam.part[sel] = num[front]
            cam.zbuf[sel] = np.maximum(cam.zbuf[sel], dmaps[front][sel])
    for g in sorted({c.group for c in cmds.values()}):
        membros = [p for p, c in cmds.items() if c.group == g and "shade_group" in c.tags]
        if len(membros) > 1:
            uniao: Mascara = np.logical_or.reduce([cam.full[p] for p in membros])
            cam.massa.update({p: uniao for p in membros})
    opaque_z = cam.zbuf[cam.part != 0]
    zmin = int(opaque_z.min()) if opaque_z.size else 0
    cam.order = np.where(cam.part != 0, cam.zbuf - zmin + 1, 0).astype(np.int32)
    return cam


@dataclass(frozen=True)
class Tabelas:
    """Os valores de cada peça por número (0 = vazio), para os passes vetorizados."""

    outline: Buf16  # a tinta do contorno do material
    ramp0: Buf16  # o tom mais escuro da rampa
    ramp3: npt.NDArray[np.bool_]  # a rampa tem 3 tons ou mais (o sel-out pinta o lado da luz com o tom 0)
    material: Buf16
    group: Buf32
    detail: npt.NDArray[np.bool_]
    no_outline: npt.NDArray[np.bool_]
    no_inner: npt.NDArray[np.bool_]
    no_cast: npt.NDArray[np.bool_]


def tabelas(cam: Camadas, materials: dict[str, MaterialDef]) -> Tabelas:
    n = len(cam.cmds) + 1
    groups = sorted({c.group for c in cam.cmds.values()})
    mat_num = {m: i + 1 for i, m in enumerate(sorted(materials))}
    t = Tabelas(np.zeros(n, np.uint16), np.zeros(n, np.uint16), np.zeros(n, bool), np.zeros(n, np.uint16),
                np.zeros(n, np.int32), np.zeros(n, bool), np.zeros(n, bool), np.zeros(n, bool), np.zeros(n, bool))
    for p, c in cam.cmds.items():
        k, mat = cam.num[p], materials[c.material]
        t.outline[k], t.ramp0[k], t.ramp3[k] = mat.outline_index, mat.ramp[0], len(mat.ramp) >= 3
        t.material[k] = mat_num[c.material]
        t.group[k] = groups.index(c.group) + 1
        t.detail[k] = "detail" in c.tags
        t.no_outline[k] = "no_outline" in c.tags
        t.no_inner[k] = "no_inner_outline" in c.tags
        t.no_cast[k] = "no_cast" in c.tags
    return t


def sombra_de_cima(cam: Camadas, t: Tabelas, sx: int, sy: int) -> Mascara:
    """O pixel cujo vizinho na direção da luz é uma peça da frente de outro grupo (nem detalhe nem ``no_cast``)."""
    dx, dy = -sx if sx else 0, -sy if sy else -1
    above_part = shift(cam.part, dx, dy)
    above_order = shift(cam.order, dx, dy)
    res: Mascara = (above_part != 0) & (above_part != cam.part) & (above_order > cam.order) \
        & ~t.detail[above_part] & ~t.no_cast[above_part] & (t.group[above_part] != t.group[cam.part])
    return res
