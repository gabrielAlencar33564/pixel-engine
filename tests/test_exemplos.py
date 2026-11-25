"""Os cinco exemplos da skill, feitos pelo padrão vigente: passam por todas as recusas do build (I8) e mostram o que
cada tipo pede (o estático de vista única, a árvore em duas construções, a ``copa`` em massa e a ``copa_aberta`` nos
galhos, o humano e o quadrúpede nas 8 direções)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pixel_forge.application import critica
from pixel_forge.application.build import renderizar
from pixel_forge.contracts.carregar import ler
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.quality import flora

PASTA = Path(__file__).parent / "fixtures" / "exemplos"
VISTAS = {"banco": 1, "arvore_folhosa": 1, "arvore_aberta": 1, "viajante": 8, "canino": 8}


@pytest.mark.parametrize("nome", sorted(VISTAS))
def test_o_exemplo_passa_pelo_build(nome: str) -> None:
    comp = ler(PASTA / f"{nome}.r1.json", Composicao)
    r = renderizar(comp)
    assert len(r.ir.views) == VISTAS[nome] and all(s.quadros for s in r.sequencias)


def test_as_arvores_de_exemplo_sao_duas_construcoes() -> None:
    """Uma de copa em massa e uma de copa aberta: sem defeito na crítica, e uma não se parece com a outra."""
    massa, aberta = (ler(PASTA / f"{nome}.r1.json", Composicao) for nome in ("arvore_folhosa", "arvore_aberta"))
    assert "copa" in {n.peca for n in massa.nos} and "copa_aberta" in {n.peca for n in aberta.nos}
    lidas = [critica.medir(c)[0] for c in (massa, aberta)]
    assert all(flora.achados(m, True, {}) == [] for m in lidas)
    assert flora.semelhanca(lidas[0].assinatura, lidas[1].assinatura) < 0.6


def test_os_exemplos_sao_os_cinco() -> None:
    assert sorted(p.name.removesuffix(".r1.json") for p in PASTA.glob("*.json")) == sorted(VISTAS)
