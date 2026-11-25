"""A flora de lâminas e de pontos (mudança 21): a touceira lê como lâminas e não como massa, a folha larga é mais
que um traço, a folha em pena é serrilhada, a palma nasce no alto do tronco, e o salpico cai onde a câmera vê. Os
controles: a moita em massa, a lâmina fina, a folha lisa, o pé no chão e o salpico sorteado na volta toda."""

from __future__ import annotations

import math
from typing import Any

import pytest

from pixel_forge.application.catalogo import de_uma_peca
from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_de_repouso
from pixel_forge.contracts.carregar import validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.design.asset import ir_da_composicao
from pixel_forge.design.escala import PPM
from pixel_forge.design.kit import pecas_ervas
from pixel_forge.design.kit.registro import PECAS
from pixel_forge.quality import flora
from pixel_forge.raster.estilo import estilo_render
from pixel_forge.raster.renderer import Quadro

CAPIM = PECAS["touceira"].variacoes[0][1]
FLORES = PECAS["salpico"].variacoes[0][1]


def _quadro(comp: Composicao) -> Quadro:
    return quadro_de_repouso(ir_da_composicao(comp), estilo_render(estilo_base()), "S")


def test_a_touceira_e_de_laminas() -> None:
    """A silhueta é de lâminas: enche pouco do fecho convexo dela, e cada lâmina é uma parte."""
    for nome, args in PECAS["touceira"].variacoes:
        comp = de_uma_peca("touceira", args)
        assert flora.solidez(_quadro(comp).dono != 0) < 0.8, nome
        laminas = [p for p in ir_da_composicao(comp).parts if not p.id.endswith(("_pena", "_miolo"))]
        assert len(laminas) == int(args["n"])


def test_controle_a_moita_em_massa_enche_o_fecho() -> None:
    moita = PECAS["copa"].variacoes[-1][1]
    assert flora.solidez(_quadro(de_uma_peca("copa", moita)).dono != 0) > 0.85


def _pixels(**args: Any) -> int:
    return int((_quadro(de_uma_peca("touceira", {**CAPIM, "altura": ["50cm", "80cm"], **args})).dono != 0).sum())


def test_a_folha_larga_e_mais_que_um_traco() -> None:
    assert _pixels(largura="20cm") >= 1.5 * _pixels()


def _borda_sobre_a_area(pena: bool) -> float:
    """Os pixels da borda da figura sobre os da figura: a folha serrilhada tem mais borda que a lisa."""
    args = {**CAPIM, "altura": ["80cm", "1.1m"], "n": "5", "abre": "0.8", "largura": "30cm", "pena": pena}
    figura = _quadro(de_uma_peca("touceira", args)).dono != 0
    dentro = figura.copy()
    dentro[1:] &= figura[:-1]
    dentro[:-1] &= figura[1:]
    dentro[:, 1:] &= figura[:, :-1]
    dentro[:, :-1] &= figura[:, 1:]
    return float((figura & ~dentro).sum()) / float(figura.sum())


def test_a_folha_em_pena_e_serrilhada() -> None:
    assert _borda_sobre_a_area(True) >= 1.15 * _borda_sobre_a_area(False)


def _pes(pe: list[str]) -> set[float]:
    ir = ir_da_composicao(de_uma_peca("touceira", {**CAPIM, "raio": "0", "pe": pe}))
    return {p.geometry.points_q8[0][2] / 256 for p in ir.parts if p.geometry.type == "polyline"}


def test_a_touceira_nasce_no_alto_de_um_tronco() -> None:
    """Com o pé no alto (a palma), toda lâmina sai de lá."""
    assert _pes(["0", "0", "2m"]) == {round(2 * PPM * 256) / 256}


def test_controle_por_padrao_a_touceira_nasce_no_chao() -> None:
    assert _pes(["0", "0", "0"]) == {0.0}


def _do_lado_de_la(vistas: tuple[str, ...]) -> tuple[int, int]:
    """Os pontos do salpico, e deles os que caem na metade de trás da moita (longe da câmera da vista S)."""
    dado = de_uma_peca("salpico", FLORES).model_dump(mode="json")
    ir = ir_da_composicao(validar({**dado, "vistas": dict.fromkeys(vistas, {})}, Composicao, "teste"))
    pontos = [p.geometry.center_q8 for p in ir.parts if p.id.startswith("n_") and p.geometry.type == "ellipse"]
    return len(pontos), sum(1 for p in pontos if p[1] < -5 * 256)


def test_o_salpico_cai_do_lado_da_camera() -> None:
    """Na composição de vista única, nenhum ponto cai atrás da moita, e a câmera vê quase todos."""
    assert _do_lado_de_la(("S",)) == (int(FLORES["n"]), 0)
    q = _quadro(de_uma_peca("salpico", FLORES))
    assert sum(1 for p in q.part_table if p.startswith("n_") and q.visiveis.get(p, 0)) >= 0.75 * int(FLORES["n"])


def test_controle_na_volta_toda_ha_pontos_do_lado_de_la() -> None:
    """Com as 4 vistas os pontos se espalham pela volta: cada vista mostra os dela."""
    assert _do_lado_de_la(("S", "E", "N", "W"))[1] >= 2


def test_o_salpico_na_ponta_das_laminas() -> None:
    """A âncora das pontas da touceira leva a flor e a espiga."""
    comp = validar({**de_uma_peca("touceira", CAPIM).model_dump(mode="json"), "nos": [
        {"id": "pe", "peca": "touceira", "args": {**CAPIM, "n": "6"}},
        {"id": "flor", "peca": "salpico", "args": {"em": "pe.pontas", "material": "ambar", "n": "6"}}]},
        Composicao, "teste")
    q = _quadro(comp)
    assert sum(1 for p in q.part_table if p.startswith("flor_") and q.visiveis.get(p, 0)) >= 4


def _sombra_no_chao() -> int:
    """Os pixels da sombra que a touceira lança no chão."""
    style = estilo_base()
    q = _quadro(de_uma_peca("touceira", {**CAPIM, "altura": ["50cm", "80cm"]}))
    chao = next(m for m in style.materials if m.id == "sombra").ramp[0]
    return int(((q.index == chao) & (q.alpha == 255) & (q.dono == 0)).sum())


def test_a_touceira_lanca_a_sombra_dela() -> None:
    """A lâmina fina não é detalhe: a sombra dela no chão assenta a planta."""
    assert _sombra_no_chao() >= 20


def test_controle_a_lamina_de_detalhe_nao_lanca_sombra(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pecas_ervas, "FIO", ("flat", "detail", "no_outline"))
    assert _sombra_no_chao() == 0


def _raios_do_ponto(**args: str) -> tuple[int, int]:
    ir = ir_da_composicao(de_uma_peca("salpico", {**FLORES, **args}))
    raios = next(p.geometry.radii_q8 for p in ir.parts if p.id.startswith("n_") and p.geometry.type == "ellipse")
    return raios[0], raios[2]


def test_o_ponto_alongado_e_a_espiga_em_pe() -> None:
    largo, alto = _raios_do_ponto(alonga="3")
    assert abs(alto - 3 * largo) <= 2  # q8: 1/128 px de arredondamento


def test_controle_por_padrao_o_ponto_e_redondo() -> None:
    largo, alto = _raios_do_ponto()
    assert alto == largo


def _claras_de_cada_lado() -> tuple[int, int]:
    """As lâminas claras de uma touceira grande que abrem para a esquerda da tela (a luz) e para a direita."""
    ir = ir_da_composicao(de_uma_peca("touceira", {**CAPIM, "n": "40", "raio": "0"}))
    lados = [p.geometry.points_q8[-1][0] for p in ir.parts
             if p.material == "capim_claro" and p.geometry.type == "polyline"]
    return sum(1 for x in lados if x < 0), sum(1 for x in lados if x > 0)


def test_o_claro_das_laminas_fica_do_lado_da_luz() -> None:
    esquerda, direita = _claras_de_cada_lado()
    assert esquerda >= 6 and esquerda >= 3 * direita


def test_controle_so_com_o_sorteio_o_claro_cai_dos_dois_lados(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pecas_ervas, "LADO_DA_LUZ", 0.0)
    esquerda, direita = _claras_de_cada_lado()
    assert esquerda >= 3 and direita >= 3



FOLHAS = {**CAPIM, "altura": ["60cm", "90cm"], "n": "8", "abre": "0.8", "cai": "0.5", "largura": "16cm", "raio": "0"}


def _nervuras_a_mostra(pena: bool) -> int:
    """As folhas largas com a nervura à mostra (a parte ``_pena`` com pixel)."""
    q = _quadro(de_uma_peca("touceira", {**FOLHAS, "pena": pena}))
    return sum(1 for p in q.part_table if p.endswith("_pena") and q.visiveis.get(p, 0) >= 3)


def test_a_folha_em_pena_tem_a_nervura_a_mostra() -> None:
    """Cada folha se lê pela nervura dela, por cima do corpo."""
    assert _nervuras_a_mostra(True) >= 6


def test_controle_a_folha_lisa_nao_tem_nervura() -> None:
    assert _nervuras_a_mostra(False) == 0


def _mais_perto_da_frente(semente: int) -> float:
    """O ângulo (graus) entre a câmera e a folha larga que mais aponta para ela."""
    dado = de_uma_peca("touceira", FOLHAS).model_dump(mode="json")
    ir = ir_da_composicao(validar({**dado, "semente": semente}, Composicao, "teste"))
    pontas = [p.geometry.points_q8[-1] for p in ir.parts if p.geometry.type == "tapered_polyline"]
    return min(abs(math.degrees(math.atan2(x, y))) for x, y, _ in pontas)


def test_nenhuma_folha_larga_aponta_para_a_camera() -> None:
    """A roseta deixa a frente livre: a folha de frente para a câmera viraria um talo em pé no meio dela."""
    assert min(_mais_perto_da_frente(s) for s in range(12)) >= 0.2 * 360 / 8 - 0.5


def test_controle_com_o_giro_solto_uma_folha_aponta_para_a_camera(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pecas_ervas, "FRENTE_LIVRE", 1.0)
    assert min(_mais_perto_da_frente(s) for s in range(12)) < 0.2 * 360 / 8 - 0.5


def _miolo_a_mostra(largura: str) -> int:
    """Os pixels do miolo escuro no pé da touceira."""
    q = _quadro(de_uma_peca("touceira", {**FOLHAS, "largura": largura, "pena": largura != "0"}))
    return q.visiveis.get("n_miolo", 0)


def test_a_roseta_de_folhas_largas_tem_o_miolo_escuro() -> None:
    """O pé das folhas largas é o ponto mais escuro da planta: a roseta tem fundo."""
    assert _miolo_a_mostra("16cm") >= 4


def test_controle_a_touceira_de_laminas_finas_nao_tem_miolo() -> None:
    assert _miolo_a_mostra("0") == 0
