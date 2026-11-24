"""O lado antigo do oráculo: roda dentro da cópia do `pixel-engine` (o Python dela, isolado) e renderiza o repouso
de cada vista como o build antigo fazia (o render e as correções de pixel do build), ou os quadros dos clipes pedidos.
Lê do stdin ``{"style": ..., "camera": {"elevation_mdeg", "depth_permille"}, "casos": [{"nome", "asset" ou
"composicao", "vistas", "clipes"?, "mp"?}]}`` no formato antigo (sem ``style``, o estilo base antigo; a câmera é a da
engine nova, que a composição antiga recebe) e escreve no stdout, por quadro, o tamanho, o sha256 do RGBA, o sha256
sem a sombra no chão (os pixels da cor dela e os transparentes zerados: o corpo igual onde a sombra mudou de
propósito) e o RGBA em base64.

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


def _quadro(rgba: Any, style: Any) -> dict[str, Any]:
    sem = rgba.copy()
    sem[rgba[..., 3] == 0] = 0  # o fundo
    # a sombra no chão, pelo nome antigo ou o novo (o estilo dos casos de IR não a tem)
    for m in (m for m in style.materials if m.id in ("ground", "sombra")):
        cor = next(p.rgba for p in style.palette if p.index == m.ramp[0])
        sem[(rgba == tuple(cor)).all(axis=-1)] = 0
    return {"tamanho": [int(rgba.shape[1]), int(rgba.shape[0])],
            "rgba_sha256": hashlib.sha256(rgba.tobytes()).hexdigest(),
            "sem_chao_sha256": hashlib.sha256(sem.tobytes()).hexdigest(),
            "rgba_b64": base64.b64encode(rgba.tobytes()).decode("ascii")}


def _asset(caso: dict[str, Any], style: Any, camera: Any) -> Any:
    loader: Any = importlib.import_module("pixel_forge.contracts.loader")
    if "asset" in caso:
        return loader.validate_document(caso["asset"], "asset")
    prev: Any = importlib.import_module("pixel_forge.application.compose_preview")
    grammar, comp = prev.grammar_for(caso["composicao"])
    ref = {"id": style.id, "revision": style.revision, "sha256": "0" * 64}
    return prev.preview_asset(grammar, comp, ref, camera=camera)


def _vistas(caso: dict[str, Any], style: Any, camera: Any) -> dict[str, Any]:
    render: Any = importlib.import_module("pixel_forge.application.render")
    ops: Any = importlib.import_module("pixel_forge.pixelops.ops")
    asset = _asset(caso, style, camera)
    fr = render.FrameRenderer(asset, style)
    tags = {p.id: set(p.tags) for p in asset.parts}
    out = {}
    for vista in caso["vistas"]:
        fb = fr.render(None, vista, 0)[0]
        ops.run_build_pixelops(fb, style, tags)
        rgba = fb.to_rgba(render.palette_map(style))
        out[vista] = _quadro(rgba, style)
    return out


def _clipes(caso: dict[str, Any], style: Any, camera: Any) -> dict[str, Any]:
    """Os quadros de cada clipe pedido (a receita antiga), em cada vista: na composição antiga com os parâmetros de
    movimento da gramática, ou na IR nova convertida (``asset``) com os parâmetros novos (``mp``)."""
    loader: Any = importlib.import_module("pixel_forge.contracts.loader")
    render: Any = importlib.import_module("pixel_forge.application.render")
    ops: Any = importlib.import_module("pixel_forge.pixelops.ops")
    receita: Any = importlib.import_module("pixel_forge.motion.receita")
    if "asset" in caso:
        asset, mp = loader.validate_document(caso["asset"], "asset"), caso["mp"]
    else:
        prev: Any = importlib.import_module("pixel_forge.application.compose_preview")
        grammar, comp = prev.grammar_for(caso["composicao"])
        ref = {"id": style.id, "revision": style.revision, "sha256": "0" * 64}
        asset = prev.preview_asset(grammar, comp, ref, camera=camera)
        p = {s.name: int(s.default or 0) if s.distribution == "fixed" else (s.lo + s.hi) // 2 for s in grammar.params}
        mp = grammar.motion(p, 96)
    fr = render.FrameRenderer(asset, style)
    tags = {pt.id: set(pt.tags) for pt in asset.parts}
    aref = {"id": asset.id, "revision": asset.revision, "sha256": "0" * 64}
    out = {}
    props: Any = importlib.import_module("pixel_forge.motion.presets_props")
    do_prop = {"balanco": props.sway_clip, "giro": props.spin_clip}  # o balanço e o giro eram presets, não receitas
    for clip, nome in caso["clipes"].items():
        gera = do_prop.get(nome) or (lambda a, r, m, nome=nome: receita.gera(nome, a, r, m))
        doc = loader.validate_document(gera(asset, aref, mp), "clip")
        for vista in caso["vistas"]:
            for i, t in enumerate(doc.sample_times_ms):
                fb = fr.render(doc, vista, t)[0]
                ops.run_build_pixelops(fb, style, tags)
                rgba = fb.to_rgba(render.palette_map(style))
                out[f"{clip}/{vista}/{i}"] = _quadro(rgba, style)
    return out


def main() -> int:
    loader: Any = importlib.import_module("pixel_forge.contracts.loader")
    entrada = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    bruto = entrada.get("style") or json.loads(Path("presets/styles/base.json").read_text(encoding="utf-8"))
    style = loader.validate_document(bruto, "style")
    camera = SimpleNamespace(model="oblique_3q", **entrada["camera"])
    sys.stdout.write(json.dumps({c["nome"]: _clipes(c, style, camera) if "clipes" in c else _vistas(c, style, camera)
                                for c in entrada["casos"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
