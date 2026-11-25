"""O acervo de trabalho (fora do git; ``--acervo``, ``PFE_ACERVO`` ou ``~/.pixel-forge/acervo``): a composição de cada
asset em ``composicoes/<id>.r<n>.json``. A identidade é imutável: a mesma revisão com outro desenho é recusada, e a
mudança de desenho é a revisão seguinte (``pfe atualizar``)."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from ..contracts.carregar import ler
from ..contracts.composicao import Composicao
from ..core.recusa import Recusa


def pasta_do_acervo(opcao: str | None) -> Path:
    return Path(opcao or os.environ.get("PFE_ACERVO") or Path.home() / ".pixel-forge" / "acervo")


def _arquivo(acervo: Path, ident: str, revisao: int) -> Path:
    return acervo / "composicoes" / f"{ident}.r{revisao}.json"


def _gravar(alvo: Path, comp: Composicao) -> None:
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(json.dumps(comp.model_dump(mode="json", exclude_none=True), ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")


def _guardada(alvo: Path) -> Composicao | None:
    """A composição guardada no acervo; a de um formato que saiu (a sombra de contato, a mudança 18) não se lê mais e
    conta como outro desenho: a revisão seguinte a refaz."""
    try:
        return ler(alvo, Composicao)
    except Recusa as e:
        if e.codigo != "DOC_INVALIDO":
            raise
        return None


def conferir(comp: Composicao, acervo: Path) -> Path:
    """O lugar da composição no acervo, sem gravar; a revisão que já existe com outro desenho é recusada."""
    alvo = _arquivo(acervo, comp.id, comp.revision)
    if alvo.is_file() and _guardada(alvo) != comp:
        raise Recusa("IDENTIDADE", f"'{comp.id}' r{comp.revision} já existe no acervo com outro desenho.",
                     "A identidade não muda: grave a mudança como a revisão seguinte com `pfe atualizar "
                     "<composição>`.", "/revision")
    return alvo


def registrar(comp: Composicao, acervo: Path) -> Path:
    """A composição no acervo, com a identidade conferida. O build registra depois de construir: a composição que ele
    recusa não ocupa a revisão."""
    alvo = conferir(comp, acervo)
    if not alvo.is_file():
        _gravar(alvo, comp)
    return alvo


def revisoes(acervo: Path, ident: str) -> list[int]:
    padrao = re.compile(rf"{re.escape(ident)}\.r(\d+)\.json")
    pasta = acervo / "composicoes"
    achadas = (padrao.fullmatch(p.name) for p in pasta.glob(f"{ident}.r*.json")) if pasta.is_dir() else iter(())
    return sorted(int(m.group(1)) for m in achadas if m)


def atualizar(comp: Composicao, acervo: Path) -> Path:
    """A composição editada como a revisão seguinte à última do acervo; sem mudança de desenho, recusa."""
    existentes = revisoes(acervo, comp.id)
    if existentes:
        ultima = _guardada(_arquivo(acervo, comp.id, existentes[-1]))
        if ultima is not None and ultima.model_copy(update={"revision": comp.revision}) == comp:
            raise Recusa("SEM_MUDANCA", f"'{comp.id}': o desenho é o mesmo da r{existentes[-1]}.",
                         "Mude a composição (as peças, as medidas, os materiais) antes de atualizar.")
    nova = comp.model_copy(update={"revision": (existentes[-1] if existentes else comp.revision - 1) + 1})
    alvo = _arquivo(acervo, nova.id, nova.revision)
    _gravar(alvo, nova)
    return alvo
