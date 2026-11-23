"""O lado antigo do oráculo: roda dentro da cópia do `pixel-engine` (o Python dela, isolado) e renderiza o repouso
de cada vista como o build antigo fazia (o render e as correções de pixel do build). Lê do stdin
``{"asset": ..., "style": ..., "vistas": [...]}`` no formato antigo e escreve no stdout, por vista, o tamanho, o
sha256 do RGBA e o RGBA em base64.

Os módulos antigos entram por ``importlib``: este arquivo não importa o pacote da engine nova.
"""

from __future__ import annotations

import base64
import hashlib
import importlib
import json
import sys
from typing import Any


def main() -> int:
    loader: Any = importlib.import_module("pixel_forge.contracts.loader")
    render: Any = importlib.import_module("pixel_forge.application.render")
    ops: Any = importlib.import_module("pixel_forge.pixelops.ops")
    entrada = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    asset = loader.validate_document(entrada["asset"], "asset")
    style = loader.validate_document(entrada["style"], "style")
    fr = render.FrameRenderer(asset, style)
    tags = {p.id: set(p.tags) for p in asset.parts}
    out = {}
    for vista in entrada["vistas"]:
        fb = fr.render(None, vista, 0)[0]
        ops.run_build_pixelops(fb, style, tags)
        rgba = fb.to_rgba(render.palette_map(style))
        out[vista] = {"tamanho": [int(rgba.shape[1]), int(rgba.shape[0])],
                      "rgba_sha256": hashlib.sha256(rgba.tobytes()).hexdigest(),
                      "rgba_b64": base64.b64encode(rgba.tobytes()).decode("ascii")}
    sys.stdout.write(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
