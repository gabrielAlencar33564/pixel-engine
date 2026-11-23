"""O quadrúpede: o parado e o passo da IR do corpo canino dão o mesmo pixel que o `pixel-engine` animando a mesma IR,
nas 8 direções, quadro a quadro (o corpo montado é provado pelo kit, fora a pegada no chão, mudada de propósito); o IK
de N segmentos deixa a pata apoiada plana; a pegada não passa do corpo; e quem anda tem as 8 direções."""

from __future__ import annotations

import json
from typing import Any

import pytest

from pixel_forge.application.catalogo import de_uma_peca
from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_de_repouso
from pixel_forge.contracts.carregar import ler, validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.contracts.ir import EllipseGeom
from pixel_forge.core.recusa import Recusa
from pixel_forge.design.asset import ir_da_composicao, movimento
from pixel_forge.design.kit.registro import PECAS
from pixel_forge.motion.canais import chain_world_mdeg
from pixel_forge.motion.gerar import gerar_clipe
from pixel_forge.raster.estilo import estilo_render
from pixel_forge.rig.fk import Skeleton

from .oraculo import CASOS
from .test_humano import _hashes

ESPERADO: dict[str, Any] = json.loads((CASOS / "quadrupedes.esperado.json").read_text(encoding="utf-8"))["casos"]
ARQ = CASOS / "quadrupedes" / "quatro_patas.r1.json"


@pytest.mark.slow
def test_o_quadrupede_parado_e_andando_igual_ao_oraculo() -> None:
    quer = ESPERADO["quatro_patas"]
    feito = _hashes(ler(ARQ, Composicao), quer)
    diferentes = sorted(k for k in quer if feito.get(k) != [quer[k]["tamanho"], quer[k]["rgba_sha256"]])
    assert feito.keys() == quer.keys() and not diferentes, diferentes[:8]


@pytest.mark.parametrize(("nome", "args"), PECAS["corpo_canino"].variacoes)
def test_cada_variacao_do_corpo_cabe_nas_8_direcoes(nome: str, args: dict[str, Any]) -> None:
    ir = ir_da_composicao(de_uma_peca("corpo_canino", args))
    est = estilo_render(estilo_base())
    assert len(ir.views) == 8 and all(quadro_de_repouso(ir, est, d).clipping_px == 0 for d in ir.views), nome


def test_no_passo_a_pata_apoiada_fica_plana_e_a_do_balanco_dobra() -> None:
    """O IK de N segmentos: no apoio, o metatarso e a pata na inclinação de repouso; no balanço, o jarrete dobra."""
    comp = ler(ARQ, Composicao)
    ir = ir_da_composicao(comp)
    pedidos, mp = movimento(comp)
    c = gerar_clipe(ir, pedidos["walk"], mp)
    skel = Skeleton(ir.bones)
    repouso = chain_world_mdeg(skel, {}, "foot_bl")
    apoio = [k for k in c.keyframes if "contact_foot_bl" in k.markers][0]
    ch = {b: ([0, 0, 0], v.rotation_mdeg) for b, v in apoio.bones.items()}
    assert chain_world_mdeg(skel, ch, "foot_bl") == repouso
    angulos = {chain_world_mdeg(skel, {b: ([0, 0, 0], v.rotation_mdeg) for b, v in k.bones.items()}, "foot_bl")
               for k in c.keyframes}
    assert min(angulos) < repouso - 10_000


def test_controle_o_quadrupede_com_uma_vista_e_recusado() -> None:
    dado = json.loads(ARQ.read_text(encoding="utf-8"))
    dado["vistas"] = {"S": {}}
    with pytest.raises(Recusa) as e:
        ir_da_composicao(validar(dado, Composicao, "teste"))
    assert e.value.codigo == "VISTA" and "8 direções" in e.value.dica


def test_a_pegada_no_chao_nao_passa_do_corpo() -> None:
    """A sombra de contato gira com o corpo: de lado ela não passa do comprimento dele (a do antigo, reescalada para o
    oblíquo, saía 2× mais longa e cortava no canvas)."""
    ir = ir_da_composicao(ler(ARQ, Composicao))
    sombra = next(p for p in ir.parts if p.id == "ground_shadow").geometry
    corpo = [p.geometry for p in ir.parts if p.id in ("chest", "body")]
    frente = max(g.center_q8[1] + g.radii_q8[1] for g in corpo if isinstance(g, EllipseGeom))
    tras = min(g.center_q8[1] - g.radii_q8[1] for g in corpo if isinstance(g, EllipseGeom))
    assert isinstance(sombra, EllipseGeom) and 2 * sombra.radii_q8[1] <= 1.3 * (frente - tras)  # o tronco, folga 30 %
