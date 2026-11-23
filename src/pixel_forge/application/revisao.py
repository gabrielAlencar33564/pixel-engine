"""A revisão humana: o dono olha a prancha e registra o veredito de um build (``aprovado`` ou ``ajustar``) em
``revisoes/<asset>.r<n>.json`` do acervo. Só o build aprovado sai publicado (``pfe exportar --publicar``); a engine e o
agente nunca aprovam a arte."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..core.recusa import Recusa
from .exportar import exportar, ler_manifesto

VEREDITOS = ("aprovado", "ajustar")


def _arquivo(build: Path) -> Path:
    m = ler_manifesto(build)
    return build.parent.parent / "revisoes" / f"{m['asset']['id']}.r{m['asset']['revision']}.json"


def registros(build: Path) -> list[dict[str, Any]]:
    alvo = _arquivo(build)
    dado: list[dict[str, Any]] = json.loads(alvo.read_text(encoding="utf-8")) if alvo.is_file() else []
    return dado


def aprovado(build: Path) -> bool:
    """O último veredito deste build é ``aprovado``."""
    bid = ler_manifesto(build)["build_id"]
    deste = [r for r in registros(build) if r["build_id"] == bid]
    return bool(deste) and deste[-1]["veredito"] == "aprovado"


def estado(build: Path) -> dict[str, Any]:
    m = ler_manifesto(build)
    return {"asset": m["asset"]["id"], "revision": m["asset"]["revision"], "build_id": m["build_id"],
            "art_review": "approved" if aprovado(build) else "pending", "registros": registros(build)}


def registrar(build: Path, veredito: str, nota: str, por: str) -> dict[str, Any]:
    if veredito not in VEREDITOS or not por.strip() or not nota.strip():
        raise Recusa("REVISAO", f"O registro pede o veredito ({' ou '.join(VEREDITOS)}), a nota e quem revisou.",
                     "Use `pfe revisar <build> --veredito aprovado --nota \"...\" --por <nome do dono>`; só o dono "
                     "aprova a arte.")
    novo = {"build_id": ler_manifesto(build)["build_id"], "veredito": veredito, "nota": nota, "por": por,
            "quando": datetime.now(UTC).isoformat(timespec="seconds")}
    alvo = _arquivo(build)
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(json.dumps([*registros(build), novo], ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return estado(build)


def publicar(build: Path) -> Path:
    """O pacote publicado (``release_candidate``, arte aprovada): só com o veredito ``aprovado`` do dono neste build."""
    if not aprovado(build):
        raise Recusa("REVISAO_PENDENTE", f"O build {build.name} não tem a revisão do dono com o veredito aprovado.",
                     "O dono olha a prancha (`pfe olhar <build>`) e registra com `pfe revisar <build> --veredito "
                     "aprovado`; até lá o pacote sai como prévia (`pfe exportar <build>`).")
    return exportar(build, aprovado=True)
