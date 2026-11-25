"""Os quatro exemplos da skill, feitos pelo padrão vigente: passam por todas as recusas do build (I8) e mostram o que
cada tipo pede (o estático de vista única, a árvore com a ``copa`` em volumes, o humano e o quadrúpede nas 8
direções)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pixel_forge.application.build import renderizar
from pixel_forge.contracts.carregar import ler
from pixel_forge.contracts.composicao import Composicao

PASTA = Path(__file__).parent / "fixtures" / "exemplos"
VISTAS = {"banco": 1, "arvore_folhosa": 1, "viajante": 8, "canino": 8}


@pytest.mark.parametrize("nome", sorted(VISTAS))
def test_o_exemplo_passa_pelo_build(nome: str) -> None:
    comp = ler(PASTA / f"{nome}.r1.json", Composicao)
    r = renderizar(comp)
    assert len(r.ir.views) == VISTAS[nome] and all(s.quadros for s in r.sequencias)


def test_a_arvore_de_exemplo_usa_a_copa_em_volumes() -> None:
    comp = ler(PASTA / "arvore_folhosa.r1.json", Composicao)
    assert "copa" in {n.peca for n in comp.nos}


def test_os_exemplos_sao_os_quatro() -> None:
    assert sorted(p.name.removesuffix(".r1.json") for p in PASTA.glob("*.json")) == sorted(VISTAS)
