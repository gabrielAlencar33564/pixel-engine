"""O kit: cada variação da prancha de cada peça monta, cabe nos tetos e dá o mesmo pixel que o `pixel-engine` na
mesma entrada (salvo as mudanças intencionais, listadas); a peça recusa o argumento fora do schema com dica; as faces
da peça ficam nos degraus da camada do nó."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

import pytest

from pixel_forge.application.catalogo import de_uma_peca
from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_de_repouso
from pixel_forge.core.recusa import Recusa
from pixel_forge.core.rng import Stream
from pixel_forge.design.asset import ir_da_composicao
from pixel_forge.design.construtor import AssetBuilder
from pixel_forge.design.kit.peca import CAMADAS_DO_NO, Ctx
from pixel_forge.design.kit.pilha import Pilha
from pixel_forge.design.kit.registro import PECAS, conferida
from pixel_forge.raster.estilo import estilo_render

from .oraculo import (
    CASOS,
    abertura_do_antigo,
    braco_do_antigo,
    cabeca_do_antigo,
    no_canvas_antigo,
    tronco_do_antigo,
)

ESPERADO: dict[str, Any] = json.loads((CASOS / "kit.esperado.json").read_text(encoding="utf-8"))["casos"]
NOVAS = {"saia", "lenco"}  # as peças que nasceram na engine nova (a saia e o lenço gerais): sem oráculo, com teste
VARIACOES = [(pid, nome, args) for pid, p in sorted(PECAS.items()) if pid not in NOVAS for nome, args in p.variacoes]


def rgba_da_variacao(peca: str, args: dict[str, Any], tamanho: list[int]) -> dict[str, Any]:
    style = estilo_base()
    q = quadro_de_repouso(ir_da_composicao(de_uma_peca(peca, args)), estilo_render(style), "S")
    return no_canvas_antigo(q.to_rgba({p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette}),
                            tamanho)


@pytest.mark.parametrize(("peca", "nome", "args"), VARIACOES, ids=[f"{p}/{n}" for p, n, _ in VARIACOES])
def test_cada_variacao_monta(peca: str, nome: str, args: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    if PECAS[peca].tipo == "humanoide":
        braco_do_antigo(monkeypatch)  # o braço do repouso fechou: o resto do humano se compara na abertura do antigo
        tronco_do_antigo(monkeypatch)  # e o tronco e os ombros mudaram de forma: compara-se no tronco do antigo
        cabeca_do_antigo(monkeypatch)  # a cabeça, os olhos e o cabelo também
        abertura_do_antigo(monkeypatch)  # e as pernas, que abriam para fora
    quer = ESPERADO[f"{peca}/{nome}"]["S"]
    feito = rgba_da_variacao(peca, args, quer["tamanho"])
    chave = "sem_chao_sha256" if PECAS[peca].tipo == "quadrupede" else "rgba_sha256"  # a pegada do quadrúpede mudou
    assert [feito["tamanho"], feito[chave]] == [quer["tamanho"], quer[chave]]


def test_controle_a_peca_acima_do_teto_e_recusada_pelo_registro() -> None:
    p = PECAS["poste"]
    with pytest.raises(ValueError, match="argumentos"):
        conferida(replace(p, args=p.args * 4))
    with pytest.raises(ValueError, match="variações"):
        conferida(replace(p, variacoes=p.variacoes[:2]))


def test_controle_o_argumento_fora_do_schema_e_recusado() -> None:
    with pytest.raises(Recusa) as e:
        ir_da_composicao(de_uma_peca("poste", {"base": ["0", "0", "0"], "altura": "1m", "raio": "5cm", "cor": "1"}))
    assert e.value.codigo == "ARGUMENTO" and "catalogo" in e.value.dica


def test_a_face_fica_na_faixa_do_no() -> None:
    c = Ctx(AssetBuilder(), Stream(0), "x", "x", Pilha(), 10 * CAMADAS_DO_NO)
    c.empilha("x_face", 3, [(0.0, 0.0, 0.0)])
    assert c.pilha.items[0][1] == 1003
    with pytest.raises(ValueError, match="degrau"):
        c.empilha("x_fora", CAMADAS_DO_NO, [(0.0, 0.0, 0.0)])


def test_controle_a_variacao_mudada_sai_diferente() -> None:
    quer = ESPERADO["poste/fino"]["S"]
    feito = rgba_da_variacao("poste", {"base": ["0", "0", "0"], "altura": "1.1m", "raio": "5cm"}, quer["tamanho"])
    assert feito["rgba_sha256"] != quer["rgba_sha256"]


def test_toda_peca_tem_oraculo_ou_e_nova() -> None:
    assert {k.split("/")[0] for k in ESPERADO} | NOVAS == set(PECAS)
