"""I11: cada fixture dá o mesmo pixel que o `pixel-engine` na mesma entrada (o esperado é gravado pelo
`scripts/oraculo.py`). O controle negativo mostra que a comparação acusa uma mudança de 1 px na geometria."""

from __future__ import annotations

import pytest

from .oraculo import caso, esperado, rgba_por_vista

CASOS_N1 = ["bloco", "tronco", "face"]


@pytest.mark.parametrize("nome", CASOS_N1)
def test_igual_ao_oraculo(nome: str) -> None:
    feito = rgba_por_vista(caso(nome))
    quer = esperado(nome)["vistas"]
    assert {v: list(t) for v, t in feito.items()} == {v: [q["tamanho"], q["rgba_sha256"]] for v, q in quer.items()}


def test_controle_um_px_a_mais_muda_o_pixel() -> None:
    dado = caso("bloco")
    vertice = dado["ir"]["parts"][0]["geometry"]["vertices"][0]["point_q8"]
    vertice[2] += 256
    feito = rgba_por_vista(dado)
    assert feito["S"][1] != esperado("bloco")["vistas"]["S"]["rgba_sha256"]
