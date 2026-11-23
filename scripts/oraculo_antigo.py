"""O lado antigo do oráculo: roda dentro da cópia do `pixel-engine` (o Python dela, isolado) e renderiza o repouso
de cada vista como o build antigo fazia (o render e as correções de pixel do build). Lê do stdin
``{"style": ..., "casos": [{"nome", "asset" ou "composicao", "vistas"}]}`` no formato antigo (sem ``style``, o estilo
base antigo) e escreve no stdout, por caso e vista, o tamanho, o sha256 do RGBA e o RGBA em base64.

Os módulos antigos entram por ``importlib``: este arquivo não importa o pacote da engine nova.
"""

from __future__ import annotations

import base64
import hashlib
import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

CAMERA = SimpleNamespace(model="oblique_3q", elevation_mdeg=45_000, depth_permille=350)


def _asset(caso: dict[str, Any], style: Any) -> Any:
    loader: Any = importlib.import_module("pixel_forge.contracts.loader")
    if "asset" in caso:
        return loader.validate_document(caso["asset"], "asset")
    prev: Any = importlib.import_module("pixel_forge.application.compose_preview")
    grammar, comp = prev.grammar_for(caso["composicao"])
    ref = {"id": style.id, "revision": style.revision, "sha256": "0" * 64}
    return prev.preview_asset(grammar, comp, ref, camera=CAMERA)


def _vistas(caso: dict[str, Any], style: Any) -> dict[str, Any]:
    render: Any = importlib.import_module("pixel_forge.application.render")
    ops: Any = importlib.import_module("pixel_forge.pixelops.ops")
    asset = _asset(caso, style)
    fr = render.FrameRenderer(asset, style)
    tags = {p.id: set(p.tags) for p in asset.parts}
    out = {}
    for vista in caso["vistas"]:
        fb = fr.render(None, vista, 0)[0]
        ops.run_build_pixelops(fb, style, tags)
        rgba = fb.to_rgba(render.palette_map(style))
        out[vista] = {"tamanho": [int(rgba.shape[1]), int(rgba.shape[0])],
                      "rgba_sha256": hashlib.sha256(rgba.tobytes()).hexdigest(),
                      "rgba_b64": base64.b64encode(rgba.tobytes()).decode("ascii")}
    return out


def main() -> int:
    loader: Any = importlib.import_module("pixel_forge.contracts.loader")
    entrada = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    bruto = entrada.get("style") or json.loads(Path("presets/styles/base.json").read_text(encoding="utf-8"))
    style = loader.validate_document(bruto, "style")
    sys.stdout.write(json.dumps({c["nome"]: _vistas(c, style) for c in entrada["casos"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
