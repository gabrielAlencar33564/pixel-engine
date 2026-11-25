"""A skill da engine é a fonte; este script gera o que sai dela e o teste confere que está em dia:

- a tabela de porte da skill, dos dados do motor (``design.porte.FAIXAS``);
- o espelho em ``.agents/skills/`` (para os agentes que leem de lá);
- o formulário de pedido do agente do jogo, ``docs/pedido.md``.

``python scripts/skill.py`` grava; ``--check`` só diz o que está velho (sai com 1).
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path

from pixel_forge.design.porte import FAIXAS

RAIZ = Path(__file__).resolve().parents[1]
SKILL = RAIZ / ".claude" / "skills" / "pixel-asset-engine" / "SKILL.md"
ESPELHO = RAIZ / ".agents" / "skills" / "pixel-asset-engine" / "SKILL.md"
PEDIDO = RAIZ / "docs" / "pedido.md"


def _bloco(texto: str, nome: str) -> str:
    m = re.search(rf"<!-- {nome} -->\n(.*?)<!-- /{nome} -->", texto, re.DOTALL)
    if m is None:
        raise SystemExit(f"a skill não tem o bloco '{nome}'")
    return m.group(1)


def portes() -> str:
    linhas = ["| Category | Range | Typical |", "|---|---|---|"]
    linhas += [f"| `{c}` | {lo}× to {hi}× | {tip} |" for c, (lo, hi, tip) in FAIXAS.items()]
    return "\n".join(linhas) + "\n"


def gerados() -> dict[Path, str]:
    """O conteúdo que cada arquivo gerado deve ter."""
    fonte = SKILL.read_text(encoding="utf-8")
    skill = fonte.replace(_bloco(fonte, "portes"), portes())
    pedido = ("# Requesting an asset\n\nThe form the game agent fills in to ask the engine for an asset. Generated "
              "from the skill\n(`.claude/skills/pixel-asset-engine/SKILL.md`) by `scripts/skill.py`; do not edit here."
              "\n\n" + _bloco(skill, "pedido"))
    return {SKILL: skill, ESPELHO: skill, PEDIDO: pedido}


def velhos() -> list[Path]:
    return [p for p, texto in gerados().items() if not p.is_file() or p.read_text(encoding="utf-8") != texto]


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    if args.check:
        fora = velhos()
        print("\n".join(f"velho: {p.relative_to(RAIZ).as_posix()}" for p in fora) or "em dia")
        return 1 if fora else 0
    for p, texto in gerados().items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(texto.encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
