"""A fronde em pena: a samambaia e a roseta de folha larga que o hábito deriva, de 0,4 a 1 m, na vista única e nas
quatro. O corpo da fronde aparece (o contorno de fora sai partido, e a fronde é larga até perto da ponta), a roseta
tem o lado claro em cima à esquerda (a folha chapada, com o lado da luz da tela erguido para o alto) e o verde é o da
copa de folha larga. Os controles: a beira recortada na máscara, a fronde de 0,2 do comprimento, a de ponta fina, a
folha com as faixas da peça lisa, o lado da luz da lâmina fina e o verde da folha miúda."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_de_repouso
from pixel_forge.contracts.carregar import validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.design import habito
from pixel_forge.design.asset import ir_da_composicao
from pixel_forge.design.kit import pecas_ervas
from pixel_forge.raster import contorno, montagem
from pixel_forge.raster.estilo import estilo_render
from pixel_forge.raster.renderer import Quadro

# a roseta pequena, a samambaia de sombra, a média e a grande
PORTES = (("40cm", "70cm", "jovem"), ("60cm", "1.1m", "adulta"), ("80cm", "1m", "adulta"), ("1m", "1.4m", "velha"))
QUATRO = ("S", "E", "N", "W")
TINTA = 1  # o índice do contorno na paleta


def _quadros(vistas: tuple[str, ...] = ("S",)) -> list[Quadro]:
    """Cada porte, em quatro sementes, em cada vista."""
    est = estilo_render(estilo_base())
    out = []
    for altura, largura, idade in PORTES:
        for semente in range(4):
            dado = {"id": "feto", "revision": 1, "description": "feto", "reference": "feto", "tipo": "prop",
                    "categoria": "arbusto", "semente": semente, "vistas": dict.fromkeys(vistas, {}),
                    "movimento": ["static"], "tracos": [],
                    "planta": {"habito": "touceira", "altura": altura, "largura": largura, "idade": idade,
                               "folha": "larga"}}
            ir = ir_da_composicao(validar(dado, Composicao, "teste"))
            out += [quadro_de_repouso(ir, est, v) for v in ir.views]
    return out


def _figura(q: Quadro) -> Any:
    return (q.alpha == 255) & (q.dono != 0)


def _corpo_e_contorno() -> tuple[float, float]:
    """Na média dos portes e sementes da vista S: a espessura do corpo de cada fronde (os px dela fora o contorno,
    sobre o comprimento dela na tela) e a parte da figura que é contorno."""
    espessuras, tinta = [], []
    for q in _quadros():
        fig = _figura(q)
        tinta.append(float((fig & (q.index == TINTA)).sum() / fig.sum()))
        for k, p in enumerate(q.part_table):
            corpo = (q.dono == k + 1) & fig & (q.index != TINTA)
            if p.count("_") != 1 or p.endswith("_miolo") or corpo.sum() < 3:
                continue  # só o corpo da fronde (a nervura é ``folhas_00_pena``)
            ys, xs = np.nonzero(corpo)
            espessuras.append(float(corpo.sum()) / (max(np.ptp(xs), np.ptp(ys)) + 1))
    return float(np.mean(espessuras)), float(np.mean(tinta))


def test_o_corpo_da_fronde_aparece() -> None:
    """A fronde de 60 cm tem 3 px de cor ou mais de grossura, e o contorno é no máximo 15 % da figura (antes: 1,9 px,
    e o contorno era 29 %: a fronde era um traço de 1 px cercado de contorno, e a roseta lia como aranha)."""
    espessura, tinta = _corpo_e_contorno()
    assert espessura >= 2.9 and tinta <= 0.15, (espessura, tinta)


def test_controle_recortada_na_mascara_a_fronde_vira_contorno(monkeypatch: pytest.MonkeyPatch) -> None:
    """O jeito antigo: a beira recortada na máscara perde o pixel do dente, e o contorno entra no lugar dele."""
    mascara = montagem._mascara

    def recortada(c: Any, w: int, h: int) -> Any:
        m = mascara(c, w, h)
        if contorno.BORDA_SERRILHADA in c.tags and m.sum() >= montagem.FOLHA_AREA_MINIMA:
            return montagem._recortada(m, 1, contorno.SERRILHA_PARTE)
        return m

    monkeypatch.setattr(montagem, "_mascara", recortada)
    monkeypatch.setattr(contorno, "_serrilha", lambda _cam, ring: np.zeros(ring.shape, dtype=bool))
    assert _corpo_e_contorno()[1] > 0.2


@pytest.mark.parametrize("antigo", ["fronde", "perfil"])
def test_controle_a_fronde_estreita_nao_tem_corpo(monkeypatch: pytest.MonkeyPatch, antigo: str) -> None:
    """A fronde de 0,2 do comprimento, ou a de ponta fina (o perfil da folha lisa), sai com menos de 2,9 px de cor."""
    if antigo == "fronde":
        monkeypatch.setattr(habito, "FRONDE", (0.2, habito.FRONDE[1]))
    else:
        monkeypatch.setattr(pecas_ervas, "LARGURA_DA_PENA", pecas_ervas.LARGURA_NO_ARCO)
    assert _corpo_e_contorno()[0] < 2.9


def _claro_do_lado_da_luz(vistas: tuple[str, ...]) -> float:
    """Dos px do tom claro de todas as rosetas, a parte que cai na metade de cima à esquerda da figura (a da luz,
    cortada na diagonal pelo meio da caixa dela)."""
    claro = next(p.index for p in estilo_base().palette if p.id == "folhosa_clara")
    na_luz = total = 0
    for q in _quadros(vistas):
        fig = _figura(q)
        ys, xs = np.nonzero(fig)
        yy, xx = np.indices(fig.shape)
        luz = (xx - (xs.min() + xs.max()) / 2) + (yy - (ys.min() + ys.max()) / 2) < 0
        tons = fig & (q.index == claro)
        na_luz, total = na_luz + int((tons & luz).sum()), total + int(tons.sum())
    return na_luz / total


def test_a_roseta_tem_o_lado_claro_em_cima_a_esquerda() -> None:
    """O claro é das frondes que abrem para a esquerda e para trás da tela, em toda vista (antes, o risco claro de
    cada fronde caía dos dois lados: não havia lado claro e lado escuro)."""
    for vistas in (("S",), QUATRO):
        assert _claro_do_lado_da_luz(vistas) >= 0.97, vistas


@pytest.mark.parametrize("antigo", ["faixas", "lado"])
def test_controle_com_as_faixas_ou_o_lado_da_lamina_o_claro_cai_na_sombra(monkeypatch: pytest.MonkeyPatch,
                                                                        antigo: str) -> None:
    """A fronde com as faixas da peça lisa (o risco claro em cada uma) ou com o lado da luz da lâmina fina (só a
    esquerda, e o sorteio pesando mais que ele) leva o claro para o lado da sombra."""
    if antigo == "faixas":
        monkeypatch.setattr(pecas_ervas, "PENA", tuple(t for t in pecas_ervas.PENA if t != "flat"))
    else:
        monkeypatch.setattr(pecas_ervas, "LUZ_DA_PENA", (pecas_ervas.LADO_DA_LUZ, 0.0))
    assert _claro_do_lado_da_luz(QUATRO) < 0.95


def _cores_fora_da_copa_larga() -> set[int]:
    """Os tons da roseta (fora o contorno) que não são da rampa da copa de folha larga."""
    copa = next(m for m in estilo_base().materials if m.id == habito.FOLHAS["larga"][0])
    return {int(i) for q in _quadros() for i in np.unique(q.index[_figura(q)])} - {*copa.ramp, TINTA}


def test_a_fronde_tem_o_verde_da_copa_de_folha_larga() -> None:
    """A folha larga é a mesma na árvore e na touceira: o verde-escuro de sombra (com o da folha miúda, a samambaia
    saía verde-limão)."""
    assert _cores_fora_da_copa_larga() == set()


def test_controle_com_o_verde_da_folha_miuda_a_fronde_sai_clara(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(habito.LAMINAS_DA_FOLHA, "larga", ("folha", "folha_clara", "folha_escura"))
    assert _cores_fora_da_copa_larga()
