"""O lado novo do oráculo: o RGBA de cada vista de um caso de ``tests/fixtures/oraculo/``."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from pixel_forge.application.estilo import estilo_base
from pixel_forge.application.quadros import quadro_de_repouso
from pixel_forge.contracts.carregar import ler, validar
from pixel_forge.contracts.estilo import StyleDoc
from pixel_forge.contracts.ir import AssetIR
from pixel_forge.design.kit import humano
from pixel_forge.motion.receita import carregar
from pixel_forge.raster.estilo import estilo_render

CASOS = Path(__file__).parent / "fixtures" / "oraculo"
ABRE_BRACO_DO_ANTIGO = 15_000.0  # o `pixel-engine` abre o braço a 15° no repouso
BALANCO_DO_ANTIGO = (23_000, 26_000)  # e, no andar, balança o ombro 23° e dobra o cotovelo 26° (mdeg)


def braco_do_antigo(monkeypatch: pytest.MonkeyPatch) -> None:
    """O braço do humano na abertura do `pixel-engine`: a engine abre menos (mudança intencional), e o oráculo
    compara o resto do humano (o corpo, o rig, o movimento e o render) na abertura dele."""
    monkeypatch.setattr(humano, "ABRE_BRACO_MDEG", ABRE_BRACO_DO_ANTIGO)


def balanco_do_antigo(monkeypatch: pytest.MonkeyPatch) -> None:
    """O balanço do braço no andar com a amplitude do `pixel-engine` (o ombro e o cotovelo): a da engine é menor
    (mudança intencional), e o oráculo compara o resto do andar na amplitude dele."""
    receita = carregar("andar_poses")
    canais = copy.deepcopy(receita["canais"])
    for lado, sinal in (("r", 1), ("l", -1)):
        canais[f"braco_{lado}.frente"]["rot"]["termos"][1]["amp"] = sinal * BALANCO_DO_ANTIGO[0]
        canais[f"braco_{lado}.cotovelo"]["rot"]["termos"][1]["amp"] = BALANCO_DO_ANTIGO[1]
    monkeypatch.setitem(receita, "canais", canais)


def no_canvas_antigo(rgba: np.ndarray[Any, np.dtype[np.uint8]], tamanho: list[int]) -> dict[str, Any]:
    """O quadro no canvas do antigo, como o oráculo grava (o tamanho, o hash e o hash sem a sombra no chão): o canvas
    novo inclui a sombra que o asset projeta no chão (à direita e embaixo; o pivô não muda), então o antigo é o
    recorte de cima e da esquerda, e fora dele só há a sombra no chão."""
    w, h = tamanho
    chao = np.array(next(p.rgba for p in estilo_base().palette if p.id == "sombra_chao"), dtype=np.uint8)
    if rgba.shape[0] >= h and rgba.shape[1] >= w:
        fora = rgba.copy()
        fora[:h, :w] = 0
        assert np.all(np.all(fora[fora[..., 3] == 255] == chao, axis=-1)), "fora do canvas antigo: não é sombra"
        rgba = np.ascontiguousarray(rgba[:h, :w])
    sem = rgba.copy()
    sem[np.all(rgba == chao, axis=-1) | (rgba[..., 3] == 0)] = 0  # a sombra no chão e o fundo
    return {"tamanho": [int(rgba.shape[1]), int(rgba.shape[0])],
            "rgba_sha256": hashlib.sha256(rgba.tobytes()).hexdigest(),
            "sem_chao_sha256": hashlib.sha256(sem.tobytes()).hexdigest()}


def caso(nome: str) -> dict[str, Any]:
    dado: dict[str, Any] = json.loads((CASOS / f"{nome}.json").read_text(encoding="utf-8"))
    return dado


def esperado(nome: str) -> dict[str, Any]:
    dado: dict[str, Any] = json.loads((CASOS / f"{nome}.esperado.json").read_text(encoding="utf-8"))
    return dado


def rgba_por_vista(dado: dict[str, Any]) -> dict[str, tuple[list[int], str]]:
    style = ler(CASOS / dado["estilo"], StyleDoc)
    ir = validar(dado["ir"], AssetIR, "caso")
    est = estilo_render(style)
    palette = {p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette}
    out = {}
    for vista in dado["vistas"]:
        rgba = quadro_de_repouso(ir, est, vista).to_rgba(palette)
        out[vista] = ([int(rgba.shape[1]), int(rgba.shape[0])], hashlib.sha256(rgba.tobytes()).hexdigest())
    return out
