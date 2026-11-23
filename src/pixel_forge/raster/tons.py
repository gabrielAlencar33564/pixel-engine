"""O tom de cada pixel pela peça dona dele: a peça chapada (com a textura do material), o sólido de revolução (pela
normal) e a peça lisa (as faixas de luz e sombra pelo lado da luz, e o tom fundo onde outra peça a cobre)."""

from __future__ import annotations

import numpy as np

from ..views.primitivas import DrawCommand, RevolutionPrim
from .estilo import EstiloRender
from .grade import Janela, Mascara, NaJanela, part_window, shift
from .montagem import Buf16, Camadas
from .revolucao import revolution_indices, surface
from .textura import Indices, flat_texture_indices

# o tom mais escuro da rampa só entra na peça lisa com o canvas mais largo que isto
DEEP_SHADOW_WIDTH_PX = 32


def _chapada(est: EstiloRender, c: DrawCommand, full: Mascara, win: Janela) -> Indices:
    """O tom do meio da rampa (o claro com ``detail_light``); a peça que não é detalhe ganha a textura do material,
    com os degraus de baixo e de cima da família, contada do canto da peça inteira."""
    ramp = est.materials[c.material].ramp
    tex = est.materials[c.material].texture
    fw = full[win]
    if tex is None or "detail" in c.tags:
        return np.full(fw.shape, ramp[len(ramp) // 2] if "detail_light" not in c.tags else ramp[-1], dtype=np.uint16)
    down = est.materials[c.material].cast_material
    up = est.family_up.get(c.material)
    ys, xs = np.nonzero(full)
    return flat_texture_indices(fw, (int(xs.min()) - win[1].start, int(ys.min()) - win[0].start), tex,
                                ramp[len(ramp) // 2],
                                (est.tom_do_meio(down) if down in est.materials else None,
                                 est.tom_do_meio(up) if up in est.materials else None))


def _revolucao(est: EstiloRender, c: DrawCommand, cam: Camadas, win: Janela, cast: Mascara) -> Indices:
    prim = c.prim
    assert isinstance(prim, RevolutionPrim)
    h, w = cam.part.shape
    fw = cam.full[c.part_id][win]
    sf = surface(prim.stations, prim.sd, prim.ce, w, h)
    return revolution_indices(sf, prim.ce, NaJanela(win, fw, cast[win] & fw), est.materials[c.material], est.side)


def _faixas(est: EstiloRender, c: DrawCommand, cam: Camadas, win: Janela, cast: Mascara) -> Indices:
    """A peça lisa: a faixa de sombra do lado oposto à luz, a de luz do lado dela (com área mínima) e o tom fundo da
    rampa onde outra peça a cobre pelo lado da luz."""
    sh = est.doc.shading
    ramp = est.materials[c.material].ramp
    shadow_i, mid_i, light_i = (ramp[0], ramp[1], ramp[1]) if len(ramp) == 2 else (ramp[-3], ramp[-2], ramp[-1])
    deep_i = ramp[0] if len(ramp) >= 4 and cam.width > DEEP_SHADOW_WIDTH_PX else shadow_i
    full = cam.full[c.part_id]
    fm = full[win]
    dark = np.zeros_like(fm)
    for k in range(1, sh.shadow_band_px + 1):
        if est.sx:
            dark |= ~shift(fm, est.sx * k, 0)
        if est.sy:
            dark |= ~shift(fm, 0, est.sy * k)
    lit = np.zeros_like(fm)
    if int(full.sum()) >= sh.highlight_min_area_px:
        for k in range(1, sh.highlight_band_px + 1):
            if est.sx:
                lit |= ~shift(fm, -est.sx * k, 0)
            if est.sy:
                lit |= ~shift(fm, 0, -est.sy * k)
    region = np.full(fm.shape, mid_i, dtype=np.uint16)
    region[lit & ~dark] = light_i
    region[dark & ~lit] = shadow_i
    region[(cam.part[win] == cam.num[c.part_id]) & cast[win] & fm] = deep_i
    return region


def sombrear(est: EstiloRender, cam: Camadas, index: Buf16, cast: Mascara) -> None:
    """Escreve em ``index`` o tom de cada pixel visível. Cada peça é processada só na janela da máscara dela mais a
    largura das faixas: fora dela nada muda."""
    band = max(est.doc.shading.shadow_band_px, est.doc.shading.highlight_band_px)
    for p in cam.part_ids:
        win = part_window(cam.full[p], band)
        if win is None:
            continue
        vis = cam.part[win] == cam.num[p]
        if not vis.any():
            continue
        c = cam.cmds[p]
        if "detail" in c.tags or "flat" in c.tags:
            region = _chapada(est, c, cam.full[p], win)
        elif isinstance(c.prim, RevolutionPrim):
            region = _revolucao(est, c, cam, win, cast)
        else:
            region = _faixas(est, c, cam, win, cast)
        index[win][vis] = region[vis]
