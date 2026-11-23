"""O kit: cada variação da prancha de cada peça monta, cabe nos tetos e dá o mesmo pixel que o `pixel-engine` na
mesma entrada (salvo as mudanças intencionais, listadas); a peça recusa o argumento fora do schema com dica."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import Any

import pytest

from pixel_forge.application.catalogo import de_uma_peca
from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_de_repouso
from pixel_forge.core.recusa import Recusa
from pixel_forge.design.asset import ir_da_composicao
from pixel_forge.design.kit.registro import PECAS, conferida
from pixel_forge.raster.estilo import estilo_render

from .oraculo import CASOS

ESPERADO: dict[str, Any] = json.loads((CASOS / "kit.esperado.json").read_text(encoding="utf-8"))["casos"]
NOVAS = {"saia", "lenco"}  # as peças que nasceram na engine nova (a saia e o lenço gerais): sem oráculo, com teste
VARIACOES = [(pid, nome, args) for pid, p in sorted(PECAS.items()) if pid not in NOVAS for nome, args in p.variacoes]


def rgba_da_variacao(peca: str, args: dict[str, Any]) -> tuple[list[int], str]:
    style = estilo_base()
    q = quadro_de_repouso(ir_da_composicao(de_uma_peca(peca, args)), estilo_render(style), "S")
    rgba = q.to_rgba({p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette})
    return [int(rgba.shape[1]), int(rgba.shape[0])], hashlib.sha256(rgba.tobytes()).hexdigest()


@pytest.mark.parametrize(("peca", "nome", "args"), VARIACOES, ids=[f"{p}/{n}" for p, n, _ in VARIACOES])
def test_cada_variacao_monta(peca: str, nome: str, args: dict[str, Any]) -> None:
    tamanho, sha = rgba_da_variacao(peca, args)
    quer = ESPERADO[f"{peca}/{nome}"]["S"]
    assert [tamanho, sha] == [quer["tamanho"], quer["rgba_sha256"]]


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


def test_controle_a_variacao_mudada_sai_diferente() -> None:
    _, sha = rgba_da_variacao("poste", {"base": ["0", "0", "0"], "altura": "1.1m", "raio": "5cm"})
    assert sha != ESPERADO["poste/fino"]["S"]["rgba_sha256"]


def test_toda_peca_tem_oraculo_ou_e_nova() -> None:
    assert {k.split("/")[0] for k in ESPERADO} | NOVAS == set(PECAS)
