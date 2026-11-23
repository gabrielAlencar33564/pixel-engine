"""O build: a composição vira a IR e os quadros de cada clipe e direção, no estilo do jogo, gravados no acervo por
conteúdo (o id do build é o hash da composição, do estilo e da versão do motor: o mesmo pedido dá o mesmo build)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any

from ..contracts.composicao import Composicao
from ..contracts.ir import AssetIR
from ..design.asset import ir_da_composicao, movimento
from ..design.porte import conferir_porte
from ..export.imagem import salvar_png
from ..motion.gerar import gerar_clipe
from ..quality.quadro import conferir_quadro
from ..raster.estilo import EstiloRender, estilo_render
from ..raster.renderer import Quadro
from ..rig.fk import Skeleton
from ..rig.pose import Pose, avaliar, rest_pose, sample_channels
from .estilo import estilo_base
from .quadros import quadro_da_pose

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


@dataclass(frozen=True)
class Instante:
    """Um quadro do clipe: o índice, o tempo, a duração, a pose e o quanto a raiz anda até o próximo (q8)."""

    index: int
    t_ms: int
    duration_ms: int
    pose: Pose
    root_delta_q8: list[int]


def instantes(ir: AssetIR, clip: str, receita: str, mp: dict[str, int]) -> tuple[list[Instante], bool]:
    """Os quadros do clipe (o estático: o repouso, 1 s) e se ele faz laço."""
    skel = Skeleton(ir.bones)
    if clip == "static":
        return [Instante(0, 0, ESTATICO_MS, rest_pose(skel), [0, 0, 0])], False
    c = gerar_clipe(ir, receita, mp)
    st = c.sample_times_ms
    roots = [sample_channels(c, t)[0] for t in st] + [sample_channels(c, c.duration_ms)[0]]
    proximos = [*st[1:], c.duration_ms]
    return [Instante(i, t, proximos[i] - t, avaliar(skel, c, t),
                     [roots[i + 1][0] - roots[i][0], roots[i + 1][1] - roots[i][1], 0])
            for i, t in enumerate(st)], c.loop


@dataclass(frozen=True)
class Sequencia:
    """Os quadros de um clipe numa direção, já conferidos (RGBA), com o laço e os instantes."""

    clip: str
    direcao: str
    loop: bool
    instantes: list[Instante]
    quadros: list[Quadro]


@dataclass(frozen=True)
class Renderizado:
    ir: AssetIR
    est: EstiloRender
    sequencias: list[Sequencia]


def renderizar(comp: Composicao) -> Renderizado:
    """Todos os quadros que o build grava, com as mesmas recusas (o porte, o quadro cortado, as cores): o ``checar``
    e o ``build`` passam por aqui (I8)."""
    ir, style = ir_da_composicao(comp), estilo_base()
    conferir_porte(comp.categoria, ir)
    est = estilo_render(style)
    pedidos, mp = movimento(comp)
    seqs = []
    for clip, receita in pedidos.items():
        its, loop = instantes(ir, clip, receita, mp)
        for direcao in ir.views:
            quadros = [quadro_da_pose(ir, est, it.pose, direcao) for it in its]
            for it, q in zip(its, quadros, strict=True):
                conferir_quadro(q, style, f"{clip}/{direcao}/{it.index}")
            seqs.append(Sequencia(clip, direcao, loop, its, quadros))
    return Renderizado(ir, est, seqs)


def _gravar(pasta: Path, r: Renderizado, s: Sequencia, i: int) -> dict[str, Any]:
    it, q = s.instantes[i], s.quadros[i]
    rgba = q.to_rgba({p.index: (p.rgba[0], p.rgba[1], p.rgba[2], p.rgba[3]) for p in r.est.doc.palette})
    rel = f"frames/{s.clip}/{s.direcao.lower()}/{it.index:03d}.png"
    salvar_png(pasta / rel, rgba)
    return {"index": it.index, "path": rel, "duration_ms": it.duration_ms, "pivot_px": list(r.ir.canvas.pivot_px),
            "events": [], "landmarks": {k: [u >> 8, v >> 8] for k, (u, v) in sorted(q.landmarks.items())},
            "rgba_sha256": hashlib.sha256(rgba.tobytes()).hexdigest()}


def construir(comp: Composicao, acervo: Path) -> Build:
    """Os quadros de cada clipe em cada direção, conferidos e gravados em ``builds/`` do acervo."""
    engine = versao_do_motor()
    r = renderizar(comp)
    build_id = hash_canonico({"engine": engine, "composicao": comp.model_dump(mode="json"),
                              "style": r.est.doc.model_dump(mode="json")})
    pasta = acervo / "builds" / f"{r.ir.id}.r{r.ir.revision}.{build_id[:12]}"
    clips = [{"clip": s.clip, "direction": s.direcao, "loop": s.loop,
              "root_deltas_q8": [it.root_delta_q8 for it in s.instantes],
              "frames": [_gravar(pasta, r, s, i) for i in range(len(s.quadros))]} for s in r.sequencias]
    manifesto = {"build_id": build_id, "engine": engine, "asset": {"id": r.ir.id, "revision": r.ir.revision},
                 "clips": clips}
    (pasta / "manifest.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return Build(pasta, build_id, manifesto)
