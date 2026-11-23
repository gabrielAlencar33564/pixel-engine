"""A CLI ``pfe``: o caminho curto de um asset no acervo, sem projeto de jogo.

    previa <composição>        o repouso de cada vista, com as recusas do build, e a prancha
    checar <composição>        todos os quadros do build conferidos, sem gravar nada
    build <composição>         os quadros no acervo (a composição entra em composicoes/, identidade imutável)
    exportar <build>           o pacote do jogo (pfe-jogo/1); --verificar relê e confere; --publicar pede a revisão
    olhar <build>              a prancha de todos os quadros do pacote e os números
    catalogo                   as peças do kit: para que servem, os argumentos e a prancha
    conjunto <composições...>  os assets lado a lado, na mesma escala, com o humano de régua
    revisar <build>            o estado da revisão; o dono registra com --veredito, --nota e --por
    atualizar <composição>     o desenho mudado como a revisão seguinte no acervo

Toda resposta com ``--json`` é um objeto curto: ``{"ok": true, "result": {...}}`` ou
``{"ok": false, "errors": [{"code", "message", "hint", "path"}]}``. Toda recusa traz código e dica."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from .application import acervo, previa, revisao
from .application.build import construir
from .application.catalogo import catalogo
from .application.exportar import exportar, verificar
from .application.olhar import olhar
from .contracts.carregar import ler
from .contracts.composicao import Composicao
from .core.recusa import Recusa

EXIT_RECUSA = 2
Comando = Callable[[argparse.Namespace], dict[str, Any]]


def _comp(a: argparse.Namespace) -> Composicao:
    return ler(Path(a.composicao), Composicao)


def _build(a: argparse.Namespace) -> dict[str, Any]:
    comp = _comp(a)
    pasta = acervo.pasta_do_acervo(a.acervo)
    registrada = acervo.registrar(comp, pasta)
    b = construir(comp, pasta)
    return {"build": str(b.pasta), "build_id": b.build_id, "composicao": str(registrada),
            "quadros": sum(len(c["frames"]) for c in b.manifesto["clips"])}


def _exportar(a: argparse.Namespace) -> dict[str, Any]:
    build = Path(a.build)
    if a.verificar:
        problemas = verificar(build)
        if problemas:
            raise Recusa("EXPORT_DIVERGE", f"O pacote relido diverge do build: {'; '.join(problemas[:5])}.",
                         "Exporte de novo com `pfe exportar <build>`.")
        return {"verificado": True}
    return {"atlas": str(revisao.publicar(build) if a.publicar else exportar(build))}


def _catalogo(a: argparse.Namespace) -> dict[str, Any]:
    destino = acervo.pasta_do_acervo(a.acervo) / "catalogo"
    destino.mkdir(parents=True, exist_ok=True)
    return {"index": str(catalogo(destino))}


def _revisar(a: argparse.Namespace) -> dict[str, Any]:
    build = Path(a.build)
    if a.veredito is None:
        return revisao.estado(build)
    return revisao.registrar(build, a.veredito, a.nota or "", a.por or "")


COMANDOS: dict[str, tuple[str, Comando, tuple[str, ...]]] = {
    "previa": ("o repouso de cada vista com as recusas do build, e a prancha",
               lambda a: previa.previa(_comp(a), acervo.pasta_do_acervo(a.acervo)), ("composicao", "--acervo")),
    "checar": ("todos os quadros do build conferidos, sem gravar", lambda a: previa.checar(_comp(a)),
               ("composicao",)),
    "build": ("os quadros da composição, no acervo", _build, ("composicao", "--acervo")),
    "exportar": ("o pacote do jogo (pfe-jogo/1) de um build", _exportar, ("build", "--verificar", "--publicar")),
    "olhar": ("a prancha de todos os quadros do pacote e os números", lambda a: olhar(Path(a.build)), ("build",)),
    "catalogo": ("as peças do kit: para que servem, os argumentos e a prancha", _catalogo, ("--acervo",)),
    "conjunto": ("os assets lado a lado, na mesma escala, com o humano de régua",
                 lambda a: previa.conjunto([ler(Path(c), Composicao) for c in a.composicoes],
                                           acervo.pasta_do_acervo(a.acervo)), ("composicoes", "--acervo")),
    "revisar": ("o estado da revisão do dono; o dono registra o veredito", _revisar,
                ("build", "--veredito", "--nota", "--por")),
    "atualizar": ("o desenho mudado como a revisão seguinte no acervo",
                  lambda a: {"composicao": str(acervo.atualizar(_comp(a), acervo.pasta_do_acervo(a.acervo)))},
                  ("composicao", "--acervo")),
}
BANDEIRAS = {"--verificar", "--publicar"}


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="pfe", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="comando", required=True)
    for nome, (ajuda, fn, args) in COMANDOS.items():
        p = sub.add_parser(nome, help=ajuda)
        for arg in args:
            if arg in BANDEIRAS:
                p.add_argument(arg, action="store_true")
            elif arg == "composicoes":
                p.add_argument(arg, nargs="+")
            else:
                p.add_argument(arg, choices=revisao.VEREDITOS if arg == "--veredito" else None)
        p.add_argument("--json", action="store_true")
        p.set_defaults(fn=fn)
    return ap


def main(argv: Sequence[str] | None = None) -> int:
    a = _parser().parse_args(argv)
    fn: Comando = a.fn
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
