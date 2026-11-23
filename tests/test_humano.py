"""O humano: o corpo vestido dá o mesmo pixel que o `pixel-engine` no parado e no andar, nas 8 direções, quadro a
quadro; cada peça de roupa veste o corpo; a saia segue a coxa ao andar; e quem anda tem as 8 direções."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest

from pixel_forge.application.build import instantes
from pixel_forge.application.catalogo import de_uma_peca
from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_da_pose, quadro_de_repouso
from pixel_forge.contracts.carregar import ler, validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.core.recusa import Recusa
from pixel_forge.design.asset import ir_da_composicao, movimento
from pixel_forge.design.kit.registro import PECAS
from pixel_forge.motion.gerar import gerar_clipe
from pixel_forge.raster.estilo import estilo_render

from .oraculo import CASOS, no_canvas_antigo

ESPERADO: dict[str, Any] = json.loads((CASOS / "humanos.esperado.json").read_text(encoding="utf-8"))["casos"]
VARIACOES = [(pid, nome, args) for pid, p in sorted(PECAS.items()) if p.tipo == "humanoide"
             for nome, args in p.variacoes]


def _comp(nome: str) -> Composicao:
    return ler(CASOS / "humanos" / f"{nome}.r1.json", Composicao)


def _hashes(comp: Composicao, quer: dict[str, Any]) -> dict[str, Any]:
    """O tamanho e o hash de cada quadro de cada clipe e vista, no canvas do antigo."""
    ir, style = ir_da_composicao(comp), estilo_base()
    est = estilo_render(style)
    pal = {p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette}
    pedidos, mp = movimento(comp)
    out = {}
    for clip, receita in pedidos.items():
        its, _ = instantes(ir, clip, receita, mp)
        for d in ir.views:
            for it in its:
                k = f"{clip}/{d}/{it.index}"
                if k not in quer:
                    continue
                feito = no_canvas_antigo(quadro_da_pose(ir, est, it.pose, d).to_rgba(pal), quer[k]["tamanho"])
                out[k] = [feito["tamanho"], feito["rgba_sha256"]]
    return out


@pytest.mark.slow
def test_o_humano_vestido_parado_e_andando_igual_ao_oraculo() -> None:
    quer = ESPERADO["vestido"]
    feito = _hashes(_comp("vestido"), quer)
    diferentes = sorted(k for k in quer if feito.get(k) != [quer[k]["tamanho"], quer[k]["rgba_sha256"]])
    assert feito.keys() == quer.keys() and not diferentes, diferentes[:8]


@pytest.mark.parametrize(("peca", "nome", "args"), VARIACOES, ids=[f"{p}/{n}" for p, n, _ in VARIACOES])
def test_cada_peca_veste_o_corpo(peca: str, nome: str, args: dict[str, Any]) -> None:
    ir = ir_da_composicao(de_uma_peca(peca, args))
    q = quadro_de_repouso(ir, estilo_render(estilo_base()), "S")
    assert q.clipping_px == 0 and len(ir.views) == 8, (peca, nome)


def _rotacao_da_saia(comp: Composicao) -> list[int]:
    ir = ir_da_composicao(comp)
    pedidos, mp = movimento(comp)
    c = gerar_clipe(ir, pedidos["walk"], mp)
    return [k.bones["skirt_l"].rotation_mdeg for k in c.keyframes]


def test_a_saia_segue_a_coxa_ao_andar() -> None:
    dado = json.loads((CASOS / "humanos" / "vestido.r1.json").read_text(encoding="utf-8"))
    dado["nos"] = [n for n in dado["nos"] if n["peca"] != "calca"] + [
        {"id": "saia", "peca": "saia", "args": {"material": "pano_marrom"}}]
    rot = _rotacao_da_saia(validar(dado, Composicao, "teste"))
    assert max(rot) > 1000 and min(rot) < -1000


def test_controle_sem_a_saia_nao_ha_osso_de_saia() -> None:
    with pytest.raises(KeyError):
        _rotacao_da_saia(_comp("vestido"))


def test_controle_quem_anda_com_uma_vista_e_recusado() -> None:
    dado = json.loads((CASOS / "humanos" / "vestido.r1.json").read_text(encoding="utf-8"))
    dado["vistas"] = {"S": {}}
    with pytest.raises(Recusa) as e:
        ir_da_composicao(validar(dado, Composicao, "teste"))
    assert e.value.codigo == "VISTA" and "8 direções" in e.value.dica


def test_cada_direcao_tem_o_proprio_quadro() -> None:
    ir = ir_da_composicao(_comp("vestido"))
    est = estilo_render(estilo_base())
    hashes = {hashlib.sha256(quadro_de_repouso(ir, est, d).index.tobytes()).hexdigest() for d in ir.views}
    assert len(hashes) == 8
