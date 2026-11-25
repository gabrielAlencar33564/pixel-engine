"""O golpe de espada do humano: a espada na mão direita segue a mão; o clipe ``attack`` não faz laço, ergue a mão
na preparação, a traz para baixo e para a frente no corte e volta ao repouso; e o canvas de quem tem a arma cabe a
lâmina no alto (sem ele, o quadro do golpe sai cortado)."""

from __future__ import annotations

import json
from typing import Any

import pytest

from pixel_forge.application.build import instantes, renderizar
from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_da_pose, quadro_de_repouso
from pixel_forge.contracts.carregar import validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.core.recusa import Recusa
from pixel_forge.design import humano
from pixel_forge.design.asset import ir_da_composicao, movimento
from pixel_forge.design.kit import humano as kit_humano
from pixel_forge.raster.estilo import estilo_render

from .oraculo import CASOS

ESPADA = {"id": "espada", "peca": "espada", "args": {"material": "casca_clara", "detalhe": "couro"}}
# de frente, na tela: na preparação a mão direita sobe ao menos 20 px acima do repouso (do quadril à altura da
# cabeça; a lâmina passa por cima dela); no corte ela desce abaixo do repouso, à frente; o último quadro volta a até
# 3 px dele
SOBE_PX, VOLTA_PX = 20, 3


def _comp(espada: bool = True, clipes: tuple[str, ...] = ("idle", "attack")) -> Composicao:
    dado: dict[str, Any] = json.loads((CASOS / "humanos" / "vestido.r1.json").read_text(encoding="utf-8"))
    dado["id"] = "golpe_teste"
    dado["nos"] = [*dado["nos"], ESPADA] if espada else dado["nos"]
    dado["movimento"] = list(clipes)
    return validar(dado, Composicao, "golpe")


def _maos(clip: str) -> list[float]:
    """Por quadro do clipe, de frente (S): a altura da mão direita na tela, em px acima do pé."""
    comp = _comp()
    ir, est = ir_da_composicao(comp), estilo_render(estilo_base())
    pedidos, mp = movimento(comp)
    out = []
    for it in instantes(ir, clip, pedidos[clip], mp)[0]:
        lm = quadro_da_pose(ir, est, it.pose, "S").landmarks
        out.append((lm["foot_r"][1] - lm["hand_r"][1]) / 256)
    return out


def test_a_espada_fica_na_mao_direita_e_aparece_no_repouso() -> None:
    ir = ir_da_composicao(_comp())
    partes = {p.id: p for p in ir.parts}
    assert {partes[s].bone_id for s in ("sword_blade", "sword_guard", "sword_grip")} == {"hand_r"}
    q = quadro_de_repouso(ir, estilo_render(estilo_base()), "S")
    assert q.clipping_px == 0


def test_o_golpe_nao_faz_laco_ergue_a_mao_e_corta_para_baixo() -> None:
    comp = _comp()
    ir = ir_da_composicao(comp)
    pedidos, mp = movimento(comp)
    _, laco = instantes(ir, "attack", pedidos["attack"], mp)
    maos = _maos("attack")
    assert not laco
    assert max(maos) - maos[0] >= SOBE_PX
    pico = maos.index(max(maos))
    assert min(maos[pico:]) < maos[0] and abs(maos[-1] - maos[0]) <= VOLTA_PX


def test_controle_o_parado_nao_ergue_a_mao() -> None:
    maos = _maos("idle")
    assert max(maos) - maos[0] < SOBE_PX / 10


def test_quem_tem_a_espada_tem_o_canvas_do_golpe() -> None:
    r = renderizar(_comp())
    assert {s.clip for s in r.sequencias} == {"idle", "attack"}
    assert r.ir.canvas.height == ir_da_composicao(_comp(espada=False)).canvas.height + 16


def test_controle_sem_o_canvas_da_arma_o_golpe_sai_cortado(monkeypatch: pytest.MonkeyPatch) -> None:
    original = kit_humano.canvas_de
    monkeypatch.setattr(humano, "canvas_de", lambda estatura, _arma=False: original(estatura))
    with pytest.raises(Recusa) as e:
        renderizar(_comp())
    assert e.value.codigo == "QUADRO_CORTADO"


def test_controle_o_clipe_que_o_corpo_nao_faz_e_recusado() -> None:
    with pytest.raises(Recusa) as e:
        ir_da_composicao(_comp(clipes=("idle", "golpe")))
    assert e.value.codigo == "MOVIMENTO"
