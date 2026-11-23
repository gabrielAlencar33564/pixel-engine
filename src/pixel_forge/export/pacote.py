"""O pacote do jogo (contrato ``pfe-jogo/1``, em ``docs/contrato-do-jogo.md``): o ``atlas.json`` e as páginas PNG.

``escrever_pacote`` grava o pacote; ``ler_pacote`` é o leitor pelo lado do jogo: usa só a pasta, confere a versão do
contrato, recorta cada quadro da página no canvas de origem e devolve as sequências por clip e direção.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from ..core.direcoes import DIRECOES
from ..core.recusa import Recusa
from .atlas import QuadroDoAtlas, Rgba, empacotar, nome_do_quadro
from .imagem import ler_rgba, salvar_png

CONTRATO = "pfe-jogo/1"


@dataclass(frozen=True)
class Cabecalho:
    asset: str
    revision: int
    engine: str
    build_id: str
    status: str  # preview | release_candidate
    art_review: str  # pending | approved | changes_requested


@dataclass(frozen=True)
class Sequencia:
    clip: str
    direction: str
    loop: bool
    root_deltas_q8: list[list[int]]


def escrever_pacote(destino: Path, cab: Cabecalho, quadros: list[QuadroDoAtlas], seqs: list[Sequencia]) -> Path:
    pages, entradas = empacotar(cab.asset, quadros)
    docs_pg = []
    for i, pg in enumerate(pages):
        nome = "atlas.png" if i == 0 else f"atlas_{i}.png"
        salvar_png(destino / nome, pg)
        docs_pg.append({"image": nome, "size": {"width": pg.shape[1], "height": pg.shape[0]}})
    duracao = {e["name"]: e["duration_ms"] for e in entradas}
    clips = []
    for s in seqs:
        idx = sorted(q.index for q in quadros if q.clip == s.clip and q.direction == s.direction)
        nomes = [nome_do_quadro(cab.asset, s.clip, s.direction, i) for i in idx]
        clips.append({"clip": s.clip, "direction": s.direction, "frames": nomes, "loop": s.loop,
                      "duration_ms": sum(duracao[n] for n in nomes), "root_deltas_q8": s.root_deltas_q8})
    doc = {"contract": CONTRATO, "asset": {"id": cab.asset, "revision": cab.revision}, "engine": cab.engine,
           "build_id": cab.build_id, "status": cab.status, "art_review": cab.art_review,
           "directions": [d for d in DIRECOES if any(s.direction == d for s in seqs)], "pages": docs_pg,
           "frames": entradas, "clips": clips}
    alvo = destino / "atlas.json"
    alvo.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return alvo


@dataclass(frozen=True)
class QuadroLido:
    rgba: Rgba  # no canvas de origem
    pivot_px: tuple[int, int]
    landmarks: dict[str, tuple[int, int]]
    duration_ms: int
    events: tuple[str, ...]


@dataclass
class Pacote:
    asset: str
    revision: int
    status: str
    art_review: str
    directions: list[str]
    quadros: dict[str, QuadroLido] = field(default_factory=dict)
    sequencias: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)


def _recorte(pagina: Rgba, f: dict[str, Any]) -> Rgba:
    x, y, w, h = f["rect"]
    sx, sy, _, _ = f["source_rect"]
    out = np.zeros((f["source_size"]["height"], f["source_size"]["width"], 4), dtype=np.uint8)
    out[sy:sy + h, sx:sx + w] = pagina[y:y + h, x:x + w]
    return out


def ler_pacote(pasta: Path) -> Pacote:
    """O pacote lido só da pasta, como o jogo faria."""
    doc = json.loads((pasta / "atlas.json").read_text(encoding="utf-8"))
    if doc.get("contract") != CONTRATO:
        raise Recusa("PACOTE_CONTRATO", f"Contrato {doc.get('contract')!r} desconhecido; este leitor entende "
                     f"{CONTRATO}.", "Exporte de novo com `pfe exportar`.")
    paginas = [ler_rgba(pasta / pg["image"]) for pg in doc["pages"]]
    pac = Pacote(doc["asset"]["id"], doc["asset"]["revision"], doc["status"], doc["art_review"], doc["directions"])
    for f in doc["frames"]:
        x, y, w, h = f["rect"]
        pg = paginas[f["page"]]
        if y + h > pg.shape[0] or x + w > pg.shape[1]:
            raise Recusa("PACOTE_INCOMPLETO", f"O quadro {f['name']} sai da página {f['page']}.",
                         "Exporte de novo com `pfe exportar`.")
        pac.quadros[f["name"]] = QuadroLido(_recorte(pg, f), (f["pivot_px"][0], f["pivot_px"][1]),
                                            {k: (v[0], v[1]) for k, v in f["landmarks"].items()}, f["duration_ms"],
                                            tuple(f["events"]))
    for c in doc["clips"]:
        faltam = [n for n in c["frames"] if n not in pac.quadros]
        if faltam:
            raise Recusa("PACOTE_INCOMPLETO", f"{c['clip']}/{c['direction']}: quadros sem entrada no atlas "
                         f"({faltam[:3]}).", "Exporte de novo com `pfe exportar`.")
        pac.sequencias[(c["clip"], c["direction"])] = c
    return pac
