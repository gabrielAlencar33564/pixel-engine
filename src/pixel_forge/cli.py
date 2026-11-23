"""A CLI ``pfe``. Toda resposta com ``--json`` é um objeto curto: ``{"ok": true, "result": {...}}`` ou
``{"ok": false, "errors": [{"code", "message", "hint", "path"}]}``. Toda recusa traz código e dica."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from .application.build import construir
from .application.exportar import exportar, verificar
from .contracts.carregar import ler
from .contracts.estilo import StyleDoc
from .contracts.ir import AssetIR
from .core.recusa import Recusa

EXIT_RECUSA = 2


def acervo(opcao: str | None) -> Path:
    """O acervo de trabalho (fora do git): ``--acervo``, ``PFE_ACERVO`` ou ``~/.pixel-forge/acervo``."""
    return Path(opcao or os.environ.get("PFE_ACERVO") or Path.home() / ".pixel-forge" / "acervo")


def _build(a: argparse.Namespace) -> dict[str, Any]:
    b = construir(ler(Path(a.ir), AssetIR), ler(Path(a.estilo), StyleDoc), acervo(a.acervo))
    return {"build": str(b.pasta), "build_id": b.build_id,
            "quadros": sum(len(c["frames"]) for c in b.manifesto["clips"])}


def _exportar(a: argparse.Namespace) -> dict[str, Any]:
    build = Path(a.build)
    if a.verificar:
        problemas = verificar(build)
        if problemas:
            raise Recusa("EXPORT_DIVERGE", f"O pacote relido diverge do build: {'; '.join(problemas[:5])}.",
                         "Exporte de novo com `pfe exportar <build>`.")
        return {"verificado": True}
    return {"atlas": str(exportar(build))}


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="pfe", description=__doc__)
    sub = ap.add_subparsers(dest="comando", required=True)
    b = sub.add_parser("build", help="os quadros da IR, no acervo")
    b.add_argument("ir")
    b.add_argument("--estilo", required=True)
    b.add_argument("--acervo")
    b.set_defaults(fn=_build)
    e = sub.add_parser("exportar", help="o pacote do jogo (pfe-jogo/1) de um build")
    e.add_argument("build")
    e.add_argument("--verificar", action="store_true", help="relê o pacote e confere com o build")
    e.set_defaults(fn=_exportar)
    for p in (b, e):
        p.add_argument("--json", action="store_true")
    return ap


def main(argv: Sequence[str] | None = None) -> int:
    a = _parser().parse_args(argv)
    fn: Callable[[argparse.Namespace], dict[str, Any]] = a.fn
    try:
        res = fn(a)
    except Recusa as r:
        erro = {"code": r.codigo, "message": r.mensagem, "hint": r.dica, "path": r.onde}
        print(json.dumps({"ok": False, "errors": [erro]}, ensure_ascii=False) if a.json
              else f"recusa {r.codigo}: {r.mensagem}\ndica: {r.dica}")
        return EXIT_RECUSA
    print(json.dumps({"ok": True, "result": res}, ensure_ascii=False) if a.json
          else "\n".join(f"{k}: {v}" for k, v in res.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
