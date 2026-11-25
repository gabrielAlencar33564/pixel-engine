"""A ligação da planta: nada fica no ar. O galho nasce do eixo do tronco declarado antes (onde ele passa nessa
altura), a copa envolve o alto do tronco ou a ponta de um galho, a touceira nasce no chão ou no alto de um tronco;
o que fica solto é recusado antes de desenhar, com a medida e a dica. Cada recusa tem o controle que passa."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from pixel_forge.contracts.carregar import validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.core.recusa import Recusa
from pixel_forge.design.asset import ir_da_composicao
from pixel_forge.design.escala import PPM

EXEMPLO = Path(__file__).parent / "fixtures" / "exemplos" / "arvore_folhosa.r1.json"
GALHOS = {"base": "1.2m", "copa": ["1.2m", "70cm", "2.2m"], "n": "5", "largura": ["8cm", "10cm"], "ponta": "3cm",
          "bifurca": "0"}


def _tronco(**args: str) -> dict[str, Any]:
    return {"id": "tronco", "peca": "tronco_em_pe",
            "args": {"altura": "2m", "base": "30cm", "topo": "20cm", "casca": "casca", **args}}


def _no(ident: str, peca: str, **args: Any) -> dict[str, Any]:
    return {"id": ident, "peca": peca, "args": args}


def _planta(*nos: dict[str, Any]) -> Composicao:
    dado = json.loads(EXEMPLO.read_text(encoding="utf-8"))
    return validar({**dado, "categoria": "arvore_pequena", "nos": list(nos), "tracos": []}, Composicao, "teste")


def _recusa(*nos: dict[str, Any]) -> Recusa:
    with pytest.raises(Recusa) as e:
        ir_da_composicao(_planta(*nos))
    assert e.value.codigo == "LIGACAO"
    return e.value


def test_a_copa_acima_do_tronco_e_recusada() -> None:
    """O tronco para 60 cm abaixo dos volumes da copa: de frente a copa o cobre, mas ela está no ar."""
    r = _recusa(_tronco(altura="1m"), _no("copa", "copa", copa=["1m", "60cm", "2.4m"]))
    assert "'copa'" in r.mensagem and "'tronco'" in r.mensagem and "tronco" in r.dica


def test_controle_a_copa_que_envolve_o_alto_do_tronco_passa() -> None:
    ir_da_composicao(_planta(_tronco(altura="2.4m"), _no("copa", "copa", copa=["1m", "60cm", "2.4m"])))


def test_a_copa_fora_do_eixo_sem_galho_e_recusada() -> None:
    copa = _no("copa", "copa", copa=["60cm", "50cm", "2m"], desvio=["1.6m", "0"])
    assert "'copa'" in _recusa(_tronco(), copa).mensagem


def test_controle_a_copa_de_lado_que_ainda_envolve_o_tronco_passa() -> None:
    ir_da_composicao(_planta(_tronco(), _no("copa", "copa", copa=["60cm", "50cm", "2m"], desvio=["30cm", "0"])))


def test_a_touceira_no_ar_e_recusada() -> None:
    folhas = _no("folhas", "touceira", altura=["60cm", "90cm"], largura="16cm", pe=["0", "0", "2.6m"])
    r = _recusa(_tronco(), folhas)
    assert "'folhas'" in r.mensagem and "`pe`" in r.dica


def test_controle_a_touceira_no_alto_do_tronco_e_no_chao_passa() -> None:
    for pe in (["0", "0", "2m"], ["0", "0", "0"]):
        ir_da_composicao(_planta(_tronco(), _no("folhas", "touceira", altura=["60cm", "90cm"], largura="16cm", pe=pe)))


def test_controle_a_planta_sobre_uma_peca_que_nao_e_planta_passa() -> None:
    """O vaso segura a touceira: a peça que não é de planta conta como apoio."""
    vaso = _no("vaso", "elipsoide", centro=["0", "0", "20cm"], raios=["25cm", "25cm", "20cm"], material="pedra")
    ir_da_composicao(_planta(vaso, _no("folhas", "touceira", altura=["30cm", "50cm"], pe=["0", "0", "38cm"])))


def test_os_galhos_sem_tronco_sao_recusados() -> None:
    r = _recusa(_no("galhos", "galhos", **GALHOS))
    assert "não têm tronco" in r.mensagem and "tronco_em_pe" in r.dica


def test_o_galho_acima_do_alto_do_tronco_e_recusado() -> None:
    r = _recusa(_tronco(altura="1m"), _no("galhos", "galhos", **GALHOS))
    assert "1.20 m" in r.mensagem and "1.00 m" in r.mensagem


def test_o_galho_mais_grosso_que_o_tronco_e_recusado() -> None:
    r = _recusa(_tronco(), _no("galhos", "galhos", **{**GALHOS, "largura": ["30cm", "34cm"]}))
    assert "mais fino" in r.dica


def _saida_dos_galhos(**tronco: str) -> tuple[float, float]:
    """Onde nasce o primeiro galho (x, px) e onde o eixo do tronco passa nessa altura."""
    ir = ir_da_composicao(_planta(_tronco(**tronco), _no("galhos", "galhos", **GALHOS)))
    galho = next(p.geometry for p in ir.parts if p.id == "galhos_0" and p.geometry.type == "tapered_polyline")
    fuste = next(p.geometry for p in ir.parts if p.id == "tronco" and p.geometry.type == "revolution")
    z = galho.points_q8[0][2]
    abaixo, acima = max(e for e in fuste.stations if e[0] <= z), min(e for e in fuste.stations if e[0] >= z)
    f = 0.0 if acima[0] == abaixo[0] else (z - abaixo[0]) / (acima[0] - abaixo[0])
    return galho.points_q8[0][0] / 256, (abaixo[2] + (acima[2] - abaixo[2]) * f) / 256


def test_o_galho_nasce_do_eixo_do_tronco_inclinado() -> None:
    """O tronco inclina 60 cm no alto: a 1,2 m o eixo já saiu do prumo, e o galho nasce nele."""
    galho, eixo = _saida_dos_galhos(inclinacao="60cm")
    assert eixo >= 0.2 * PPM and abs(galho - eixo) <= 0.5


def test_controle_no_tronco_a_prumo_o_galho_nasce_no_prumo() -> None:
    galho, eixo = _saida_dos_galhos()
    assert galho == eixo == 0.0
