"""O build: a IR e o estilo viram os quadros de cada clip e vista, gravados no acervo por conteúdo (o id do build é o
hash da entrada e da versão do motor, então o mesmo pedido dá o mesmo build)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any

from ..contracts.estilo import StyleDoc
from ..contracts.ir import AssetIR
from ..export.imagem import salvar_png
from ..quality.quadro import conferir_quadro
from ..raster.estilo import estilo_render
from .quadros import quadro_de_repouso

ESTATICO_MS = 1000  # o quadro do estático dura 1 s (um quadro por vista)


def versao_do_motor() -> str:
    return version("pixel-asset-engine")


def hash_canonico(dado: Any) -> str:
    texto = json.dumps(dado, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Build:
    pasta: Path
    build_id: str
    manifesto: dict[str, Any]


def construir(ir: AssetIR, style: StyleDoc, acervo: Path) -> Build:
    """Os quadros do estático (o repouso de cada vista), conferidos e gravados em ``builds/`` do acervo."""
    engine = versao_do_motor()
    build_id = hash_canonico({"engine": engine, "ir": ir.model_dump(mode="json"),
                              "style": style.model_dump(mode="json")})
    pasta = acervo / "builds" / f"{ir.id}.r{ir.revision}.{build_id[:12]}"
    est = estilo_render(style)
    palette = {p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in style.palette}
    clips = []
    for direcao in ir.views:
        q = quadro_de_repouso(ir, est, direcao)
        conferir_quadro(q, style, f"static/{direcao}")
        rgba = q.to_rgba(palette)
        rel = f"frames/static/{direcao.lower()}/000.png"
        salvar_png(pasta / rel, rgba)
        clips.append({"clip": "static", "direction": direcao, "loop": False, "root_deltas_q8": [[0, 0, 0]],
                      "frames": [{"index": 0, "path": rel, "duration_ms": ESTATICO_MS,
                                  "pivot_px": list(ir.canvas.pivot_px), "events": [],
                                  "landmarks": {k: [u >> 8, v >> 8] for k, (u, v) in sorted(q.landmarks.items())},
                                  "rgba_sha256": hashlib.sha256(rgba.tobytes()).hexdigest()}]})
    manifesto = {"build_id": build_id, "engine": engine, "asset": {"id": ir.id, "revision": ir.revision},
                 "clips": clips}
    (pasta / "manifest.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return Build(pasta, build_id, manifesto)
