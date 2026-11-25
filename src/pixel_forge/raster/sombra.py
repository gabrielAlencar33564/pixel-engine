"""As sombras: a projetada entre peças pelo z-buffer e a lançada no chão pela luz.

Entre peças: de cada pixel, um raio para a luz anda até ``cast_shadow_px`` px na tela, subindo na profundidade o que a
luz sobe; se passa atrás de um pixel de outro grupo, o pixel está na sombra (a largura da faixa sai da diferença de
profundidade, não de uma constante). A peça chapada compara peça com peça e plano com plano: as fileiras de um
telhado e as pedras de uma parede, do mesmo plano, não se sombreiam.

No chão: cada peça volta da tela ao mundo pela câmera da vista, é lançada no chão (z = 0) na direção da luz e volta à
tela, em xadrez (o chão aparece entre os pixels), no material ``sombra`` do estilo. É a única sombra no chão: não há
sombra de contato (a mancha redonda embaixo do asset), e a do pé nasce no pé, que se lança sobre si mesmo. O tronco
(o sólido de revolução) se lança como o tubo do eixo dele; o cacho pontilhado da copa é um plano virado para a câmera,
que a luz pega de lado (no chão ele seria uma linha), e se lança como a almofada redonda que ele desenha.
"""

from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np
import numpy.typing as npt

from ..views.camera import ELEVACAO_MDEG, PROFUNDIDADE_PERMILLE
from ..views.primitivas import (
    DrawCommand,
    EllipsePrim,
    RevolutionPrim,
    Scene2D,
    StipplePrim,
    SupElipsoide,
    SupLeque,
    SupTubo,
)
from .estilo import EstiloRender
from .formas import raster_ellipse, raster_polygon, raster_tapered
from .grade import MARGIN, Mascara, shift
from .montagem import Buf16, Camadas, Tabelas
from .profundidade import DEPTH_QUANT
from .textura import Floats

CAST_TONES = 2  # quantos tons da rampa a sombra entre peças desce
CAST_BIAS_PX = 0.5  # a folga de profundidade: a peça encostada não sombreia a vizinha
CAST_SAME_PLANE_PERMILLE = 950  # normais com cosseno acima de 0,95 ...
CAST_PLANE_GAP_PX = 1.0  # ... e planos a menos de 1 px um do outro são o mesmo plano


class _Planos:
    """A chapada de cada peça (com degrau de sombra), a normal dela (×1000) e a distância do plano, em px de tela."""

    def __init__(self, est: EstiloRender, cam: Camadas) -> None:
        n = len(cam.cmds) + 1
        self.flat = np.zeros(n, dtype=bool)
        self.normal = np.zeros((n, 3), dtype=np.int64)
        self.offset = np.zeros(n, dtype=np.float64)
        for p, c in cam.cmds.items():
            k = cam.num[p]
            self.flat[k] = "flat" in c.tags and est.materials[c.material].cast_material is not None
            if c.facing is not None and "flat" in c.tags and isinstance(c.surface, SupLeque):
                self.normal[k] = c.facing
                u0, v0, d0 = c.surface.pts[0]
                self.offset[k] = (c.facing[0] * u0 + c.facing[1] * v0 + c.facing[2] * d0) / 256_000

    def outro_plano(self, part: Buf16, po: Buf16) -> Mascara:
        nrm = self.normal[part]
        no = self.normal[po]
        dot = (nrm * no).sum(axis=-1)
        conhecida = (np.abs(nrm).sum(axis=-1) > 0) & (np.abs(no).sum(axis=-1) > 0)
        mesmo = conhecida & (dot >= CAST_SAME_PLANE_PERMILLE * 1000) \
            & (np.abs(self.offset[part] - self.offset[po]) < CAST_PLANE_GAP_PX)
        res: Mascara = (po != part) & ~mesmo
        return res


def _cast_shadow(est: EstiloRender, cam: Camadas, t: Tabelas, planos: _Planos) -> Mascara:
    lx, ly, lz = est.light
    s = math.hypot(lx, ly)
    out = np.zeros(cam.part.shape, dtype=bool)
    if s < 1e-6:
        return out
    ux, uy, uz = lx / s, ly / s, lz / s
    opaque = cam.part != 0
    z: Floats = np.where(opaque, cam.zbuf / DEPTH_QUANT, 0.0)
    grp = t.group[cam.part]
    blocker = opaque & ~(t.detail | t.no_cast)[cam.part]
    flat = planos.flat[cam.part] if planos.flat.any() else None
    for k in range(1, est.doc.shading.cast_shadow_px + 1):
        dx, dy = round(ux * k), round(uy * k)
        if dx == 0 and dy == 0:
            continue
        zo = shift(z, dx, dy)
        hit = (shift(grp, dx, dy) != grp) & (zo > z + uz * k + CAST_BIAS_PX)
        if flat is not None:  # a chapada: outra peça, de outro plano, à frente
            outro = planos.outro_plano(cam.part, shift(cam.part, dx, dy))
            hit = np.where(flat, outro & (zo > z + uz * k + CAST_BIAS_PX), hit)
        out |= opaque & shift(blocker, dx, dy) & hit
    return out


def _desce(index: Buf16, sel: Mascara, ramp: list[int]) -> None:
    vals = index[sel]
    for v in np.unique(vals):
        if int(v) in ramp:
            vals[vals == v] = ramp[max(0, ramp.index(int(v)) - CAST_TONES)]
    index[sel] = vals


def sombra_entre_pecas(est: EstiloRender, cam: Camadas, t: Tabelas, index: Buf16) -> None:
    """A peça lisa desce dois tons da rampa; a chapada pega o tom do meio do degrau de sombra do material."""
    shade = _cast_shadow(est, cam, t, _Planos(est, cam)) & ~t.detail[cam.part] & ~t.no_outline[cam.part]
    for p, c in sorted(cam.cmds.items()):
        sel = shade & (cam.part == cam.num[p])
        if not sel.any():
            continue
        if "flat" in c.tags:
            to = est.materials[c.material].cast_material
            if to is not None and to in est.materials:
                index[sel] = est.tom_do_meio(to)
            continue
        _desce(index, sel, list(est.materials[c.material].ramp))


def _ground_projection(scene: Scene2D, light: tuple[float, float, float], w: int, h: int) -> Mascara:
    out = np.zeros((h, w), dtype=bool)
    a, e = math.radians(scene.azimuth_mdeg / 1000), math.radians(ELEVACAO_MDEG / 1000)
    sa, ca, se, ce = math.sin(a), math.cos(a), math.sin(e), math.cos(e)
    sd = PROFUNDIDADE_PERMILLE / 1000
    eu, ev, ed = np.array([ca, -sa, 0.0]), np.array([sa * sd, ca * sd, -ce]), np.array([sa * ce, ca * ce, se])
    inv = np.linalg.inv(np.array([eu, ev, ed]))
    lw = light[0] * eu + light[1] * np.array([sa * se, ca * se, -ce]) + light[2] * ed  # a luz no mundo
    if lw[2] <= 1e-6:  # luz rasante ou de baixo: sem sombra no chão
        return out
    pu, pv = scene.pivot_q8

    def chao(u: float, v: float, d: float) -> tuple[int, int]:
        p: npt.NDArray[np.float64] = inv @ np.array([u - pu, v - pv, d])
        g = p - lw * (max(p[2], 0.0) / lw[2])
        return round(float(g @ eu)) + pu, round(float(g @ ev)) + pv

    for c in scene.commands:
        if not {"detail", "no_cast"} & set(c.tags):
            out |= _lancada(c, chao, sd, w, h)
    return out


def _lancada(c: DrawCommand, chao: Callable[[float, float, float], tuple[int, int]], sd: float, w: int,
             h: int) -> Mascara:
    """A peça lançada no chão, com ``chao`` levando um ponto (u, v, profundidade) em q8 ao chão sob a luz."""
    if isinstance(c.prim, RevolutionPrim):
        eixo = [chao(s[0] * 256, s[1] * 256, s[2] * 256) for s in c.prim.stations]
        return raster_tapered(w, h, MARGIN, tuple(eixo), tuple(round(s[3] * 256) for s in c.prim.stations))
    if isinstance(c.prim, StipplePrim) and isinstance(c.surface, SupLeque):
        us, vs = zip(*(chao(*p) for p in c.surface.pts), strict=True)
        meia = (max(us) - min(us)) // 2  # a almofada tem no chão a profundidade da largura
        return raster_ellipse(w, h, MARGIN, ((max(us) + min(us)) // 2, sum(vs) // len(vs)), (meia, round(meia * sd)))
    if isinstance(c.surface, SupLeque):
        pts = [chao(*p) for p in c.surface.pts]
        out = np.zeros((h, w), dtype=bool)
        for b, d in zip(pts[1:], pts[2:], strict=False):
            out |= raster_polygon(w, h, MARGIN, (pts[0], b, d))
        return out
    if isinstance(c.surface, SupTubo):
        return raster_tapered(w, h, MARGIN, tuple(chao(*p) for p in c.surface.pts), c.surface.radii)
    if isinstance(c.surface, SupElipsoide) and isinstance(c.prim, EllipsePrim):
        s = c.surface
        return raster_ellipse(w, h, MARGIN, chao(s.cu, s.cv, s.dc), (c.prim.hu, max(1, c.prim.hv // 2)))
    return np.zeros((h, w), dtype=bool)


MATERIAL_DA_SOMBRA = "sombra"  # o material do estilo que pinta a sombra no chão (sem ele, o chão fica limpo)


def sombra_no_chao(est: EstiloRender, cam: Camadas, scene: Scene2D, index: Buf16,
                   alpha: npt.NDArray[np.uint8]) -> Mascara:
    """A sombra que o asset projeta no chão, camada atrás de tudo, em xadrez na fase do pivô; devolve os pixels dela
    (sem dono: não são da figura, e a limpeza não os toca)."""
    h, w = cam.part.shape
    if MATERIAL_DA_SOMBRA not in est.materials:
        return np.zeros((h, w), dtype=bool)
    yy, xx = np.indices((h, w))
    ox, oy = (scene.pivot_q8[0] >> 8) + MARGIN, (scene.pivot_q8[1] >> 8) + MARGIN
    sh: Mascara = _ground_projection(scene, est.light, w, h) & ((xx - ox + yy - oy) % 2 == 0) & (alpha == 0)
    index[sh] = est.materials[MATERIAL_DA_SOMBRA].ramp[0]
    alpha[sh] = 255
    return sh
