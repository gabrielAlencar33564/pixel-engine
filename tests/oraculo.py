"""O lado novo do oráculo: o RGBA de cada vista de um caso de ``tests/fixtures/oraculo/``."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pixel_forge.application.quadros import quadro_de_repouso
from pixel_forge.contracts.carregar import ler, validar
from pixel_forge.contracts.estilo import StyleDoc
from pixel_forge.contracts.ir import AssetIR
from pixel_forge.raster.estilo import estilo_render

CASOS = Path(__file__).parent / "fixtures" / "oraculo"


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
