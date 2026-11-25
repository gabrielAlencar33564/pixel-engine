"""A sombra no chão é só a que o asset projeta (mudança 18): em xadrez na fase do pivô, nascendo na base do asset.
Não há sombra de contato (a mancha cheia embaixo dele), e a composição que ainda a pede é recusada com a dica."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_de_repouso
from pixel_forge.contracts.carregar import ler, validar
from pixel_forge.contracts.composicao import Composicao
from pixel_forge.core.recusa import Recusa
from pixel_forge.design.asset import ir_da_composicao
from pixel_forge.raster.estilo import estilo_render

EXEMPLOS = Path(__file__).parent / "fixtures" / "exemplos"
CASOS = ["banco", "arvore_folhosa", "viajante", "canino"]  # o prop, a árvore, o humano e o quadrúpede
Rgba = np.ndarray[Any, np.dtype[np.uint8]]


def _quadro(nome: str) -> tuple[Rgba, tuple[int, int]]:
    """O repouso na S e o pivô (o pé do asset) no canvas."""
    style = estilo_base()
    ir = ir_da_composicao(ler(EXEMPLOS / f"{nome}.r1.json", Composicao))
    q = quadro_de_repouso(ir, estilo_render(style), "S")
    rgba = q.to_rgba({p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette})
    return rgba, (ir.canvas.pivot_px[0], ir.canvas.pivot_px[1])


def _chao(rgba: Rgba) -> np.ndarray[Any, np.dtype[np.bool_]]:
    cor = np.array(next(p.rgba for p in estilo_base().palette if p.id == "sombra_chao"), dtype=np.uint8)
    res: np.ndarray[Any, np.dtype[np.bool_]] = np.all(rgba == cor, axis=-1)
    return res


def fora_do_xadrez(rgba: Rgba, pivo: tuple[int, int]) -> int:
    """Os pixels de sombra no chão fora da fase do xadrez do pivô: a mancha cheia (a de contato) os tem."""
    yy, xx = np.indices(rgba.shape[:2])
    return int((_chao(rgba) & ((xx - pivo[0] + yy - pivo[1]) % 2 != 0)).sum())


def nasce_na_base(rgba: Rgba) -> bool:
    """Algum pixel de sombra encosta (8 vizinhos) num pixel do asset nas duas fileiras de baixo dele."""
    chao = _chao(rgba)
    corpo = (rgba[..., 3] == 255) & ~chao
    ys = np.nonzero(corpo.any(axis=1))[0]
    base = corpo.copy()
    base[: int(ys.max()) - 1] = False
    perto = np.zeros_like(base)
    h, w = base.shape
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            perto[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] |= \
                base[max(-dy, 0):h + min(-dy, 0), max(-dx, 0):w + min(-dx, 0)]
    return bool((perto & chao).any())


@pytest.mark.parametrize("nome", CASOS)
def test_a_sombra_no_chao_e_so_a_projetada(nome: str) -> None:
    rgba, pivo = _quadro(nome)
    assert _chao(rgba).sum() > 0
    assert fora_do_xadrez(rgba, pivo) == 0
    assert nasce_na_base(rgba)


def test_controle_a_sombra_de_contato_sai_do_xadrez() -> None:
    """A mancha cheia do jeito antigo (a elipse embaixo do pé, 3:1 na tela) é acusada."""
    rgba, (px, py) = _quadro("viajante")
    cor = np.array(next(p.rgba for p in estilo_base().palette if p.id == "sombra_chao"), dtype=np.uint8)
    yy, xx = np.indices(rgba.shape[:2])
    contato = (((xx - px) / 7) ** 2 + ((yy - py) / 2.4) ** 2 <= 1) & (rgba[..., 3] == 0)
    rgba[contato] = cor
    assert fora_do_xadrez(rgba, (px, py)) > 0


def test_controle_a_composicao_com_a_sombra_de_contato_e_recusada() -> None:
    dado = json.loads((EXEMPLOS / "banco.r1.json").read_text(encoding="utf-8"))
    dado["sombra"] = {"meia_largura": "60cm"}
    with pytest.raises(Recusa) as e:
        validar(dado, Composicao, "banco")
    assert e.value.onde == "/sombra" and "projeta" in e.value.dica
