"""Os cinzentos do estilo (pedido do dono, 2026-11-25): a paleta tem uma rampa cinzenta neutra, puxada para o quente
(`cinza_fundo` a `cinza_claro`), e a casca cinzenta é pintada com ela, com o veio em pé fundo e a crista clara ao lado
dele; as cascas alvas (a lisa e a anelada) também, com o osso no claro. A folhagem cinzenta é cinza-esverdeada
(`cinza_verde_fundo` a `cinza_verde_claro`), e a agulha tem o traço dela: deitado, fino e comprido. Os controles: a
rampa de antes da casca cinzenta (a da ardósia e do metal) é azulada, e o tronco pintado com ela lê como cano, como
a casca clara e a anelada; a textura de antes, sem a crista, não levanta a casca; a copa cinzenta na rampa neutra
não é verde (lê como pedra); a agulha com a textura da folha larga não tem direção."""

from __future__ import annotations

import colorsys
from typing import Any

import numpy as np

from pixel_forge.application.catalogo import de_uma_peca
from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_de_repouso
from pixel_forge.contracts.carregar import validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.contracts.estilo import MaterialDef, StyleDoc
from pixel_forge.design.asset import ir_da_composicao
from pixel_forge.raster.estilo import estilo_render

CINZENTOS = ("casca_cinzenta", "cinza", "cinza_fundo", "casca_alva", "casca_alva_anelada")
ARDOSIA = [27, 20, 21, 26]  # a rampa da casca cinzenta de antes: os tons da ardósia, da pedra e do metal
CINZA_NEUTRO = [50, 51, 52, 53]  # a rampa da copa cinzenta de antes (a da casca cinzenta)
TRONCO = {"altura": "2.4m", "base": "40cm", "topo": "28cm", "casca": "casca_cinzenta", "pe": "0", "irregular": "0"}
# a conífera em andares e o pinheiro aberto, de agulha
AGULHAS = ({"habito": "excurrente", "altura": "5m", "largura": "2.6m"}, {"habito": "aberto", "altura": "4m",
                                                                         "largura": "3.5m"})
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


def _estilo(material: str = "casca_cinzenta", **troca: Any) -> StyleDoc:
    """O estilo base com um material trocado (a rampa ou a textura)."""
    style = estilo_base()
    mats: list[MaterialDef] = [m.model_copy(update=troca) if m.id == material else m for m in style.materials]
    return style.model_copy(update={"materials": mats})


def _rampa(style: StyleDoc, material: str) -> list[int]:
    return list(next(m.ramp for m in style.materials if m.id == material))


def _tronco(style: StyleDoc, casca: str = "casca_cinzenta") -> tuple[Indices, np.ndarray[Any, np.dtype[np.bool_]]]:
    """Os índices do tronco na vista S e a máscara da casca (sem o contorno)."""
    ir = ir_da_composicao(de_uma_peca("tronco_em_pe", {**TRONCO, "casca": casca}))
    q = quadro_de_repouso(ir, estilo_render(style), "S")
    return q.index, np.isin(q.index, _rampa(style, casca)) & (q.alpha == 255)


def _media(index: Indices, onde: np.ndarray[Any, np.dtype[np.bool_]]) -> tuple[float, float, float]:
    rgb = np.array([_rgb(int(i)) for i in index[onde]], dtype=np.float64).mean(axis=0)
    return float(rgb[0]), float(rgb[1]), float(rgb[2])


def _cor_media(style: StyleDoc, casca: str = "casca_cinzenta") -> tuple[float, float, float]:
    return _media(*_tronco(style, casca))


def test_o_tronco_de_casca_cinzenta_nao_e_azulado() -> None:
    """Na média da casca à mostra o vermelho passa o azul: o cinza é pardo, não ardósia."""
    r, _, b = _cor_media(estilo_base())
    assert r >= b + 5


def test_controle_o_tronco_com_a_rampa_de_ardosia_e_azulado() -> None:
    r, _, b = _cor_media(_estilo(ramp=ARDOSIA))
    assert b >= r + 15


def test_as_cascas_alvas_nao_sao_lilases() -> None:
    """A casca alva lisa e a anelada (a bétula) são claras e pardas: o vermelho passa o azul na casca à mostra."""
    for casca in ("casca_alva", "casca_alva_anelada"):
        r, g, b = _cor_media(estilo_base(), casca)
        assert r >= b + 5 and (r + g + b) / 3 >= 120


def test_controle_a_casca_clara_e_a_anelada_sao_lilases() -> None:
    """As de antes (a clara está no oráculo e não muda) puxam para o azul: no tronco fino liam como cano de metal."""
    for casca in ("casca_clara", "casca_anelada"):
        r, _, b = _cor_media(estilo_base(), casca)
        assert b >= r + 10


def _anel(casca: str) -> tuple[int, int]:
    """As marcas que a textura põe no tronco (contra o mesmo tronco liso): os pares de marca um sobre o outro e lado a
    lado."""
    style = estilo_base()
    (com, mascara), (sem, _) = _tronco(style, casca), _tronco(_estilo(casca, texture=None), casca)
    marca = mascara & (com != sem)
    return int((marca[1:] & marca[:-1]).sum()), int((marca[:, 1:] & marca[:, :-1]).sum())


def _luz(i: int) -> float:
    return sum(_rgb(i)) / 3


def test_a_casca_alva_anelada_tem_as_marcas_escuras_deitadas() -> None:
    """As marcas da bétula correm em volta do tronco, são mais que as da anelada (22 pares contra 12 no tronco de
    40 cm) e escuras: o tom de baixo da rampa fica a mais de 100 de luz do de cima (a marca é o cinza do fundo sobre
    o branco, não um tom médio)."""
    em_pe, deitado = _anel("casca_alva_anelada")
    rampa = _rampa(estilo_base(), "casca_alva_anelada")
    assert deitado >= 3 * em_pe and deitado >= 18
    assert _luz(rampa[1]) - _luz(rampa[0]) >= 100


def test_controle_a_anelada_de_antes_tem_a_marca_rasa() -> None:
    rampa = _rampa(estilo_base(), "casca_anelada")
    assert _luz(rampa[1]) - _luz(rampa[0]) < 100


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


def _planta(style: StyleDoc, categoria: str, **planta: str) -> tuple[Indices, np.ndarray[Any, np.dtype[np.bool_]]]:
    """A planta pelos traços na vista S: os índices e a máscara da folhagem (os tons da copa da folha dela)."""
    comp = validar({"id": "planta", "revision": 1, "description": "planta", "reference": "o teste do estilo",
                    "tipo": "prop", "categoria": categoria, "semente": 5, "planta": planta, "vistas": {"S": {}},
                    "movimento": ["static"], "tracos": []}, Composicao, "teste")
    q = quadro_de_repouso(ir_da_composicao(comp), estilo_render(style), "S")
    copa = {"cinzenta": "copa_cinzenta", "agulha": "copa_agulha"}[planta["folha"]]
    return q.index, np.isin(q.index, _rampa(style, copa)) & (q.alpha == 255)


def cinza_verde(rgb: tuple[float, float, float]) -> bool:
    """Cinza-esverdeado: pouca cor (a saturação de 0,08 a 0,3) e, a que tem, do lado do verde (a matiz de 75° a
    150°), longe do verde vivo da folha larga e do pardo da pedra."""
    h, s, _ = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    return 0.08 <= s <= 0.3 and 75 <= h * 360 <= 150


def _sabia_e_oliveira(style: StyleDoc) -> list[tuple[float, float, float]]:
    """A cor média da folhagem cinzenta na moita baixa e na árvore de copa em massa."""
    return [_media(*_planta(style, "arbusto", habito="moita", altura="60cm", largura="90cm", folha="cinzenta")),
            _media(*_planta(style, "arvore_grande", habito="decurrente", altura="5m", largura="5.5m",
                            folha="cinzenta"))]


def test_a_folhagem_cinzenta_e_cinza_esverdeada() -> None:
    """A rampa da copa cinzenta é cinza-esverdeada tom a tom, e a folhagem desenhada também (lê como planta)."""
    assert all(cinza_verde(_rgb(i)) for i in _rampa(estilo_base(), "copa_cinzenta"))
    assert all(cinza_verde(rgb) for rgb in _sabia_e_oliveira(estilo_base()))


def test_controle_a_copa_cinzenta_na_rampa_neutra_le_como_pedra() -> None:
    """A rampa de antes (o cinza neutro e quente da casca) não tem o verde: a folhagem sai parda."""
    assert not any(cinza_verde(rgb) for rgb in _sabia_e_oliveira(_estilo("copa_cinzenta", ramp=CINZA_NEUTRO)))


def _traco_deitado(style: StyleDoc) -> list[float]:
    """Na folhagem de agulha, as trocas de tom entre vizinhos de cima e de baixo sobre as entre vizinhos de lado: o
    traço deitado e comprido troca de tom muito mais na vertical que na horizontal (o pontilhado, igual)."""
    razoes = []
    for planta in AGULHAS:
        index, folha = _planta(style, "arvore_grande", folha="agulha", **planta)
        idx = index.astype(np.int64)
        lado = int(((idx[:, 1:] != idx[:, :-1]) & folha[:, 1:] & folha[:, :-1]).sum())
        cima = int(((idx[1:] != idx[:-1]) & folha[1:] & folha[:-1]).sum())
        razoes.append(cima / max(1, lado))
    return razoes


def test_a_agulha_tem_o_traco_fino_deitado() -> None:
    """Na conífera em andares e no pinheiro aberto a agulha é traço: a troca de tom na vertical passa 1,3 vez a da
    horizontal (medido: 1,66 e 1,43)."""
    assert all(r >= 1.3 for r in _traco_deitado(estilo_base()))


def test_controle_a_agulha_com_a_textura_da_folha_larga_nao_tem_direcao() -> None:
    """Com a textura da folha larga (o pontilhado de 1 a 2 px, o de antes), a agulha lê como folha em outra cor (1,15
    e 1,14)."""
    folhosa = next(m.texture for m in estilo_base().materials if m.id == "copa_folhosa")
    assert all(r < 1.2 for r in _traco_deitado(_estilo("copa_agulha", texture=folhosa)))
