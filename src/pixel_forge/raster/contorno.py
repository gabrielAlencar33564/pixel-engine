"""Os contornos: o interno, no lado da peça de trás onde o grupo muda, e o externo, por dentro da silhueta (a figura
não engorda) com o sel-out (o lado da luz no tom mais escuro do material), a limpeza pixel-perfect dos cantos e, na
folha em pena, a linha partida dente a dente."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from .estilo import EstiloRender
from .grade import Mascara, pixel_perfect, shift
from .montagem import Buf16, Camadas, Tabelas, sorteadas

QUATRO = ((1, 0), (-1, 0), (0, 1), (0, -1))
BORDA_SERRILHADA = "borda_serrilhada"  # a marca da folha em pena: o contorno de fora sai partido, dente a dente
SERRILHA_PARTE = 500  # os pixels desse contorno que voltam a ser vazio (‰)


def contorno_interno(cam: Camadas, t: Tabelas, index: Buf16) -> Mascara:
    """A linha entre peças de grupos diferentes, no pixel da peça de trás (nem detalhe nem ``no_inner_outline``)."""
    inner = np.zeros(cam.part.shape, dtype=bool)
    part = cam.part
    livre = ~t.detail & ~t.no_inner
    for dx, dy in QUATRO:
        nb = shift(part, dx, dy)
        inner |= (part != 0) & (nb != 0) & (nb != part) & (shift(cam.order, dx, dy) > cam.order) \
            & livre[part] & livre[nb] & (t.group[nb] != t.group[part])
    index[inner] = t.outline[part[inner]]
    return inner


def _fina(group: npt.NDArray[np.int32]) -> Mascara:
    """O pixel de peça com 3 px ou mais do mesmo grupo na fileira e na coluna (a que não é fina)."""
    def same(dx: int, dy: int) -> Mascara:
        res: Mascara = shift(group, dx, dy) == group
        return res

    wide_h = (same(-1, 0) & same(-2, 0)) | (same(1, 0) & same(2, 0)) | (same(-1, 0) & same(1, 0))
    wide_v = (same(0, -1) & same(0, -2)) | (same(0, 1) & same(0, 2)) | (same(0, -1) & same(0, 1))
    res: Mascara = wide_h & wide_v
    return res


def _bordas(est: EstiloRender, opaque: Mascara, no_ol: Mascara) -> tuple[Mascara, Mascara, Mascara]:
    """(o anel da borda, a borda do lado da luz, a borda do lado da sombra)."""
    ring = np.zeros(opaque.shape, dtype=bool)
    lit_edge = np.zeros(opaque.shape, dtype=bool)
    dark_side = np.zeros(opaque.shape, dtype=bool)
    for dx, dy in QUATRO:
        out_nb = opaque & ~shift(opaque, dx, dy)
        ring |= out_nb & ~no_ol
        lado = dx * est.sx + dy * est.sy
        if lado < 0:  # o vazio está do lado da luz
            lit_edge |= out_nb
        elif lado > 0:
            dark_side |= out_nb
    return ring, lit_edge, dark_side


def contorno_externo(est: EstiloRender, cam: Camadas, t: Tabelas, bufs: tuple[Buf16, npt.NDArray[np.uint8], Buf16],
                     inner: Mascara) -> Mascara:
    """A borda da silhueta vira o contorno; a peça fina (2 px ou menos) não vira só linha: o contorno dela vai para
    fora. Escreve em ``index`` e ``alpha`` (``bufs``, com o ``fill``, o tom antes das linhas), dá dono ao anel de fora
    em ``cam.part``, tira de ``inner`` o canto pixel-perfect e devolve o anel."""
    index, alpha, fill = bufs
    opaque = cam.part != 0
    ring, lit_edge, dark_side = _bordas(est, opaque, t.no_outline[cam.part])
    thin = ring & ~_fina(t.group[cam.part])
    ring &= ~thin
    src_thin = np.where(thin, cam.part, 0).astype(np.uint16)
    out_ring = np.zeros(opaque.shape, dtype=bool)
    for dx, dy in QUATRO:
        nb = shift(src_thin, dx, dy)
        take = ~opaque & ~out_ring & (nb != 0)
        cam.part = np.where(take, nb, cam.part)
        out_ring |= take
    index[ring] = t.outline[cam.part[ring]]
    light = ring & lit_edge & ~dark_side & t.ramp3[cam.part]
    index[light] = t.ramp0[cam.part[light]]
    index[out_ring] = t.outline[cam.part[out_ring]]
    alpha[out_ring] = 255
    ring |= out_ring
    drop = pixel_perfect(ring | inner)
    index[drop & ~out_ring] = fill[drop & ~out_ring]
    gone = drop & out_ring  # o canto do anel de fora volta a ser vazio
    alpha[gone] = 0
    cam.part = np.where(gone, 0, cam.part).astype(cam.part.dtype)
    ring &= ~drop
    inner &= ~drop
    dentes = _serrilha(cam, ring)
    alpha[dentes] = 0
    cam.part = np.where(dentes, 0, cam.part).astype(cam.part.dtype)
    return ring & ~dentes


def _serrilha(cam: Camadas, ring: Mascara) -> Mascara:
    """Os pixels do contorno de fora da peça ``borda_serrilhada`` que saem: a metade, sorteada pixel a pixel (contada
    do canto da máscara dela), e a beira da folha aparece entre os que ficam, sem linha. A folha não perde o corpo:
    recortada na máscara, ela perdia o pixel do dente, a linha entrava no lugar dele e a folha de 5 px virava um
    traço de 1 px de cor cercado de contorno."""
    dentes = np.zeros(ring.shape, dtype=bool)
    for p in (p for p, c in cam.cmds.items() if BORDA_SERRILHADA in c.tags):
        dela = ring & (cam.part == cam.num[p])
        if dela.any():
            dentes |= dela & sorteadas(cam.full[p], 1, SERRILHA_PARTE)
    return dentes
