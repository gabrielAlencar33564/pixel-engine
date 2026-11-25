"""Os cinzentos do estilo (pedido do dono, 2026-11-25): a paleta tem uma rampa cinzenta neutra, puxada para o quente
(`cinza_fundo` a `cinza_claro`), e a casca cinzenta é pintada com ela, com o veio em pé fundo e a crista clara ao lado
dele. Os controles: a rampa de antes da casca cinzenta (a da ardósia e do metal) é azulada, e o tronco pintado com
ela lê como cano; a textura de antes, sem a crista, não levanta a casca."""

from __future__ import annotations

import colorsys
from typing import Any

import numpy as np

from pixel_forge.application.catalogo import de_uma_peca
from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_de_repouso
from pixel_forge.contracts.estilo import MaterialDef, StyleDoc
from pixel_forge.design.asset import ir_da_composicao
from pixel_forge.raster.estilo import estilo_render

CINZENTOS = ("casca_cinzenta", "cinza", "cinza_fundo", "copa_cinzenta")
ARDOSIA = [27, 20, 21, 26]  # a rampa da casca cinzenta de antes: os tons da ardósia, da pedra e do metal
TRONCO = {"altura": "2.4m", "base": "40cm", "topo": "28cm", "casca": "casca_cinzenta", "pe": "0", "irregular": "0"}
Indices = np.ndarray[Any, np.dtype[np.uint16]]


def _rgb(i: int) -> tuple[int, int, int]:
    r, g, b, _ = next(p.rgba for p in estilo_base().palette if p.index == i)
    return r, g, b


def cinzento_quente(rampa: list[int]) -> bool:
    """Cada tom quase sem cor (a saturação até 0,15) e, se tem alguma, do lado quente (a matiz de 15° a 60°: do
    pardo ao oliva); os tons sobem de luz do primeiro ao último."""
    luz = []
    for i in rampa:
        h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in _rgb(i)))
        if s > 0.15 or (s >= 0.03 and not 15 <= h * 360 <= 60):
            return False
        luz.append(v)
    return all(a <= b for a, b in zip(luz, luz[1:], strict=False))


def test_os_cinzentos_da_paleta_sao_neutros_e_quentes() -> None:
    mats = {m.id: m for m in estilo_base().materials}
    assert all(cinzento_quente(list(mats[m].ramp)) for m in CINZENTOS)
    assert len(mats["casca_cinzenta"].ramp) == 4


def test_controle_a_rampa_de_ardosia_e_azulada() -> None:
    assert not cinzento_quente(ARDOSIA)


def _estilo(**troca: Any) -> StyleDoc:
    """O estilo base com a casca cinzenta trocada (a rampa ou a textura)."""
    style = estilo_base()
    mats: list[MaterialDef] = [m.model_copy(update=troca) if m.id == "casca_cinzenta" else m for m in style.materials]
    return style.model_copy(update={"materials": mats})


def _tronco(style: StyleDoc) -> tuple[Indices, np.ndarray[Any, np.dtype[np.bool_]]]:
    """Os índices do tronco de casca cinzenta na vista S e a máscara da casca (sem o contorno)."""
    q = quadro_de_repouso(ir_da_composicao(de_uma_peca("tronco_em_pe", TRONCO)), estilo_render(style), "S")
    rampa = next(m.ramp for m in style.materials if m.id == "casca_cinzenta")
    return q.index, np.isin(q.index, rampa) & (q.alpha == 255)


def _cor_media(style: StyleDoc) -> tuple[float, float, float]:
    index, casca = _tronco(style)
    rgb = np.array([_rgb(int(i)) for i in index[casca]], dtype=np.float64).mean(axis=0)
    return float(rgb[0]), float(rgb[1]), float(rgb[2])


def test_o_tronco_de_casca_cinzenta_nao_e_azulado() -> None:
    """Na média da casca à mostra o vermelho passa o azul: o cinza é pardo, não ardósia."""
    r, _, b = _cor_media(estilo_base())
    assert r >= b + 5


def test_controle_o_tronco_com_a_rampa_de_ardosia_e_azulado() -> None:
    r, _, b = _cor_media(_estilo(ramp=ARDOSIA))
    assert b >= r + 15


def _relevo(style: StyleDoc) -> tuple[int, int, int, int]:
    """O que a textura muda no tronco, contra o mesmo tronco liso: os pixels que descem de tom (o sulco), os que
    sobem (a crista), e os pares de sulco um sobre o outro e lado a lado."""
    rampa = list(next(m.ramp for m in style.materials if m.id == "casca_cinzenta"))
    pos = np.full(65536, -1, dtype=np.int64)
    pos[rampa] = np.arange(len(rampa))
    (com, casca), (sem, _) = _tronco(style), _tronco(_estilo(texture=None))
    passo = np.where(casca, pos[com] - pos[sem], 0)
    sulco = passo < 0
    return (int(sulco.sum()), int((passo > 0).sum()), int((sulco[1:] & sulco[:-1]).sum()),
            int((sulco[:, 1:] & sulco[:, :-1]).sum()))


def _casca_levantada(style: StyleDoc) -> bool:
    """O sulco cobre um sétimo da casca à mostra, a crista clara passa de 4 %, e o veio corre ao longo da altura."""
    sulcos, cristas, em_pe, deitado = _relevo(style)
    casca = int(_tronco(style)[1].sum())
    return sulcos >= casca / 7 and cristas >= 0.04 * casca and em_pe >= 3 * deitado


def test_a_casca_cinzenta_tem_o_sulco_em_pe_e_a_crista() -> None:
    assert _casca_levantada(estilo_base())


def test_controle_a_textura_de_antes_nao_levanta_a_casca() -> None:
    """A textura de antes (a da sulcada: o sulco mais curto e raso, sem a crista) deixa o tronco quase liso."""
    tex = next(m.texture for m in estilo_base().materials if m.id == "casca_cinzenta")
    assert tex is not None
    antes = tex.model_copy(update={"density_permille": 600, "depth_permille": 330, "length_px": [3, 7],
                                   "lift_permille": 0})
    assert not _casca_levantada(_estilo(texture=antes))
