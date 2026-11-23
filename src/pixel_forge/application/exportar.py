"""O export do build para o jogo e a verificação dele: o pacote relido pelo leitor do jogo tem de dar os mesmos
quadros, pivôs, pontos, durações e sequências do build."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from ..core.recusa import Recusa
from ..export.atlas import QuadroDoAtlas, nome_do_quadro
from ..export.imagem import ler_rgba
from ..export.pacote import Cabecalho, Sequencia, escrever_pacote, ler_pacote


def ler_manifesto(build: Path) -> dict[str, Any]:
    alvo = build / "manifest.json"
    if not alvo.is_file():
        raise Recusa("BUILD_AUSENTE", f"{build} não é um build.", "Passe a pasta que o `pfe build` devolveu.")
    dado: dict[str, Any] = json.loads(alvo.read_text(encoding="utf-8"))
    return dado


def pasta_do_pacote(build: Path) -> Path:
    return build.parent.parent / "exports" / build.name


def exportar(build: Path) -> Path:
    m = ler_manifesto(build)
    quadros = [QuadroDoAtlas(c["clip"], c["direction"], f["index"], ler_rgba(build / f["path"]), f["pivot_px"],
                             f["landmarks"], f["duration_ms"], f["events"]) for c in m["clips"] for f in c["frames"]]
    seqs = [Sequencia(c["clip"], c["direction"], c["loop"], c["root_deltas_q8"]) for c in m["clips"]]
    cab = Cabecalho(m["asset"]["id"], m["asset"]["revision"], m["engine"], m["build_id"], "preview", "pending")
    return escrever_pacote(pasta_do_pacote(build), cab, quadros, seqs)


def _problemas_do_quadro(nome: str, f: dict[str, Any], build: Path, lido: Any) -> list[str]:
    out = []
    if not np.array_equal(lido.rgba, ler_rgba(build / f["path"])):
        out.append(f"{nome}: os pixels divergem")
    if list(lido.pivot_px) != f["pivot_px"]:
        out.append(f"{nome}: o pivô diverge")
    if {k: list(v) for k, v in lido.landmarks.items()} != f["landmarks"]:
        out.append(f"{nome}: os pontos divergem")
    if lido.duration_ms != f["duration_ms"] or list(lido.events) != f["events"]:
        out.append(f"{nome}: a duração ou os eventos divergem")
    return out


def verificar(build: Path) -> list[str]:
    """Os problemas do pacote relido contra o build (vazio = o roundtrip passa)."""
    m = ler_manifesto(build)
    pac = ler_pacote(pasta_do_pacote(build))
    out: list[str] = []
    for c in m["clips"]:
        nomes = [nome_do_quadro(m["asset"]["id"], c["clip"], c["direction"], f["index"]) for f in c["frames"]]
        seq = pac.sequencias.get((c["clip"], c["direction"]))
        if seq is None or seq["frames"] != nomes or seq["root_deltas_q8"] != c["root_deltas_q8"]:
            out.append(f"{c['clip']}/{c['direction']}: a sequência diverge")
            continue
        for nome, f in zip(nomes, c["frames"], strict=True):
            out += _problemas_do_quadro(nome, f, build, pac.quadros[nome])
    return out
